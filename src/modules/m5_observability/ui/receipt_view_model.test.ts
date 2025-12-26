import * as assert from 'assert';
import { toObsUiModel, ObsUiModel } from './receipt_view_model';

suite('Receipt View Model', () => {
  test('toObsUiModel maps receipt to UI model correctly', () => {
    const receipt = {
      decision: {
        outcome: "pass"
      },
      inputs: {
        telemetry_coverage_pct_before: 66.67,
        telemetry_coverage_pct_after: 100.0
      },
      actions: {
        snippet_inserted: true
      },
      policy_snapshot_id: "policy_v1"
    };
    
    const result = toObsUiModel(receipt);
    
    assert.strictEqual(result.outcome, "pass");
    assert.strictEqual(result.coverageBefore, 66.67);
    assert.strictEqual(result.coverageAfter, 100.0);
    assert.strictEqual(result.snippetInserted, true);
    assert.strictEqual(result.policySnapshotId, "policy_v1");
  });
  
  test('toObsUiModel throws error if decision.outcome missing', () => {
    const receipt = {
      inputs: {
        telemetry_coverage_pct_before: 66.67,
        telemetry_coverage_pct_after: 100.0
      },
      actions: {
        snippet_inserted: true
      },
      policy_snapshot_id: "policy_v1"
    };
    
    assert.throws(() => toObsUiModel(receipt), /Missing required field: decision.outcome/);
  });
  
  test('toObsUiModel throws error if coverage_before missing', () => {
    const receipt = {
      decision: {
        outcome: "pass"
      },
      inputs: {
        telemetry_coverage_pct_after: 100.0
      },
      actions: {
        snippet_inserted: true
      },
      policy_snapshot_id: "policy_v1"
    };
    
    assert.throws(() => toObsUiModel(receipt), /Missing required field: inputs.telemetry_coverage_pct_before/);
  });
  
  test('toObsUiModel throws error if coverage_after missing', () => {
    const receipt = {
      decision: {
        outcome: "pass"
      },
      inputs: {
        telemetry_coverage_pct_before: 66.67
      },
      actions: {
        snippet_inserted: true
      },
      policy_snapshot_id: "policy_v1"
    };
    
    assert.throws(() => toObsUiModel(receipt), /Missing required field: inputs.telemetry_coverage_pct_after/);
  });
  
  test('toObsUiModel throws error if snippet_inserted missing', () => {
    const receipt = {
      decision: {
        outcome: "pass"
      },
      inputs: {
        telemetry_coverage_pct_before: 66.67,
        telemetry_coverage_pct_after: 100.0
      },
      policy_snapshot_id: "policy_v1"
    };
    
    assert.throws(() => toObsUiModel(receipt), /Missing required field: actions.snippet_inserted/);
  });
  
  test('toObsUiModel throws error if policy_snapshot_id missing', () => {
    const receipt = {
      decision: {
        outcome: "pass"
      },
      inputs: {
        telemetry_coverage_pct_before: 66.67,
        telemetry_coverage_pct_after: 100.0
      },
      actions: {
        snippet_inserted: true
      }
    };
    
    assert.throws(() => toObsUiModel(receipt), /Missing required field: policy_snapshot_id/);
  });
});

