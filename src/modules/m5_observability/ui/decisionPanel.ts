import * as vscode from 'vscode';
import { renderExplainabilitySection } from './explainabilitySection';
import { viewLastM5Receipt } from '../receipts/view_last_receipt';
import * as fs from 'fs/promises';
import * as path from 'path';
import { getCoverageThresholds } from '../policy/policyLoader';

interface FileCoverage {
  file: string;
  coverage: number;
  missing: string[];
  outcome: string;
}

export class DecisionPanel {
  private panel: vscode.WebviewPanel | undefined;
  private context: vscode.ExtensionContext;
  private diagnosticsCollection: vscode.DiagnosticCollection | undefined;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
  }

  public setDiagnosticsCollection(collection: vscode.DiagnosticCollection): void {
    this.diagnosticsCollection = collection;
    // Note: DiagnosticCollection doesn't have onDidChange, so we rely on extension.ts
    // to call refresh() when diagnostics change
  }

  async show(receiptPath?: string): Promise<void> {
    if (this.panel) {
      this.panel.reveal();
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      'm5DecisionPanel',
      'M5 Observability Decision',
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    this.panel.onDidDispose(() => {
      this.panel = undefined;
    });

    this.panel.webview.onDidReceiveMessage(async (message) => {
      if (message.command === 'insertSnippet') {
        vscode.commands.executeCommand('zeroui.m5.insertObsSnippet');
      } else if (message.command === 'redactPii') {
        vscode.commands.executeCommand('zeroui.m5.redactPii');
      } else if (message.command === 'runSmokeTests') {
        vscode.commands.executeCommand('zeroui.m5.runSmokeTests');
      }
    });

    await this.updateContent(receiptPath);
  }

  private async updateContent(receiptPath?: string): Promise<void> {
    if (!this.panel) {
      return;
    }

    let html = this.getBaseHtml();

    // Calculate coverage from current diagnostics (dynamic)
    const diagnosticsData = this.calculateCoverageFromDiagnostics();
    
    if (diagnosticsData && diagnosticsData.files.length > 0) {
      // Show dynamic coverage from diagnostics
      const minCoverage = diagnosticsData.minCoverage;
      const avgCoverage = diagnosticsData.avgCoverage;
      const totalFiles = diagnosticsData.files.length;
      const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      
      // Get status class (await async call)
      const statusClass = await this.getStatusClass(minCoverage, workspaceRoot);
      html += `<div class="status-card ${statusClass}">\n`;
      html += `  <div class="status-header">\n`;
      html += `    <span class="status-icon">${this.getStatusIcon(minCoverage)}</span>\n`;
      html += `    <div class="status-info">\n`;
      html += `      <h2>Observability Status</h2>\n`;
      html += `      <p class="status-outcome">${this.getOutcomeText(minCoverage)}</p>\n`;
      html += `    </div>\n`;
      html += `  </div>\n`;
      html += `</div>\n`;

      // Coverage bar with both min and avg
      html += this.renderCoverageBar(minCoverage, avgCoverage, totalFiles);

      // File-by-file breakdown
      html += `<div class="files-breakdown">\n`;
      html += `  <h3><span class="icon">📊</span> File Coverage Breakdown</h3>\n`;
      html += `  <div class="files-list">\n`;
      
      // Render all file cards (await each async call)
      for (const file of diagnosticsData.files) {
        const fileCardHtml = await this.renderFileCard(file, workspaceRoot);
        html += fileCardHtml;
      }
      
      html += `  </div>\n`;
      html += `</div>\n`;

      // Missing signals summary
      const allMissing = new Set<string>();
      diagnosticsData.files.forEach(f => f.missing.forEach(m => allMissing.add(m)));
      if (allMissing.size > 0) {
        html += `<div class="missing-signals-card">\n`;
        html += `  <h3><span class="icon">⚠️</span> Missing Signals Across All Files</h3>\n`;
        html += `  <div class="signals-grid">\n`;
        for (const signal of Array.from(allMissing).sort()) {
          html += `    <span class="signal-badge">${this.escapeHtml(signal)}</span>\n`;
        }
        html += `  </div>\n`;
        html += `</div>\n`;
      }
    }

    // Also show receipt data if available
    if (receiptPath) {
      try {
        await fs.access(receiptPath);
        const { summary, receipt } = await viewLastM5Receipt(
          async (path: string) => {
            return await fs.readFile(path, 'utf-8');
          },
          receiptPath
        );

        if (receipt) {
          html += `<div class="receipt-card">\n`;
          html += `  <h3><span class="icon">📋</span> Last Smoke Test Receipt</h3>\n`;
          html += `  <div class="receipt-summary">\n`;
          html += `    <pre>${this.escapeHtml(summary)}</pre>\n`;
          html += `  </div>\n`;
          
          // Always show explainability section when receipt exists (per F5.2 requirement)
          // The explainability section handles empty cases gracefully
          html += renderExplainabilitySection(JSON.stringify(receipt));
          
          html += `</div>\n`;
        }
      } catch (error: any) {
        // Silently ignore receipt errors if we have diagnostics
        if (!diagnosticsData || diagnosticsData.files.length === 0) {
          if (error.code !== 'ENOENT') {
            html += `<div class="error">Error loading receipt: ${this.escapeHtml(error.message)}</div>\n`;
          } else {
            html += `<div class="no-data">No receipt data available. Run "Run Observability Smoke Tests" to generate a receipt.</div>\n`;
          }
        }
      }
    } else if (!diagnosticsData || diagnosticsData.files.length === 0) {
      html += `<div class="no-data">\n`;
      html += `  <div class="no-data-icon">🔍</div>\n`;
      html += `  <p>No observability data available.</p>\n`;
      html += `  <p class="hint">Save a code file to see coverage analysis.</p>\n`;
      html += `</div>\n`;
    }

    html += `</body>\n</html>`;
    this.panel.webview.html = html;
  }

  private calculateCoverageFromDiagnostics(): { files: FileCoverage[]; minCoverage: number; avgCoverage: number } | null {
    if (!this.diagnosticsCollection) {
      return null;
    }

    const files: FileCoverage[] = [];
    const coverages: number[] = [];

    // Get all diagnostics and filter for M5 Observability ones
    const allDiagnostics = vscode.languages.getDiagnostics();
    
    for (const [uri, diagnostics] of allDiagnostics) {
      if (uri.scheme !== 'file') continue;

      // Filter for M5 Observability diagnostics
      const m5Diagnostics = diagnostics.filter((d: vscode.Diagnostic) => 
        d.source === 'M5 Observability'
      );

      if (m5Diagnostics.length === 0) continue;

      const fileName = path.basename(uri.fsPath);
      let fileCoverage = 0;
      let missing: string[] = [];
      let outcome = 'unknown';

      const coverageDiagnostic = m5Diagnostics.find((d: vscode.Diagnostic) => 
        d.message.includes('Coverage:')
      );

      if (coverageDiagnostic) {
        const coverageMatch = coverageDiagnostic.message.match(/Coverage:\s*([\d.]+)%/);
        if (coverageMatch) {
          fileCoverage = parseFloat(coverageMatch[1]);
        }
        
        // Parse missing signals more robustly
        const missingMatch = coverageDiagnostic.message.match(/Missing telemetry signals:\s*([^.]+?)(?:\.|$)/);
        if (missingMatch && missingMatch[1].trim() !== 'none') {
          missing = missingMatch[1].split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
        }
        
        // Determine outcome from diagnostic code
        if (coverageDiagnostic.code === 'CC-OB-0101') {
          outcome = 'pass';
        } else if (coverageDiagnostic.code === 'CC-OB-0201') {
          outcome = 'warn';
        } else if (coverageDiagnostic.code === 'CC-OB-0301') {
          outcome = 'soft_block';
        } else {
          outcome = 'hard_block';
        }
      } else {
        // Check for pass diagnostic
        const passDiagnostic = m5Diagnostics.find((d: vscode.Diagnostic) => 
          d.code === 'CC-OB-0101' && d.message.includes('All required telemetry signals present')
        );
        if (passDiagnostic) {
          fileCoverage = 100;
          outcome = 'pass';
        } else {
          // Has diagnostics but no coverage info = assume 0% (missing signals)
          fileCoverage = 0;
          outcome = 'hard_block';
          // Try to extract missing signals from any diagnostic message
          const allMissingSignals = new Set<string>();
          for (const diag of m5Diagnostics) {
            const missingMatch = diag.message.match(/Missing telemetry signals:\s*([^.]+?)(?:\.|$)/);
            if (missingMatch && missingMatch[1].trim() !== 'none') {
              missingMatch[1].split(',').forEach((s: string) => {
                const trimmed = s.trim();
                if (trimmed.length > 0) allMissingSignals.add(trimmed);
              });
            }
          }
          missing = Array.from(allMissingSignals).sort();
        }
      }

      files.push({ file: fileName, coverage: fileCoverage, missing, outcome });
      coverages.push(fileCoverage);
    }

    if (files.length === 0) {
      return null;
    }

    const minCoverage = Math.min(...coverages);
    const avgCoverage = coverages.reduce((a, b) => a + b, 0) / coverages.length;

    // Sort files by coverage (lowest first) for better UX
    files.sort((a, b) => a.coverage - b.coverage);

    return { files, minCoverage, avgCoverage };
  }

  private async renderFileCard(file: FileCoverage, workspaceRoot?: string): Promise<string> {
    const thresholds = await getCoverageThresholds(workspaceRoot);
    const coverageColor = file.coverage >= thresholds.warn ? 'success' : file.coverage >= thresholds.block ? 'warning' : 'error';
    const outcomeIcon = file.outcome === 'pass' ? '✅' : file.outcome === 'warn' ? '⚠️' : '❌';
    
    return `
      <div class="file-card ${coverageColor}">
        <div class="file-header">
          <span class="file-icon">${outcomeIcon}</span>
          <span class="file-name">${this.escapeHtml(file.file)}</span>
          <span class="file-coverage ${coverageColor}">${file.coverage.toFixed(1)}%</span>
        </div>
        ${file.missing.length > 0 ? `
          <div class="file-missing">
            <span class="missing-label">Missing:</span>
            ${file.missing.map((s: string) => `<span class="signal-tag">${this.escapeHtml(s)}</span>`).join('')}
          </div>
        ` : '<div class="file-complete">✓ All signals present</div>'}
      </div>
    `;
  }

  private async getStatusClass(coverage: number, workspaceRoot?: string): Promise<string> {
    const thresholds = await getCoverageThresholds(workspaceRoot);
    if (coverage >= thresholds.warn) return 'status-pass';
    if (coverage >= thresholds.block) return 'status-warn';
    if (coverage >= thresholds.block * 0.67) return 'status-soft'; // 2/3 of block threshold
    return 'status-hard';
  }

  private getStatusIcon(coverage: number): string {
    if (coverage >= 80) return '✅';
    if (coverage >= 60) return '⚠️';
    if (coverage >= 40) return '🔶';
    return '❌';
  }

  private getOutcomeText(coverage: number): string {
    if (coverage >= 80) return 'PASS - Good observability coverage';
    if (coverage >= 60) return 'WARN - Some signals missing';
    if (coverage >= 40) return 'SOFT BLOCK - Significant gaps';
    return 'HARD BLOCK - Critical signals missing';
  }

  private renderCoverageBar(minCoverage: number, avgCoverage: number, totalFiles: number): string {
    const minPercentage = Math.round(minCoverage);
    const avgPercentage = Math.round(avgCoverage);
    const minColor = minCoverage >= 80 ? '#4caf50' : minCoverage >= 60 ? '#ff9800' : '#f44336';
    const avgColor = avgCoverage >= 80 ? '#81c784' : avgCoverage >= 60 ? '#ffb74d' : '#e57373';
    
    return `
      <div class="coverage-section">
        <h3><span class="icon">📈</span> Telemetry Coverage</h3>
        <div class="coverage-stats">
          <div class="stat-item">
            <span class="stat-label">Minimum (Module 5)</span>
            <span class="stat-value" style="color: ${minColor}">${minCoverage.toFixed(1)}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Average</span>
            <span class="stat-value" style="color: ${avgColor}">${avgCoverage.toFixed(1)}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Files Checked</span>
            <span class="stat-value">${totalFiles}</span>
          </div>
        </div>
        <div class="bar-container">
          <div class="bar-fill-min" style="width: ${minPercentage}%; background: linear-gradient(90deg, ${minColor} 0%, ${minColor}dd 100%);"></div>
          <div class="bar-fill-avg" style="width: ${avgPercentage}%; background: linear-gradient(90deg, ${avgColor}88 0%, ${avgColor}44 100%);"></div>
          <span class="bar-label-min">Min: ${minPercentage}%</span>
          <span class="bar-label-avg">Avg: ${avgPercentage}%</span>
        </div>
        <p class="coverage-note">Module 5 uses minimum coverage (weakest surface determines overall status)</p>
      </div>
    `;
  }

  private getBaseHtml(): string {
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>M5 Observability Decision</title>
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      font-family: var(--vscode-font-family);
      padding: 24px;
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      margin: 0;
      line-height: 1.6;
    }
    h1 {
      margin: 0 0 24px 0;
      font-size: 24px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    h1::before {
      content: "🔬";
      font-size: 28px;
    }
    h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
    h3 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .icon {
      font-size: 18px;
    }
    .status-card {
      background: var(--vscode-editor-background);
      border: 2px solid var(--vscode-panel-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .status-card.status-pass {
      border-color: #4caf50;
      background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, var(--vscode-editor-background) 100%);
    }
    .status-card.status-warn {
      border-color: #ff9800;
      background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, var(--vscode-editor-background) 100%);
    }
    .status-card.status-soft {
      border-color: #ff9800;
      background: linear-gradient(135deg, rgba(255, 152, 0, 0.15) 0%, var(--vscode-editor-background) 100%);
    }
    .status-card.status-hard {
      border-color: #f44336;
      background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, var(--vscode-editor-background) 100%);
    }
    .status-header {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .status-icon {
      font-size: 32px;
    }
    .status-info h2 {
      margin-bottom: 4px;
    }
    .status-outcome {
      margin: 0;
      color: var(--vscode-descriptionForeground);
      font-size: 14px;
    }
    .coverage-section {
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .coverage-stats {
      display: flex;
      gap: 24px;
      margin: 16px 0;
      flex-wrap: wrap;
    }
    .stat-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .stat-label {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .stat-value {
      font-size: 24px;
      font-weight: 700;
    }
    .bar-container {
      position: relative;
      width: 100%;
      height: 48px;
      background: var(--vscode-input-background);
      border: 2px solid var(--vscode-panel-border);
      border-radius: 8px;
      overflow: hidden;
      margin: 16px 0;
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    .bar-fill-min {
      position: absolute;
      height: 100%;
      top: 0;
      left: 0;
      transition: width 0.5s ease;
      z-index: 2;
      border-radius: 8px 0 0 8px;
    }
    .bar-fill-avg {
      position: absolute;
      height: 50%;
      top: 50%;
      left: 0;
      transform: translateY(-50%);
      transition: width 0.5s ease;
      z-index: 1;
      opacity: 0.6;
      border-radius: 8px 0 0 8px;
    }
    .bar-label-min {
      position: absolute;
      top: 50%;
      left: 12px;
      transform: translateY(-50%);
      font-weight: 700;
      font-size: 14px;
      color: white;
      text-shadow: 0 1px 3px rgba(0,0,0,0.5);
      z-index: 3;
      pointer-events: none;
    }
    .bar-label-avg {
      position: absolute;
      top: 50%;
      right: 12px;
      transform: translateY(-50%);
      font-weight: 600;
      font-size: 12px;
      color: var(--vscode-foreground);
      z-index: 3;
      pointer-events: none;
      background: rgba(0,0,0,0.1);
      padding: 2px 6px;
      border-radius: 4px;
    }
    .coverage-note {
      margin: 12px 0 0 0;
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      font-style: italic;
    }
    .files-breakdown {
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .files-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 16px;
      max-height: 400px;
      overflow-y: auto;
    }
    .files-list::-webkit-scrollbar {
      width: 8px;
    }
    .files-list::-webkit-scrollbar-track {
      background: var(--vscode-input-background);
      border-radius: 4px;
    }
    .files-list::-webkit-scrollbar-thumb {
      background: var(--vscode-scrollbarSlider-background);
      border-radius: 4px;
    }
    .files-list::-webkit-scrollbar-thumb:hover {
      background: var(--vscode-scrollbarSlider-hoverBackground);
    }
    .file-card {
      background: var(--vscode-input-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 6px;
      padding: 16px;
      transition: all 0.2s;
      cursor: pointer;
    }
    .file-card:hover {
      border-color: var(--vscode-focusBorder);
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      transform: translateY(-1px);
    }
    .file-card.error {
      border-left: 4px solid #f44336;
    }
    .file-card.warning {
      border-left: 4px solid #ff9800;
    }
    .file-card.success {
      border-left: 4px solid #4caf50;
    }
    .file-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .file-icon {
      font-size: 18px;
    }
    .file-name {
      flex: 1;
      font-weight: 600;
      font-family: var(--vscode-editor-font-family);
    }
    .file-coverage {
      font-weight: 700;
      font-size: 16px;
      padding: 4px 12px;
      border-radius: 12px;
      background: var(--vscode-input-background);
    }
    .file-coverage.error {
      color: #f44336;
    }
    .file-coverage.warning {
      color: #ff9800;
    }
    .file-coverage.success {
      color: #4caf50;
    }
    .file-missing {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--vscode-panel-border);
    }
    .missing-label {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      font-weight: 600;
    }
    .signal-tag {
      display: inline-block;
      padding: 4px 10px;
      background: var(--vscode-input-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 12px;
      font-size: 11px;
      font-family: var(--vscode-editor-font-family);
      color: var(--vscode-errorForeground);
      font-weight: 500;
      transition: all 0.15s;
    }
    .signal-tag:hover {
      background: var(--vscode-inputValidation-errorBackground);
      border-color: var(--vscode-errorForeground);
    }
    .file-complete {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--vscode-panel-border);
      color: #4caf50;
      font-size: 13px;
      font-weight: 600;
    }
    .missing-signals-card {
      background: var(--vscode-inputValidation-errorBackground);
      border: 1px solid var(--vscode-errorForeground);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .missing-signals-card h3 {
      color: var(--vscode-errorForeground);
    }
    .signals-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .signal-badge {
      display: inline-block;
      padding: 6px 12px;
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-errorForeground);
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: var(--vscode-errorForeground);
      font-family: var(--vscode-editor-font-family);
    }
    .receipt-card {
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .receipt-summary {
      background: var(--vscode-input-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 6px;
      padding: 16px;
      margin-top: 12px;
    }
    .receipt-summary pre {
      margin: 0;
      font-family: var(--vscode-editor-font-family);
      font-size: 13px;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .explainability-section {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px dashed var(--vscode-panel-border);
    }
    .fired-rules, .smallest-fix {
      margin-top: 16px;
      padding: 12px;
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 6px;
    }
    .fired-rules h3, .smallest-fix h3 {
      margin-top: 0;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .fired-rules ul {
      margin: 8px 0;
      padding-left: 20px;
    }
    .fired-rules li, .smallest-fix p {
      margin: 6px 0;
      line-height: 1.5;
    }
    .no-rules, .no-fix {
      color: var(--vscode-descriptionForeground);
      font-style: italic;
      padding: 10px;
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      margin: 8px 0;
    }
    .apply-fix-btn {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 8px 16px;
      margin-top: 8px;
      cursor: pointer;
      border-radius: 4px;
      font-size: 0.9em;
    }
    .apply-fix-btn:hover {
      background: var(--vscode-button-hoverBackground);
    }
    button {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 10px 20px;
      margin: 8px 8px 8px 0;
      cursor: pointer;
      border-radius: 6px;
      font-weight: 600;
      transition: all 0.2s;
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .error {
      color: var(--vscode-errorForeground);
      padding: 16px;
      background: var(--vscode-inputValidation-errorBackground);
      border-radius: 6px;
      border: 1px solid var(--vscode-errorForeground);
    }
    .no-data {
      padding: 48px 24px;
      text-align: center;
      color: var(--vscode-descriptionForeground);
      background: var(--vscode-input-background);
      border: 2px dashed var(--vscode-panel-border);
      border-radius: 8px;
    }
    .no-data-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
    .no-data p {
      margin: 8px 0;
      font-size: 14px;
    }
    .hint {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      font-style: italic;
    }
  </style>
</head>
<body>
  <h1>M5 Observability Decision Panel</h1>
`;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  async refresh(receiptPath?: string): Promise<void> {
    if (this.panel) {
      await this.updateContent(receiptPath);
    }
  }
}

