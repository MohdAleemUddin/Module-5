export type ObsUiModel = {
  outcome: string;
  coverageBefore: number;
  coverageAfter: number;
  snippetInserted: boolean;
  policySnapshotId: string;
};

export function toObsUiModel(receipt: any): ObsUiModel {
  if (!receipt.decision || typeof receipt.decision.outcome !== 'string') {
    throw new Error('Missing required field: decision.outcome');
  }
  
  if (!receipt.inputs || typeof receipt.inputs.telemetry_coverage_pct_before !== 'number') {
    throw new Error('Missing required field: inputs.telemetry_coverage_pct_before');
  }
  
  if (!receipt.inputs || typeof receipt.inputs.telemetry_coverage_pct_after !== 'number') {
    throw new Error('Missing required field: inputs.telemetry_coverage_pct_after');
  }
  
  if (!receipt.actions || typeof receipt.actions.snippet_inserted !== 'boolean') {
    throw new Error('Missing required field: actions.snippet_inserted');
  }
  
  if (typeof receipt.policy_snapshot_id !== 'string') {
    throw new Error('Missing required field: policy_snapshot_id');
  }
  
  return {
    outcome: receipt.decision.outcome,
    coverageBefore: receipt.inputs.telemetry_coverage_pct_before,
    coverageAfter: receipt.inputs.telemetry_coverage_pct_after,
    snippetInserted: receipt.actions.snippet_inserted,
    policySnapshotId: receipt.policy_snapshot_id
  };
}

