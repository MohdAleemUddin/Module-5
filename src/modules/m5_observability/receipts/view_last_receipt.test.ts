import * as assert from 'assert';
import {
  parseLastJsonlLine,
  renderM5ReceiptSummary,
  viewLastM5Receipt
} from './view_last_receipt';

suite('view_last_receipt helpers', () => {
  test('parseLastJsonlLine handles empty and invalid', () => {
    assert.strictEqual(parseLastJsonlLine(''), null);
    assert.strictEqual(parseLastJsonlLine('\n\n'), null);
    assert.strictEqual(parseLastJsonlLine('not-json\n'), null);
  });

  test('parseLastJsonlLine picks last non-empty JSON line', () => {
    const a = JSON.stringify({ a: 1 });
    const b = JSON.stringify({ b: 2 });
    const content = `${a}\n${b}\n`;
    assert.deepStrictEqual(parseLastJsonlLine(content), { b: 2 });
  });

  test('renderM5ReceiptSummary formats full and missing fields', () => {
    const full = {
      decision: { outcome: 'pass' },
      inputs: { telemetry_coverage_pct: 85.5, signals_missing: ['a', 'b'] },
      policy_snapshot_id: 'snap-1'
    };
    const expectedFull =
      'outcome: pass\ncoverage: 85.5\nmissing: a,b\npolicy_snapshot_id: snap-1';
    assert.strictEqual(renderM5ReceiptSummary(full), expectedFull);

    const missingExpected =
      'outcome: -\ncoverage: -\nmissing: -\npolicy_snapshot_id: -';
    assert.strictEqual(renderM5ReceiptSummary({}), missingExpected);
  });

  test('viewLastM5Receipt reads last receipt and renders summary', async () => {
    const lines = [
      JSON.stringify({
        decision: { outcome: 'warn' },
        inputs: { telemetry_coverage_pct: 70, signals_missing: ['x'] },
        policy_snapshot_id: 'snap-0'
      }),
      JSON.stringify({
        decision: { outcome: 'pass' },
        inputs: { telemetry_coverage_pct: 90, signals_missing: [] },
        policy_snapshot_id: 'snap-1'
      })
    ].join('\n');

    const fakeRead = async () => lines;
    const result = await viewLastM5Receipt(fakeRead, 'dummy');

    assert.deepStrictEqual(result.receipt, {
      decision: { outcome: 'pass' },
      inputs: { telemetry_coverage_pct: 90, signals_missing: [] },
      policy_snapshot_id: 'snap-1'
    });

    const expectedSummary =
      'outcome: pass\ncoverage: 90\nmissing: \npolicy_snapshot_id: snap-1';
    assert.strictEqual(result.summary, expectedSummary);
  });
});


