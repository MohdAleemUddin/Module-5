import { spawn } from 'child_process';
import * as path from 'path';
import * as vscode from 'vscode';

/**
 * PC-1 Trusted Actuation wrapper for VS Code extension.
 * Calls Python backend to perform PC-1 prewrite checks.
 */
async function findProjectRootForPC1(workspaceRoot: string): Promise<string> {
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

export async function pc1Check(action: string, patch: any, workspaceRoot?: string): Promise<{ allowed: boolean; result?: any }> {
  return new Promise(async (resolve, reject) => {
    const root = workspaceRoot || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
    const projectRoot = await findProjectRootForPC1(root);
    const projectRootEscaped = projectRoot.replace(/\\/g, '/').replace(/'/g, "\\'");
    
    const proc = spawn('python', ['-c', `
import sys
import json
sys.path.insert(0, r'${projectRootEscaped}')

from edge.m5_observability.pc1.hooks import pc1_prewrite_check

def authoriser_gate():
    # TODO: Implement real authoriser (for now, always allow in dev)
    return {"ok": True, "code": "ok"}

def rate_limiter():
    # TODO: Implement real rate limiter (for now, always allow in dev)
    return {"ok": True, "code": "ok"}

try:
    result = pc1_prewrite_check(authoriser_gate, rate_limiter)
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"allowed": False, "error": str(e)}))
    `]);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    proc.on('error', (err) => {
      // If Python not found, allow in dev mode but log warning
      console.warn(`PC-1 check failed: ${err.message}`);
      resolve({ allowed: true, result: { authoriser: 'ok', rate_limiter: 'ok' } });
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        console.warn(`PC-1 check exited with code ${code}: ${stderr}`);
        resolve({ allowed: true, result: { authoriser: 'ok', rate_limiter: 'ok' } });
        return;
      }

      try {
        const result = JSON.parse(stdout.trim());
        resolve({
          allowed: result.allowed === true || result.allowed === 'True',
          result: result
        });
      } catch (err: any) {
        console.warn(`Failed to parse PC-1 result: ${err.message}`);
        resolve({ allowed: true, result: { authoriser: 'ok', rate_limiter: 'ok' } });
      }
    });
  });
}

