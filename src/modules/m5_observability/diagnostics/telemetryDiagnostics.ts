import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs/promises';
import { getRequiredSignals } from '../policy/policyLoader';

export interface TelemetryFinding {
  file: string;
  line: number;
  severity: 'error' | 'warning' | 'info';
  code: string;
  message: string;
  missingSignals?: string[];
  coverage?: number;
}

const PROBLEM_CODES = {
  PASS: 'CC-OB-0101',
  WARN: 'CC-OB-0201',
  SOFT: 'CC-OB-0301',
  HARD: 'CC-OB-0401',
};

export class TelemetryDiagnosticsProvider {
  public diagnosticCollection: vscode.DiagnosticCollection;
  private outputChannel: vscode.OutputChannel;
  private statusBarUpdater: (() => void) | undefined;

  constructor(context: vscode.ExtensionContext) {
    this.diagnosticCollection = vscode.languages.createDiagnosticCollection('m5-observability');
    this.outputChannel = vscode.window.createOutputChannel('M5 Observability');
    context.subscriptions.push(this.diagnosticCollection, this.outputChannel);
  }
  
  setStatusBarUpdater(updater: () => void): void {
    this.statusBarUpdater = updater;
  }

  async checkDocument(document: vscode.TextDocument): Promise<void> {
    if (document.uri.scheme !== 'file') {
      return;
    }

    const filePath = document.uri.fsPath;
    
    // Only check code files, not config files
    if (!this.isCodeFile(filePath)) {
      // Clear diagnostics for non-code files
      this.diagnosticCollection.delete(document.uri);
      return;
    }

    const text = document.getText();

    try {
      // Run Python backend to check telemetry
      const findings = await this.runTelemetryCheck(filePath, text);
      this.updateDiagnostics(document, findings);
    } catch (error: any) {
      this.outputChannel.appendLine(`Error checking ${filePath}: ${error.message}`);
    }
  }

  private isCodeFile(filePath: string): boolean {
    // Code file extensions (same as Python smoke runner)
    const codeExtensions = ['.js', '.ts', '.py', '.java', '.go', '.rs', '.cpp', '.c', '.cs', '.rb', '.php'];
    const ext = path.extname(filePath).toLowerCase();
    
    // Check if it's a code file
    if (codeExtensions.includes(ext)) {
      // Also check if it's in an ignored directory
      const normalizedPath = filePath.replace(/\\/g, '/');
      const ignoreDirs = ['node_modules', 'dist', 'out', '__pycache__', '.venv', 'venv', '.git'];
      return !ignoreDirs.some(dir => normalizedPath.includes(`/${dir}/`) || normalizedPath.includes(`\\${dir}\\`));
    }
    
    return false;
  }

  private async runTelemetryCheck(filePath: string, text: string): Promise<TelemetryFinding[]> {
    return new Promise(async (resolve, reject) => {
      const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
      const scriptPath = path.join(
        workspaceRoot,
        'edge',
        'm5_observability',
        'tools',
        'm5_ci_gate_cli.py'
      );

      // Load required signals from policy dynamically
      const requiredSignals = await getRequiredSignals(workspaceRoot);
      const findings: TelemetryFinding[] = [];

      // Remove comments and strings to avoid false positives
      // Simple approach: remove single-line comments and string literals
      let codeText = text;
      
      // Remove single-line comments (// ...)
      codeText = codeText.replace(/\/\/.*$/gm, '');
      
      // Remove multi-line comments (/* ... */)
      codeText = codeText.replace(/\/\*[\s\S]*?\*\//g, '');
      
      // Remove string literals (basic - handles single and double quotes)
      codeText = codeText.replace(/['"`][^'"`]*['"`]/g, '');
      
      // Simple text-based check on cleaned code
      const missing: string[] = [];
      for (const signal of requiredSignals) {
        // Check for signal as identifier (word boundary) to avoid partial matches
        const regex = new RegExp(`\\b${signal.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`);
        if (!regex.test(codeText)) {
          missing.push(signal);
        }
      }

      // Check for dynamic keys in file content
      const dynamicKeyPattern = /(?:labels\[|label_|tags\[)[^\]]*(?:\$\{[^\}]*\}|\{[^\}]*\})[^\]]*\]?/g;
      const dynamicKeyMatches = codeText.match(dynamicKeyPattern);
      if (dynamicKeyMatches && dynamicKeyMatches.length > 0) {
        findings.push({
          file: filePath,
          line: 0,
          severity: 'error',
          code: PROBLEM_CODES.HARD,
          message: `Dynamic keys detected: ${dynamicKeyMatches.slice(0, 3).join(', ')}${dynamicKeyMatches.length > 3 ? '...' : ''}. Use static keys instead.`,
          missingSignals: [],
          coverage: 0,
        });
      }

      if (missing.length > 0) {
        const coverage = ((requiredSignals.length - missing.length) / requiredSignals.length) * 100;
        const severity = this.determineSeverity(missing, coverage);
        const code = this.getProblemCode(severity);

        findings.push({
          file: filePath,
          line: 0,
          severity,
          code,
          message: `Missing telemetry signals: ${missing.join(', ')}. Coverage: ${coverage.toFixed(1)}%`,
          missingSignals: missing,
          coverage,
        });
      } else {
        findings.push({
          file: filePath,
          line: 0,
          severity: 'info',
          code: PROBLEM_CODES.PASS,
          message: 'All required telemetry signals present',
          coverage: 100,
        });
      }

      resolve(findings);
    });
  }

  private determineSeverity(missingSignals: string[], coverage: number): 'error' | 'warning' | 'info' {
    const hasCritical = missingSignals.includes('request_id') || 
                       missingSignals.includes('trace_id') || 
                       missingSignals.includes('hw_ts_ms');
    
    if (hasCritical || coverage < 60) {
      return 'error';
    } else if (coverage < 80) {
      return 'warning';
    }
    return 'info';
  }

  private getProblemCode(severity: 'error' | 'warning' | 'info'): string {
    switch (severity) {
      case 'error':
        return PROBLEM_CODES.HARD;
      case 'warning':
        return PROBLEM_CODES.SOFT;
      default:
        return PROBLEM_CODES.PASS;
    }
  }

  private updateDiagnostics(document: vscode.TextDocument, findings: TelemetryFinding[]): void {
    const diagnostics: vscode.Diagnostic[] = [];

    for (const finding of findings) {
      if (finding.file !== document.uri.fsPath) {
        continue;
      }

      const range = new vscode.Range(
        Math.max(0, finding.line - 1),
        0,
        finding.line,
        0
      );

      let severity: vscode.DiagnosticSeverity;
      switch (finding.severity) {
        case 'error':
          severity = vscode.DiagnosticSeverity.Error;
          break;
        case 'warning':
          severity = vscode.DiagnosticSeverity.Warning;
          break;
        default:
          severity = vscode.DiagnosticSeverity.Information;
      }

      const diagnostic = new vscode.Diagnostic(range, finding.message, severity);
      diagnostic.code = finding.code;
      diagnostic.source = 'M5 Observability';
      diagnostics.push(diagnostic);
    }

    // Update diagnostics
    this.diagnosticCollection.set(document.uri, diagnostics);
    
    // Trigger status bar update after diagnostics change
    if (this.statusBarUpdater) {
      this.statusBarUpdater();
    }
  }

  clear(): void {
    this.diagnosticCollection.clear();
  }
}

