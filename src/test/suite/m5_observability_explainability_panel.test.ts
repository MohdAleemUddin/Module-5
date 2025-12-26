import assert from 'assert';
import { renderExplainabilitySection } from '../../modules/m5_observability/ui/explainabilitySection';

suite('M5 Explainability Panel Section', () => {
  test('renders fired rules and smallest fix correctly', () => {
    const receiptJsonText = JSON.stringify({
      decision: {
        outcome: "hard_block",
        rationale: "OBS: HARD [missing_critical=request_id,trace_id; pii=0]",
        explainability: {
          fired_rules: [
            {
              rule_id: "OBS-EXPL-0001",
              threshold: "require_correlation_id=true,require_hw_timestamp=false",
              why: "Missing critical signals: request_id,trace_id"
            },
            {
              rule_id: "OBS-EXPL-0008",
              threshold: "require_signals=optional",
              why: "Missing 1 optional signal(s): signal1"
            }
          ],
          smallest_fix: {
            type: "snippet",
            action_id: "zeroui.m5.insertObsSnippet",
            summary: "Add required observability signals"
          }
        }
      }
    });

    const html = renderExplainabilitySection(receiptJsonText);

    // Assert fired rules are present
    assert(html.includes('OBS-EXPL-0001'), 'Should contain first rule_id');
    assert(html.includes('OBS-EXPL-0008'), 'Should contain second rule_id');
    assert(html.includes('require_correlation_id=true,require_hw_timestamp=false'), 'Should contain first threshold');
    assert(html.includes('require_signals=optional'), 'Should contain second threshold');
    assert(html.includes('Missing critical signals: request_id,trace_id'), 'Should contain first why');
    assert(html.includes('Missing 1 optional signal(s): signal1'), 'Should contain second why');

    // Assert smallest fix
    assert(html.includes('Add required observability signals'), 'Should contain summary');
    assert(html.includes('data-action-id="zeroui.m5.insertObsSnippet"'), 'Should contain action_id marker');
  });

  test('deterministic output: same input produces identical HTML', () => {
    const receiptJsonText = JSON.stringify({
      decision: {
        outcome: "warn",
        rationale: "OBS: WARN [coverage=75.0; missing=-]",
        explainability: {
          fired_rules: [
            {
              rule_id: "OBS-EXPL-0002",
              threshold: "min_cov_warn=80.0",
              why: "Coverage 75.00% below warn threshold 80.0%"
            }
          ],
          smallest_fix: {
            type: "snippet",
            action_id: "zeroui.m5.insertObsSnippet",
            summary: "Add required observability signals"
          }
        }
      }
    });

    const html1 = renderExplainabilitySection(receiptJsonText);
    const html2 = renderExplainabilitySection(receiptJsonText);

    assert.strictEqual(html1, html2, 'Same input should produce identical HTML');
  });
});

