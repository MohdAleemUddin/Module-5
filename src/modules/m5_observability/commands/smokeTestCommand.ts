import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs/promises';

export function registerSmokeTestCommand(context: vscode.ExtensionContext): void {
  const disposable = vscode.commands.registerCommand('zeroui.m5.runSmokeTests', async () => {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      vscode.window.showErrorMessage('No workspace folder found.');
      return;
    }

    const repoRoot = workspaceFolder.uri.fsPath;
    const receiptsPath = path.join(context.globalStorageUri.fsPath, 'receipts_m5.jsonl');

    // Ensure receipts directory exists
    await fs.mkdir(context.globalStorageUri.fsPath, { recursive: true });

    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Running M5 Observability Smoke Tests',
        cancellable: false,
      },
      async (progress) => {
        try {
          progress.report({ increment: 0, message: 'Starting smoke tests...' });

          // Call Python backend
          const result = await runSmokeTests(repoRoot, receiptsPath);

          progress.report({ increment: 100, message: 'Smoke tests completed' });

          if (result.outcome === 'pass') {
            vscode.window.showInformationMessage(
              `Smoke tests passed. Coverage: ${result.telemetry_coverage_pct}%`
            );
          } else {
            vscode.window.showWarningMessage(
              `Smoke tests ${result.outcome}. Coverage: ${result.telemetry_coverage_pct}%. Missing: ${result.missing_signals?.join(', ') || 'none'}`
            );
          }

          // Refresh decision panel if open
          vscode.commands.executeCommand('zeroui.m5.refreshDecisionPanel', receiptsPath).then(() => {}, () => {});
        } catch (error: any) {
          vscode.window.showErrorMessage(`Smoke tests failed: ${error.message}`);
        }
      }
    );
  });

  context.subscriptions.push(disposable);
}

async function findProjectRoot(workspaceRoot: string): Promise<string> {
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

async function runSmokeTests(repoRoot: string, receiptsPath: string): Promise<any> {
  // Find project root (where 'edge' module is located)
  const projectRoot = await findProjectRoot(repoRoot);
  
  return new Promise((resolve, reject) => {
    const pythonPath = 'python';
    
    // Try to load policy from file, fallback to default
    const policyPath = path.join(repoRoot, 'policy_observability.json');
    
    // Escape paths properly for Python (use raw strings to avoid escape sequence issues)
    // Replace backslashes with forward slashes and escape single quotes
    const projectRootEscaped = projectRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    const repoRootEscaped = repoRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    const policyPathEscaped = policyPath.replace(/\\/g, '/').replace(/'/g, "\\'");
    const receiptsPathEscaped = receiptsPath.replace(/\\/g, '/').replace(/'/g, "\\'");
    
    // Check if policy file exists and load it
    const loadPolicy = `
import sys
import json
import os
from pathlib import Path
# Add project root to Python path (where 'edge' module is)
sys.path.insert(0, r'${projectRootEscaped}')

policy_path = r'${policyPathEscaped}'
if os.path.exists(policy_path):
    from edge.m5_observability.policy.loader import load_observability_policy
    policy = load_observability_policy(policy_path)
    # Extract full policy dict (loader returns ordered dict with all policy keys)
    policy_cfg = dict(policy)  # Convert OrderedDict to regular dict
else:
    # Default policy config with all required keys
    policy_cfg = {
        'obs.required_signals': ['latency_ms', 'status', 'error_code', 'request_id', 'trace_id', 'hw_ts_ms'],
        'obs.min_telemetry_coverage_warn': 0.8,
        'obs.min_telemetry_coverage_block': 0.6,
        'obs.require_correlation_id': True,
        'obs.require_hw_timestamp': True,
        'obs.max_label_cardinality_warn': 100,
        'obs.max_label_cardinality_block': 500,
        'obs.disallow_dynamic_keys': True,
        'obs.sample_rate_default': 1.0,
        'obs.generated_marker_comment': 'CC_OBS_SNIPPET',
        'gate_mode': 'Warn'
    }
`;

    const proc = spawn(pythonPath, ['-c', `
${loadPolicy}
from edge.m5_observability.smoke.smoke_runner import run_and_record

receipts_path = r'${receiptsPathEscaped}'
result = run_and_record(r'${repoRootEscaped}', policy_cfg, receipts_path)
print(json.dumps(result))
    `]);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    proc.on('error', (err) => {
      reject(new Error(`Failed to start smoke test: ${err.message}`));
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Smoke test exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout.trim());
        resolve(result);
      } catch (err: any) {
        reject(new Error(`Failed to parse smoke test result: ${err.message}. Output: ${stdout}`));
      }
    });
  });
}

