import * as vscode from 'vscode';
import { registerPiiRedaction } from './modules/m5_observability/quickfix/piiRedaction';
import { TelemetryDiagnosticsProvider } from './modules/m5_observability/diagnostics/telemetryDiagnostics';
import { DecisionPanel } from './modules/m5_observability/ui/decisionPanel';
import { ObservabilityStatusBar } from './modules/m5_observability/ui/statusBar';
import { registerSnippetCommands } from './modules/m5_observability/commands/snippetCommands';
import { registerSmokeTestCommand } from './modules/m5_observability/commands/smokeTestCommand';
import * as path from 'path';
import * as fs from 'fs/promises';

let decisionPanel: DecisionPanel;
let diagnosticsProvider: TelemetryDiagnosticsProvider;
let statusBar: ObservabilityStatusBar;

export function activate(context: vscode.ExtensionContext) {
  // Initialize components
  diagnosticsProvider = new TelemetryDiagnosticsProvider(context);
  decisionPanel = new DecisionPanel(context);
  statusBar = new ObservabilityStatusBar(context);
  
  // Connect diagnostics collection to status bar and decision panel for dynamic updates
  const diagnosticsCollection = (diagnosticsProvider as any).diagnosticCollection;
  if (diagnosticsCollection) {
    statusBar.setDiagnosticsCollection(diagnosticsCollection);
    decisionPanel.setDiagnosticsCollection(diagnosticsCollection);
    // Set up status bar updater to trigger updates when diagnostics change
    (diagnosticsProvider as any).setStatusBarUpdater(() => {
      statusBar.update();
    });
  }

  // Register commands
  const openPanelDisposable = vscode.commands.registerCommand('zeroui.m5.openPanel', async () => {
    const receiptPath = path.join(context.globalStorageUri.fsPath, 'receipts_m5.jsonl');
    await decisionPanel.show(receiptPath);
  });

  const refreshPanelDisposable = vscode.commands.registerCommand(
    'zeroui.m5.refreshDecisionPanel',
    async (receiptPath?: string) => {
      if (receiptPath) {
        await decisionPanel.refresh(receiptPath);
      } else {
        const defaultPath = path.join(context.globalStorageUri.fsPath, 'receipts_m5.jsonl');
        await decisionPanel.refresh(defaultPath);
      }
      await statusBar.update();
    }
  );

  registerPiiRedaction(context);
  registerSnippetCommands(context);
  registerSmokeTestCommand(context);

  // Tree view
  const treeDataProvider = new M5TreeDataProvider(context);
  const treeView = vscode.window.createTreeView('zeroui-view-main', {
    treeDataProvider,
  });

  // Document save handler
  const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
    await diagnosticsProvider.checkDocument(document);
    await statusBar.update();
    // Refresh decision panel if open
    const receiptPath = path.join(context.globalStorageUri.fsPath, 'receipts_m5.jsonl');
    await decisionPanel.refresh(receiptPath);
    // Refresh tree view
    treeDataProvider.refresh();
  });

  // Document change handler (for new files, etc.)
  const changeDisposable = vscode.workspace.onDidChangeTextDocument(async (event) => {
    // Update status bar when files change
    await statusBar.update();
  });

  // File open handler
  const openDisposable = vscode.workspace.onDidOpenTextDocument(async (document) => {
    await diagnosticsProvider.checkDocument(document);
    await statusBar.update();
    // Refresh decision panel if open
    const receiptPath = path.join(context.globalStorageUri.fsPath, 'receipts_m5.jsonl');
    await decisionPanel.refresh(receiptPath);
    // Refresh tree view
    treeDataProvider.refresh();
  });

  // File create handler (when new files are added)
  const createDisposable = vscode.workspace.onDidCreateFiles(async (event) => {
    for (const file of event.files) {
      try {
        const document = await vscode.workspace.openTextDocument(file);
        await diagnosticsProvider.checkDocument(document);
      } catch {
        // Ignore files that can't be opened as text
      }
    }
    await statusBar.update();
    // Refresh tree view
    treeDataProvider.refresh();
  });

  // Initial check for open documents
  vscode.workspace.textDocuments.forEach((doc) => {
    diagnosticsProvider.checkDocument(doc);
  });
  
  // Update status bar after initial checks (with delay to ensure diagnostics are set)
  setTimeout(() => {
    statusBar.update();
  }, 1500);

  context.subscriptions.push(
    openPanelDisposable,
    refreshPanelDisposable,
    treeView,
    saveDisposable,
    changeDisposable,
    openDisposable,
    createDisposable
  );
}

export function deactivate() {}

class M5TreeDataProvider implements vscode.TreeDataProvider<M5TreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<M5TreeItem | undefined | null | void> =
    new vscode.EventEmitter<M5TreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<M5TreeItem | undefined | null | void> =
    this._onDidChangeTreeData.event;

  constructor(private context: vscode.ExtensionContext) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: M5TreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: M5TreeItem): Promise<M5TreeItem[]> {
    if (!element) {
      const items: M5TreeItem[] = [];

      // Calculate current coverage from diagnostics (dynamic)
      const currentStatus = this.calculateCurrentStatus();
      
      if (currentStatus) {
        // Show current status from diagnostics
        const outcomeText = currentStatus.outcome.toUpperCase();
        const coverageText = currentStatus.coverage.toFixed(0);
        const icon = this.getStatusIcon(currentStatus.outcome);
        
        items.push(
          new M5TreeItem(
            `${icon} Current: ${outcomeText} (${coverageText}% coverage)`,
            vscode.TreeItemCollapsibleState.None,
            undefined,
            currentStatus.outcome === 'pass' ? 'info' : 
            currentStatus.outcome === 'warn' ? 'warning' : 'error'
          )
        );
      } else {
        // Fallback to receipt if no diagnostics
        try {
          const receiptPath = path.join(this.context.globalStorageUri.fsPath, 'receipts_m5.jsonl');
          const content = await fs.readFile(receiptPath, 'utf-8');
          const lines = content.split('\n').filter((l) => l.trim());
          if (lines.length > 0) {
            const lastReceipt = JSON.parse(lines[lines.length - 1]);
            const outcome = lastReceipt.decision?.outcome || 'unknown';
            const coverage = lastReceipt.inputs?.telemetry_coverage_pct || 0;
            const icon = this.getStatusIcon(outcome);
            items.push(
              new M5TreeItem(
                `${icon} Last Smoke Test: ${outcome.toUpperCase()} (${coverage.toFixed(0)}% coverage)`,
                vscode.TreeItemCollapsibleState.None
              )
            );
          }
        } catch {
          // No receipt yet
        }
      }

      items.push(
        new M5TreeItem('Observability Status', vscode.TreeItemCollapsibleState.None, {
          command: 'zeroui.m5.openPanel',
          title: 'Open Decision Panel',
        }),
        new M5TreeItem('Run Smoke Tests', vscode.TreeItemCollapsibleState.None, {
          command: 'zeroui.m5.runSmokeTests',
          title: 'Run Smoke Tests',
        })
      );

      return items;
    }
    return [];
  }

  private calculateCurrentStatus(): { outcome: string; coverage: number } | null {
    const allDiagnostics = vscode.languages.getDiagnostics();
    
    if (!allDiagnostics || allDiagnostics.length === 0) {
      return null;
    }

    const fileCoverageArray: number[] = [];

    for (const [uri, diagnostics] of allDiagnostics) {
      if (uri.scheme !== 'file') continue;

      const m5Diagnostics = diagnostics.filter((d: vscode.Diagnostic) => 
        d.source === 'M5 Observability'
      );

      if (m5Diagnostics.length === 0) continue;

      const coverageDiagnostic = m5Diagnostics.find((d: vscode.Diagnostic) => 
        d.message.includes('Coverage:')
      );

      let fileCoverage = 0;

      if (coverageDiagnostic) {
        const coverageMatch = coverageDiagnostic.message.match(/Coverage:\s*([\d.]+)%/);
        if (coverageMatch) {
          fileCoverage = parseFloat(coverageMatch[1]);
        }
      } else {
        const passDiagnostic = m5Diagnostics.find((d: vscode.Diagnostic) => 
          d.code === 'CC-OB-0101'
        );
        if (passDiagnostic) {
          fileCoverage = 100;
        }
      }

      fileCoverageArray.push(fileCoverage);
    }

    if (fileCoverageArray.length === 0) {
      return null;
    }

    const minCoverage = Math.min(...fileCoverageArray);
    const outcome = this.determineOutcome(minCoverage);

    return { outcome, coverage: minCoverage };
  }

  private determineOutcome(coverage: number): string {
    if (coverage >= 80) return 'pass';
    if (coverage >= 60) return 'warn';
    if (coverage >= 40) return 'soft_block';
    return 'hard_block';
  }

  private getStatusIcon(outcome: string): string {
    switch (outcome) {
      case 'pass':
        return '✅';
      case 'warn':
        return '⚠️';
      case 'soft_block':
        return '🔶';
      case 'hard_block':
        return '❌';
      default:
        return '🔍';
    }
  }
}

class M5TreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly command?: vscode.Command,
    public readonly severity?: 'error' | 'warning' | 'info'
  ) {
    super(label, collapsibleState);
    if (command) {
      this.command = command;
    }
    if (severity) {
      this.iconPath = new vscode.ThemeIcon(
        severity === 'error' ? 'error' :
        severity === 'warning' ? 'warning' :
        'info'
      );
    }
  }
}

