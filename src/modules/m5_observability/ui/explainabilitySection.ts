export function renderExplainabilitySection(receiptJsonText: string): string {
  try {
    const receipt = JSON.parse(receiptJsonText);
    const decision = receipt.decision || {};
    
    // Always show explainability section (per F5.2 requirement)
    // Even if explainability is missing, show empty state
    let explainability = decision.explainability;
    
    // If explainability is missing, create empty structure
    if (!explainability) {
      explainability = {
        fired_rules: [],
        smallest_fix: { type: 'none', action_id: '', summary: '' }
      };
    }
    
    const firedRules = explainability.fired_rules || [];
    const smallestFix = explainability.smallest_fix || { type: 'none', action_id: '', summary: '' };

    let html = '<div class="explainability-section">\n';
    
    // Fired Rules section - always show (per F5.2 requirement)
    html += '  <div class="fired-rules">\n';
    html += '    <h3><span class="icon">🔥</span> Fired Rules</h3>\n';
    
    if (firedRules.length > 0) {
      html += '    <ul>\n';
      for (const rule of firedRules) {
        // Format: Rule ID, Threshold, Why (per TESTING_GUIDE.md requirements)
        const ruleId = rule.rule_id || 'UNKNOWN';
        const threshold = rule.threshold || 'N/A';
        const why = rule.why || 'No explanation';
        html += `      <li><strong>${ruleId}</strong>: ${why} (Threshold: ${threshold})</li>\n`;
      }
      html += '    </ul>\n';
    } else {
      // Show message when no rules fired (pass case)
      html += '    <p class="no-rules">✓ No rules fired - all checks passed</p>\n';
    }
    
    html += '  </div>\n';
    
    // Smallest Fix section - always show (per F5.2 requirement)
    html += '  <div class="smallest-fix">\n';
    html += '    <h3><span class="icon">🛠️</span> Smallest Fix</h3>\n';
    
    if (smallestFix.type && smallestFix.type !== 'none' && smallestFix.type !== '') {
      html += `    <p><strong>Type:</strong> ${smallestFix.type}</p>\n`;
      html += `    <p><strong>Summary:</strong> ${smallestFix.summary || 'No summary available'}</p>\n`;
      
      if (smallestFix.action_id && smallestFix.action_id !== '') {
        html += `    <button class="apply-fix-btn" data-action-id="${smallestFix.action_id}">Apply Fix</button>\n`;
      }
    } else {
      // Show message when no fix needed
      html += '    <p class="no-fix">✓ No fix needed - observability requirements met</p>\n';
    }
    
    html += '  </div>\n';
    html += '</div>\n';
    
    return html;
  } catch (error) {
    // If parsing fails, still show explainability section with error message
    return '<div class="explainability-section">\n  <div class="fired-rules"><h3><span class="icon">🔥</span> Fired Rules</h3><p class="error">Error rendering explainability: ' + String(error) + '</p></div>\n  <div class="smallest-fix"><h3><span class="icon">🛠️</span> Smallest Fix</h3><p class="error">Error rendering explainability</p></div>\n</div>\n';
  }
}

