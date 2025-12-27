import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import { pc1Check } from '../pc1/pc1Wrapper';
import { CoverageDeltaTracker } from '../coverage/deltaTracker';
import { loadPolicy, getRequiredSignals, getMarkerComment } from '../policy/policyLoader';

let deltaTracker: CoverageDeltaTracker | undefined;

async function findProjectRootForSnippets(workspaceRoot: string): Promise<string> {
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

async function calculateCurrentCoverage(filePath: string, text: string): Promise<number | null> {
  const requiredSignals = ['latency_ms', 'status', 'error_code', 'request_id', 'trace_id', 'hw_ts_ms'];
  
  // Remove comments and strings
  let codeText = text;
  codeText = codeText.replace(/\/\/.*$/gm, '');
  codeText = codeText.replace(/\/\*[\s\S]*?\*\//g, '');
  codeText = codeText.replace(/['"`][^'"`]*['"`]/g, '');
  
  // Count found signals
  let found = 0;
  for (const signal of requiredSignals) {
    const regex = new RegExp(`\\b${signal.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`);
    if (regex.test(codeText)) {
      found++;
    }
  }
  
  return (found / requiredSignals.length) * 100;
}

export function registerSnippetCommands(context: vscode.ExtensionContext): void {
  deltaTracker = new CoverageDeltaTracker(context);
  // Insert observability snippet
  const insertSnippetDisposable = vscode.commands.registerCommand(
    'zeroui.m5.insertObsSnippet',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showInformationMessage('Open a file to insert snippet.');
        return;
      }

      const document = editor.document;
      const filePath = document.uri.fsPath;
      const text = document.getText();

      try {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        
        // Get marker from policy
        const marker = await getMarkerComment(workspaceRoot);
        
        // Call Python backend to plan snippet insertion
        const plan = await planLoggingSnippet(filePath, text, workspaceRoot, marker);
        
        if (!plan || plan.patch.op === 'noop') {
          vscode.window.showInformationMessage('Snippet already exists or no changes needed.');
          return;
        }
        
        // PC-1 check before write
        const pc1Result = await pc1Check('m5.log_snippet.insert', plan.patch, workspaceRoot);
        if (!pc1Result.allowed) {
          vscode.window.showErrorMessage('PC-1 denied: snippet insertion not allowed');
          return;
        }
        
        // Save coverage before insertion
        const coverageBefore = await calculateCurrentCoverage(document.uri.fsPath, text);
        if (coverageBefore !== null && deltaTracker) {
          await deltaTracker.saveSnapshot(document.uri.fsPath, coverageBefore);
        }
        
        // Apply patch
        const edit = new vscode.WorkspaceEdit();
        const position = new vscode.Position(document.lineCount, 0);
        edit.insert(document.uri, position, plan.patch.text);
        
        const applied = await vscode.workspace.applyEdit(edit);
        if (applied) {
          // Save document to trigger diagnostics refresh and status bar update
          await document.save();
          
          // Wait a bit for diagnostics to update
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Calculate delta after insertion
          if (deltaTracker) {
            const newText = text + plan.patch.text;
            const coverageAfter = await calculateCurrentCoverage(document.uri.fsPath, newText);
            if (coverageAfter !== null) {
              await deltaTracker.saveSnapshot(document.uri.fsPath, coverageAfter);
              const delta = await deltaTracker.getDelta(document.uri.fsPath);
              if (delta) {
                const roiTags = await deltaTracker.calculateRoiTags(document.uri.fsPath, delta.delta);
                vscode.window.showInformationMessage(
                  `Observability snippet inserted. Coverage: ${coverageBefore?.toFixed(1)}% → ${coverageAfter.toFixed(1)}% (Δ${delta.delta > 0 ? '+' : ''}${delta.delta.toFixed(1)}%)`
                );
              } else {
                vscode.window.showInformationMessage('Observability snippet inserted.');
              }
            } else {
              vscode.window.showInformationMessage('Observability snippet inserted.');
            }
          } else {
            vscode.window.showInformationMessage('Observability snippet inserted.');
          }
        }
      } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to insert snippet: ${error.message}`);
      }
    }
  );

  // Insert metrics snippet
  const insertMetricsDisposable = vscode.commands.registerCommand(
    'zeroui.m5.insertMetricsSnippet',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showInformationMessage('Open a file to insert metrics snippet.');
        return;
      }

      const document = editor.document;
      const filePath = document.uri.fsPath;
      const text = document.getText();

      try {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        
        // Load policy dynamically using centralized loader
        const policyCfg = await loadPolicy(workspaceRoot);
        
        // Call Python backend to plan metrics insertion
        const plan = await planMetricsSnippet(filePath, text, policyCfg, workspaceRoot);
        
        if (!plan || plan.patch.op === 'noop') {
          vscode.window.showInformationMessage('Snippet already exists or no changes needed.');
          return;
        }
        
        if (plan.patch.op === 'blocked') {
          vscode.window.showErrorMessage(`Snippet blocked: ${plan.patch.reason}`);
          return;
        }
        
        // PC-1 check before write
        const pc1Result = await pc1Check('m5.metrics_snippet.insert', plan.patch, workspaceRoot);
        if (!pc1Result.allowed) {
          vscode.window.showErrorMessage('PC-1 denied: metrics snippet insertion not allowed');
          return;
        }
        
        // Apply patch
        const edit = new vscode.WorkspaceEdit();
        const position = new vscode.Position(document.lineCount, 0);
        edit.insert(document.uri, position, plan.patch.text);
        
        // Save coverage before insertion
        const coverageBefore = await calculateCurrentCoverage(document.uri.fsPath, text);
        if (coverageBefore !== null && deltaTracker) {
          await deltaTracker.saveSnapshot(document.uri.fsPath, coverageBefore);
        }
        
        const applied = await vscode.workspace.applyEdit(edit);
        if (applied) {
          // Save document to trigger diagnostics refresh and status bar update
          await document.save();
          
          // Wait a bit for diagnostics to update
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Calculate delta after insertion
          if (deltaTracker) {
            const newText = text + plan.patch.text;
            const coverageAfter = await calculateCurrentCoverage(document.uri.fsPath, newText);
            if (coverageAfter !== null) {
              await deltaTracker.saveSnapshot(document.uri.fsPath, coverageAfter);
              const delta = await deltaTracker.getDelta(document.uri.fsPath);
              if (delta) {
                vscode.window.showInformationMessage(
                  `Metrics snippet inserted. Coverage: ${coverageBefore?.toFixed(1)}% → ${coverageAfter.toFixed(1)}% (Δ${delta.delta > 0 ? '+' : ''}${delta.delta.toFixed(1)}%)`
                );
              } else {
                vscode.window.showInformationMessage('Metrics snippet inserted.');
              }
            } else {
              vscode.window.showInformationMessage('Metrics snippet inserted.');
            }
          } else {
            vscode.window.showInformationMessage('Metrics snippet inserted.');
          }
        }
      } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to insert metrics snippet: ${error.message}`);
      }
    }
  );

  // Inject correlation IDs
  const injectCorrelationDisposable = vscode.commands.registerCommand(
    'zeroui.m5.injectCorrelation',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showInformationMessage('Open a file to inject correlation IDs.');
        return;
      }

      const document = editor.document;
      const filePath = document.uri.fsPath;
      const text = document.getText();

      try {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        const policyPath = path.join(workspaceRoot, 'policy_observability.json');
        
        // Load policy
        let policyCfg: any = {};
        try {
          const policyContent = await vscode.workspace.fs.readFile(vscode.Uri.file(policyPath));
          const policyData = JSON.parse(Buffer.from(policyContent).toString('utf-8'));
          policyCfg = policyData.policy || {};
        } catch {
          // Use defaults if policy not found
          policyCfg = {
            'obs.require_correlation_id': true
          };
        }
        
        // Call Python backend to plan correlation injection
        const plan = await planCorrelationSnippet(filePath, text, policyCfg, workspaceRoot);
        
        if (!plan || plan.patch.op === 'noop') {
          vscode.window.showInformationMessage('Correlation IDs already exist or not required.');
          return;
        }
        
        // PC-1 check before write
        const pc1Result = await pc1Check('m5.correlation.inject', plan.patch, workspaceRoot);
        if (!pc1Result.allowed) {
          vscode.window.showErrorMessage('PC-1 denied: correlation injection not allowed');
          return;
        }
        
        // Apply patch
        const edit = new vscode.WorkspaceEdit();
        const position = new vscode.Position(document.lineCount, 0);
        edit.insert(document.uri, position, plan.patch.text);
        
        // Save coverage before insertion
        const coverageBefore = await calculateCurrentCoverage(document.uri.fsPath, text);
        if (coverageBefore !== null && deltaTracker) {
          await deltaTracker.saveSnapshot(document.uri.fsPath, coverageBefore);
        }
        
        const applied = await vscode.workspace.applyEdit(edit);
        if (applied) {
          // Save document to trigger diagnostics refresh and status bar update
          await document.save();
          
          // Wait a bit for diagnostics to update
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Calculate delta after insertion
          if (deltaTracker) {
            const newText = text + plan.patch.text;
            const coverageAfter = await calculateCurrentCoverage(document.uri.fsPath, newText);
            if (coverageAfter !== null) {
              await deltaTracker.saveSnapshot(document.uri.fsPath, coverageAfter);
              const delta = await deltaTracker.getDelta(document.uri.fsPath);
              if (delta) {
                vscode.window.showInformationMessage(
                  `Correlation ID injection inserted. Coverage: ${coverageBefore?.toFixed(1)}% → ${coverageAfter.toFixed(1)}% (Δ${delta.delta > 0 ? '+' : ''}${delta.delta.toFixed(1)}%)`
                );
              } else {
                vscode.window.showInformationMessage('Correlation ID injection snippet inserted.');
              }
            } else {
              vscode.window.showInformationMessage('Correlation ID injection snippet inserted.');
            }
          } else {
            vscode.window.showInformationMessage('Correlation ID injection snippet inserted.');
          }
        }
      } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to inject correlation: ${error.message}`);
      }
    }
  );

  context.subscriptions.push(insertSnippetDisposable, insertMetricsDisposable, injectCorrelationDisposable);
}

async function planLoggingSnippet(filePath: string, text: string, workspaceRoot: string, marker: string): Promise<any> {
  return new Promise(async (resolve, reject) => {
    const snippetText = `// TODO: Import logger if not already available
// import { logger } from './logger'; // or your logger module

const duration = Date.now() - startTime; // Calculate latency
const statusCode = 200; // HTTP status code
const errorCode = 0; // Error code (0 = success)
const reqId = req.headers['x-request-id'] || generateId(); // Request ID
const traceId = req.headers['x-trace-id'] || generateId(); // Trace ID

logger.info({
  latency_ms: duration,
  status: statusCode,
  error_code: errorCode || 0,
  request_id: reqId,
  trace_id: traceId,
  hw_ts_ms: Date.now()
}, 'Request processed');`;

    // Find project root (where 'edge' module is located)
    const projectRoot = await findProjectRootForSnippets(workspaceRoot);
    const projectRootEscaped = projectRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    const filePathEscaped = filePath.replace(/\\/g, '/').replace(/'/g, "\\'");
    const textEscaped = text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\$/g, '\\$').replace(/\n/g, '\\n').replace(/\r/g, '\\r');
    const snippetTextEscaped = snippetText.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\$/g, '\\$').replace(/\n/g, '\\n').replace(/\r/g, '\\r');

    const proc = spawn('python', ['-c', `
import sys
import json
sys.path.insert(0, r'${projectRootEscaped}')

from edge.m5_observability.snippets.logging_inserter import plan_logging_insert

file_path = r'${filePathEscaped}'
original_text = """${textEscaped}"""
snippet_text = """${snippetTextEscaped}"""
marker = "${marker}"

result = plan_logging_insert(file_path, original_text, snippet_text, marker)
print(json.dumps(result))
    `]);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    proc.on('error', (err) => {
      reject(new Error(`Failed to plan logging snippet: ${err.message}`));
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Planning failed with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout.trim());
        resolve(result);
      } catch (err: any) {
        reject(new Error(`Failed to parse plan result: ${err.message}`));
      }
    });
  });
}

async function planMetricsSnippet(filePath: string, text: string, policyCfg: any, workspaceRoot: string): Promise<any> {
  return new Promise(async (resolve, reject) => {
    const marker = 'CC_OBS_SNIPPET';
    const labelKeys = ['endpoint', 'method', 'status']; // Default labels

    // Find project root
    const projectRoot = await findProjectRootForSnippets(workspaceRoot);
    const projectRootEscaped = projectRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    const filePathEscaped = filePath.replace(/\\/g, '/').replace(/'/g, "\\'");
    const textEscaped = text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\$/g, '\\$').replace(/\n/g, '\\n').replace(/\r/g, '\\r');
    
    // Serialize policy config to JSON and encode as base64 to avoid escape sequence issues
    const policyCfgJson = JSON.stringify(policyCfg);
    const policyCfgBase64 = Buffer.from(policyCfgJson, 'utf-8').toString('base64');
    const labelKeysJson = JSON.stringify(labelKeys);
    const labelKeysBase64 = Buffer.from(labelKeysJson, 'utf-8').toString('base64');

    const proc = spawn('python', ['-c', `
import sys
import json
import base64
sys.path.insert(0, r'${projectRootEscaped}')

from edge.m5_observability.snippets.metrics_inserter import plan_metrics_insert

file_path = r'${filePathEscaped}'
original_text = """${textEscaped}"""
# Decode base64-encoded JSON to avoid escape sequence issues
policy_cfg = json.loads(base64.b64decode('${policyCfgBase64}').decode('utf-8'))
label_keys = json.loads(base64.b64decode('${labelKeysBase64}').decode('utf-8'))
marker = "${marker}"

result = plan_metrics_insert(file_path, original_text, policy_cfg, label_keys, marker)
print(json.dumps(result))
    `]);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    proc.on('error', (err) => {
      reject(new Error(`Failed to plan metrics snippet: ${err.message}`));
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Planning failed with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout.trim());
        resolve(result);
      } catch (err: any) {
        reject(new Error(`Failed to parse plan result: ${err.message}`));
      }
    });
  });
}

async function planCorrelationSnippet(filePath: string, text: string, policyCfg: any, workspaceRoot: string): Promise<any> {
  return new Promise(async (resolve, reject) => {
    const marker = policyCfg['obs.generated_marker_comment'] || 'CC_OBS_SNIPPET';

    // Find project root
    const projectRoot = await findProjectRootForSnippets(workspaceRoot);
    const projectRootEscaped = projectRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    const filePathEscaped = filePath.replace(/\\/g, '/').replace(/'/g, "\\'");
    const textEscaped = text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\$/g, '\\$').replace(/\n/g, '\\n').replace(/\r/g, '\\r');
    
    // Serialize policy config to JSON and encode as base64 to avoid escape sequence issues
    const policyCfgJson = JSON.stringify(policyCfg);
    const policyCfgBase64 = Buffer.from(policyCfgJson, 'utf-8').toString('base64');

    const proc = spawn('python', ['-c', `
import sys
import json
import base64
sys.path.insert(0, r'${projectRootEscaped}')

from edge.m5_observability.snippets.correlation_injector import plan_correlation_inject

file_path = r'${filePathEscaped}'
original_text = """${textEscaped}"""
# Decode base64-encoded JSON to avoid escape sequence issues
policy_cfg = json.loads(base64.b64decode('${policyCfgBase64}').decode('utf-8'))
marker = "${marker}"

result = plan_correlation_inject(file_path, original_text, policy_cfg, marker)
print(json.dumps(result))
    `]);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    proc.on('error', (err) => {
      reject(new Error(`Failed to plan correlation snippet: ${err.message}`));
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Planning failed with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout.trim());
        resolve(result);
      } catch (err: any) {
        reject(new Error(`Failed to parse plan result: ${err.message}`));
      }
    });
  });
}

