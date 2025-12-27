import * as vscode from 'vscode';
import * as fs from 'fs/promises';
import { viewLastM5Receipt } from '../receipts/view_last_receipt';

export class ObservabilityStatusBar {
  private statusBarItem: vscode.StatusBarItem;
  private receiptPath: string | undefined;
  private diagnosticsCollection: vscode.DiagnosticCollection | undefined;

  constructor(context: vscode.ExtensionContext) {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.statusBarItem.command = 'zeroui.m5.openPanel';
    this.statusBarItem.tooltip = 'M5 Observability - Click to open decision panel';
    context.subscriptions.push(this.statusBarItem);

    // Try to find receipt path
    const storagePath = context.globalStorageUri.fsPath;
    this.receiptPath = `${storagePath}/receipts_m5.jsonl`;

    this.update();
  }

  setDiagnosticsCollection(collection: vscode.DiagnosticCollection): void {
    this.diagnosticsCollection = collection;
    // Note: DiagnosticCollection doesn't have onDidChange event
    // Status bar will be updated via document save/change events in extension.ts
    // We'll also manually trigger updates when needed
  }
  
  // Public method to manually trigger update (called after diagnostics change)
  public triggerUpdate(): void {
    this.update();
  }

  async update(): Promise<void> {
    // First, try to calculate coverage from current diagnostics (dynamic)
    const dynamicCoverage = this.calculateCoverageFromDiagnostics();
    
    if (dynamicCoverage !== null) {
      // Use dynamic coverage from diagnostics
      const coverage = dynamicCoverage.coverage;
      const outcome = this.determineOutcomeFromCoverage(coverage);
      const icon = this.getIconForOutcome(outcome);
      
      this.statusBarItem.text = `${icon} OBS ${coverage.toFixed(0)}%`;
      this.statusBarItem.backgroundColor = this.getColorForOutcome(outcome);
      this.statusBarItem.show();
      return;
    }

    // Fallback to receipt if no diagnostics available
    if (!this.receiptPath) {
      this.statusBarItem.text = '$(beaker) OBS';
      this.statusBarItem.show();
      return;
    }

    try {
      const { receipt } = await viewLastM5Receipt(
        async (path: string) => {
          try {
            return await fs.readFile(path, 'utf-8');
          } catch {
            return '';
          }
        },
        this.receiptPath
      );

      if (receipt) {
        const outcome = receipt.decision?.outcome || 'unknown';
        const coverage = receipt.inputs?.telemetry_coverage_pct || 0;
        const icon = this.getIconForOutcome(outcome);
        
        this.statusBarItem.text = `${icon} OBS ${coverage.toFixed(0)}%`;
        this.statusBarItem.backgroundColor = this.getColorForOutcome(outcome);
      } else {
        this.statusBarItem.text = '$(beaker) OBS';
      }
    } catch {
      this.statusBarItem.text = '$(beaker) OBS';
    }

    this.statusBarItem.show();
  }

  private calculateCoverageFromDiagnostics(): { coverage: number; totalFiles: number; filesWithSignals: number } | null {
    // Get all diagnostics from VS Code (includes our M5 diagnostics)
    const allDiagnostics = vscode.languages.getDiagnostics();
    
    if (!allDiagnostics || allDiagnostics.length === 0) {
      return null;
    }

    const fileCoverageArray: number[] = [];
    let totalFiles = 0;
    let filesWithSignals = 0;

    // Process each file's diagnostics
    for (const [uri, diagnostics] of allDiagnostics) {
      if (uri.scheme !== 'file') {
        continue;
      }

      // Only process files with M5 Observability diagnostics
      const m5Diagnostics = diagnostics.filter((d: vscode.Diagnostic) => 
        d.source === 'M5 Observability'
      );

      if (m5Diagnostics.length === 0) {
        continue; // Skip files without M5 diagnostics
      }

      totalFiles++;
      
      // Find coverage diagnostic for this file
      const coverageDiagnostic = m5Diagnostics.find((d: vscode.Diagnostic) => 
        d.message.includes('Coverage:')
      );

      let fileCoverage = 0;

      if (coverageDiagnostic) {
        // Extract coverage from message: "Missing telemetry signals: ... Coverage: X.X%"
        const coverageMatch = coverageDiagnostic.message.match(/Coverage:\s*([\d.]+)%/);
        if (coverageMatch) {
          fileCoverage = parseFloat(coverageMatch[1]);
        }
      } else {
        // Check if it's a "pass" diagnostic (100% coverage)
        const passDiagnostic = m5Diagnostics.find((d: vscode.Diagnostic) => 
          d.code === 'CC-OB-0101' && 
          d.message.includes('All required telemetry signals present')
        );
        if (passDiagnostic) {
          fileCoverage = 100;
        } else {
          // Has diagnostics but no coverage info = assume 0% (missing signals)
          fileCoverage = 0;
        }
      }

      fileCoverageArray.push(fileCoverage);
      if (fileCoverage > 0) {
        filesWithSignals++;
      }
    }

    if (totalFiles === 0) {
      return null;
    }

    // Calculate minimum coverage across all files (per Module 5 spec)
    // Module 5 uses minimum because "coverage is only as good as the weakest surface"
    const minCoverage = fileCoverageArray.length > 0 ? Math.min(...fileCoverageArray) : 0;

    return {
      coverage: minCoverage,
      totalFiles,
      filesWithSignals
    };
  }

  private determineOutcomeFromCoverage(coverage: number): string {
    if (coverage >= 80) {
      return 'pass';
    } else if (coverage >= 60) {
      return 'warn';
    } else if (coverage >= 40) {
      return 'soft_block';
    } else {
      return 'hard_block';
    }
  }

  private getIconForOutcome(outcome: string): string {
    switch (outcome) {
      case 'pass':
        return '$(check)';
      case 'warn':
        return '$(warning)';
      case 'soft_block':
        return '$(error)';
      case 'hard_block':
        return '$(error)';
      default:
        return '$(beaker)';
    }
  }

  private getColorForOutcome(outcome: string): vscode.ThemeColor | undefined {
    switch (outcome) {
      case 'pass':
        return new vscode.ThemeColor('statusBarItem.prominentForeground');
      case 'warn':
        return new vscode.ThemeColor('statusBarItem.warningBackground');
      case 'soft_block':
      case 'hard_block':
        return new vscode.ThemeColor('statusBarItem.errorBackground');
      default:
        return undefined;
    }
  }
}

