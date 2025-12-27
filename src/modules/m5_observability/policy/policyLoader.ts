import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';

export interface PolicyConfig {
  'obs.required_signals': string[];
  'obs.min_telemetry_coverage_warn': number;
  'obs.min_telemetry_coverage_block': number;
  'obs.require_correlation_id': boolean;
  'obs.require_hw_timestamp': boolean;
  'obs.max_label_cardinality_warn': number;
  'obs.max_label_cardinality_block': number;
  'obs.disallow_dynamic_keys': boolean;
  'obs.sample_rate_default': number;
  'obs.generated_marker_comment': string;
  'obs.pii_rules'?: Array<{ rule_id: string; pattern: string }>;
  'gate_mode'?: string;
}

const DEFAULT_POLICY: PolicyConfig = {
  'obs.required_signals': ['latency_ms', 'status', 'error_code', 'request_id', 'trace_id', 'hw_ts_ms'],
  'obs.min_telemetry_coverage_warn': 0.8,
  'obs.min_telemetry_coverage_block': 0.6,
  'obs.require_correlation_id': true,
  'obs.require_hw_timestamp': true,
  'obs.max_label_cardinality_warn': 100,
  'obs.max_label_cardinality_block': 500,
  'obs.disallow_dynamic_keys': true,
  'obs.sample_rate_default': 1.0,
  'obs.generated_marker_comment': 'CC_OBS_SNIPPET',
  'obs.pii_rules': [
    { rule_id: 'PII-001', pattern: 'Authorization:\\s*Bearer\\s+\\S+' },
    { rule_id: 'PII-002', pattern: '[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}' },
    { rule_id: 'PII-003', pattern: '(?:token|api[_-]?key|secret)\\s*[:=]\\s*[\'"]?\\S+' }
  ],
  'gate_mode': 'Warn'
};

let cachedPolicy: PolicyConfig | null = null;
let cachedPolicyPath: string | null = null;

/**
 * Load observability policy from workspace.
 * Caches the policy for performance.
 */
export async function loadPolicy(workspaceRoot?: string): Promise<PolicyConfig> {
  const root = workspaceRoot || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
  const policyPath = path.join(root, 'policy_observability.json');
  
  // Return cached policy if path hasn't changed
  if (cachedPolicy && cachedPolicyPath === policyPath) {
    try {
      // Check if file was modified
      const stats = await fs.stat(policyPath);
      const mtime = stats.mtimeMs;
      // For now, always reload (could cache mtime for better performance)
      // In production, you might want to cache with mtime check
    } catch {
      // File doesn't exist, return cached default
      return cachedPolicy;
    }
  }
  
  try {
    const policyContent = await vscode.workspace.fs.readFile(vscode.Uri.file(policyPath));
    const policyData = JSON.parse(Buffer.from(policyContent).toString('utf-8'));
    const policy = policyData.policy || {};
    
    // Merge with defaults to ensure all keys are present
    const mergedPolicy: PolicyConfig = {
      ...DEFAULT_POLICY,
      ...policy,
      // Ensure required_signals is always an array
      'obs.required_signals': policy['obs.required_signals'] || DEFAULT_POLICY['obs.required_signals'],
      // Ensure pii_rules is merged properly
      'obs.pii_rules': policy['obs.pii_rules'] || DEFAULT_POLICY['obs.pii_rules']
    };
    
    cachedPolicy = mergedPolicy;
    cachedPolicyPath = policyPath;
    return mergedPolicy;
  } catch (error: any) {
    // Policy not found or invalid, use defaults
    if (cachedPolicy) {
      return cachedPolicy;
    }
    cachedPolicy = DEFAULT_POLICY;
    cachedPolicyPath = policyPath;
    return DEFAULT_POLICY;
  }
}

/**
 * Clear policy cache (useful for testing or when policy changes)
 */
export function clearPolicyCache(): void {
  cachedPolicy = null;
  cachedPolicyPath = null;
}

/**
 * Get required signals from policy
 */
export async function getRequiredSignals(workspaceRoot?: string): Promise<string[]> {
  const policy = await loadPolicy(workspaceRoot);
  return policy['obs.required_signals'];
}

/**
 * Get marker comment from policy
 */
export async function getMarkerComment(workspaceRoot?: string): Promise<string> {
  const policy = await loadPolicy(workspaceRoot);
  return policy['obs.generated_marker_comment'];
}

/**
 * Get coverage thresholds from policy
 */
export async function getCoverageThresholds(workspaceRoot?: string): Promise<{ warn: number; block: number }> {
  const policy = await loadPolicy(workspaceRoot);
  return {
    warn: policy['obs.min_telemetry_coverage_warn'] * 100, // Convert to percentage
    block: policy['obs.min_telemetry_coverage_block'] * 100
  };
}

