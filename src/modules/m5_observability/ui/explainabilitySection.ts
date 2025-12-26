export function renderExplainabilitySection(receiptJsonText: string): string {
  const receipt = JSON.parse(receiptJsonText);
  const decision = receipt.decision || {};
  const explainability = decision.explainability || {};
  const firedRules = explainability.fired_rules || [];
  const smallestFix = explainability.smallest_fix || {};

  let html = '<div class="explainability-section">\n';
  
  // Fired rules list
  html += '  <div class="fired-rules">\n';
  html += '    <h3>Fired Rules</h3>\n';
  html += '    <ul>\n';
  
  for (const rule of firedRules) {
    html += `      <li><strong>${rule.rule_id}</strong>: ${rule.threshold} - ${rule.why}</li>\n`;
  }
  
  html += '    </ul>\n';
  html += '  </div>\n';
  
  // Smallest fix
  html += '  <div class="smallest-fix">\n';
  html += '    <h3>Smallest Fix</h3>\n';
  html += `    <p>${smallestFix.summary || ''}</p>\n`;
  
  if (smallestFix.action_id) {
    html += `    <button data-action-id="${smallestFix.action_id}">Apply Fix</button>\n`;
  }
  
  html += '  </div>\n';
  html += '</div>\n';
  
  return html;
}

