import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import * as vscode from 'vscode';
import { pc1Check } from '../pc1/pc1Wrapper';
import { loadPolicy } from '../policy/policyLoader';

type PlanItem = {
  rule_id: string;
  start: number;
  end: number;
  replacement: string;
};

async function loadPiiRulesFromPolicy(workspaceRoot: string): Promise<any[]> {
  const policy = await loadPolicy(workspaceRoot);
  return policy['obs.pii_rules'] || [];
}

async function findProjectRootForPII(workspaceRoot: string): Promise<string> {
  const fs = await import('fs/promises');
  const path = await import('path');
  
  // Check if 'edge' exists in workspace root
  const edgePath = path.join(workspaceRoot, 'edge');
  try {
    await fs.access(edgePath);
    return workspaceRoot;
  } catch {
    // Edge not in workspace root, try parent directory
    const parentEdgePath = path.join(path.dirname(workspaceRoot), 'edge');
    try {
      await fs.access(parentEdgePath);
      return path.dirname(workspaceRoot);
    } catch {
      // Fallback: assume edge is in parent of workspace
      return path.dirname(workspaceRoot);
    }
  }
}

async function runRedactionCli(payload: object, workspaceRoot: string): Promise<string> {
  return new Promise(async (resolve, reject) => {
    const projectRoot = await findProjectRootForPII(workspaceRoot);
    const projectRootEscaped = projectRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    
    // Use Python -c with explicit path and call the CLI function directly
    // The CLI reads from stdin, so we pass payload via stdin
    const proc = spawn('python', ['-c', `
import sys
import json
sys.path.insert(0, r'${projectRootEscaped}')

from edge.m5_observability.checks.pii_redaction import build_redaction_plan

# Read payload from stdin
payload_str = sys.stdin.read()
payload = json.loads(payload_str)

# Call build_redaction_plan directly
text = payload["text"]
rules = payload["rules"]
mode = payload.get("mode", "hash")
result = build_redaction_plan(text, rules, mode)
sys.stdout.write(json.dumps(result))
    `], {
      env: { ...process.env, PYTHONPATH: projectRoot }
    });
    
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));
    proc.on('error', reject);
    proc.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr || `pii_redact_cli exited with code ${code}`));
      }
    });
    proc.stdin.write(JSON.stringify(payload));
    proc.stdin.end();
  });
}

async function appendJsonLines(filePath: string, entries: object[]): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const lines = entries.map((e) => JSON.stringify(e)).join('\n') + '\n';
  await fs.appendFile(filePath, lines, { encoding: 'utf8' });
}

export function registerPiiRedaction(context: vscode.ExtensionContext): void {
  const disposable = vscode.commands.registerCommand('zeroui.m5.redactPii', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage('Open a file to run PII redaction.');
      return;
    }

    const document = editor.document;
    const text = document.getText();
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
    
    // Load PII rules from policy
    const rules = await loadPiiRulesFromPolicy(workspaceRoot);
    const payload = { text, rules, mode: 'hash' };

    let plan: PlanItem[] = [];
    try {
      const output = await runRedactionCli(payload, workspaceRoot);
      const parsed = JSON.parse(output);
      plan = parsed.plan || [];
    } catch (err: any) {
      vscode.window.showErrorMessage(`PII redaction failed: ${err.message || err}`);
      return;
    }
    
    if (plan.length === 0) {
      vscode.window.showInformationMessage('No PII/secret patterns found to redact.');
      return;
    }
    
    // PC-1 check before write
    const pc1Result = await pc1Check('m5.pii.redact', { plan }, workspaceRoot);
    if (!pc1Result.allowed) {
      vscode.window.showErrorMessage('PC-1 denied: PII redaction not allowed');
      return;
    }

    const storageDir = context.globalStorageUri.fsPath;
    const mappingFile = path.join(storageDir, 'm5_pii_redaction_map.json');
    const receiptFile = path.join(storageDir, 'receipts_m5.jsonl');

    const edit = new vscode.WorkspaceEdit();
    const sortedPlan = [...plan].sort(
      (a, b) =>
        b.start - a.start ||
        b.end - a.end ||
        a.rule_id.localeCompare(b.rule_id) ||
        a.replacement.localeCompare(b.replacement)
    );

    const mappingEntries: object[] = [];
    for (const item of plan) {
      const original = text.slice(item.start, item.end);
      mappingEntries.push({
        file: document.uri.fsPath,
        rule_id: item.rule_id,
        start: item.start,
        end: item.end,
        original,
        replacement: item.replacement
      });
    }

    for (const item of sortedPlan) {
      const startPos = document.positionAt(item.start);
      const endPos = document.positionAt(item.end);
      edit.replace(document.uri, new vscode.Range(startPos, endPos), item.replacement);
    }

    const applied = await vscode.workspace.applyEdit(edit);
    if (!applied) {
      vscode.window.showErrorMessage('Failed to apply redaction edits.');
      return;
    }

    await appendJsonLines(mappingFile, mappingEntries);

    const receiptEntry = {
      module: 'M5_observability_v1',
      action: 'pii_redaction',
      pc1_attested: true,
      redactions_applied: plan.map((item) => ({
        file: document.uri.fsPath,
        rule_id: item.rule_id,
        start: item.start,
        end: item.end,
        replacement: item.replacement
      })),
      mapping_file: 'm5_pii_redaction_map.json'
    };
    await appendJsonLines(receiptFile, [receiptEntry]);

    vscode.window.showInformationMessage(`Applied ${plan.length} redactions.`);
  });

  context.subscriptions.push(disposable);
}

