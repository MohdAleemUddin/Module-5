import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import * as vscode from 'vscode';

type PlanItem = {
  rule_id: string;
  start: number;
  end: number;
  replacement: string;
};

const TEST_RULES = [
  { rule_id: 'PII-001', pattern: 'Authorization:\\s*Bearer\\s+\\S+' },
  { rule_id: 'PII-002', pattern: 'email=\\S+' },
  { rule_id: 'PII-003', pattern: 'token=\\S+' }
]; // TODO replace with policy-driven rules later

async function runRedactionCli(payload: object): Promise<string> {
  return new Promise((resolve, reject) => {
    const proc = spawn('python', ['-m', 'edge.m5_observability.tools.pii_redact_cli']);
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
    const payload = { text, rules: TEST_RULES, mode: 'hash' }; // TODO policy choice

    let plan: PlanItem[] = [];
    try {
      const output = await runRedactionCli(payload);
      const parsed = JSON.parse(output);
      plan = parsed.plan || [];
    } catch (err: any) {
      vscode.window.showErrorMessage(`PII redaction failed: ${err.message || err}`);
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

