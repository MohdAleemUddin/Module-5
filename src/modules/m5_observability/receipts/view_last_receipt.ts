/**
 * Helpers to read and summarize the last M5 receipt from a JSONL file.
 * Pure utilities (no VS Code API usage) to ease unit testing.
 */

export function parseLastJsonlLine(content: string): any | null {
  if (!content) return null;
  const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length === 0) return null;
  const last = lines[lines.length - 1];
  try {
    return JSON.parse(last);
  } catch {
    return null;
  }
}

export function renderM5ReceiptSummary(r: any): string {
  const lines: string[] = [];
  
  // Module and Gate ID
  const module = r?.module ?? "-";
  const gateId = r?.gate_id ?? "-";
  lines.push(`module: ${module}`);
  lines.push(`gate_id: ${gateId}`);
  
  // Decision
  const outcome = r?.decision?.outcome ?? "-";
  const rationale = r?.decision?.rationale ?? "-";
  lines.push(`outcome: ${outcome}`);
  lines.push(`rationale: ${rationale}`);
  
  // Coverage and Signals
  const coverageVal = r?.inputs?.telemetry_coverage_pct;
  const coverage = coverageVal != null ? (typeof coverageVal === 'number' ? coverageVal.toFixed(1) + '%' : String(coverageVal)) : "-";
  lines.push(`coverage: ${coverage}`);
  
  // Support both signals_missing (new) and missing_signals (old) for backward compatibility
  const missingVal = r?.inputs?.signals_missing ?? r?.inputs?.missing_signals;
  const missing = Array.isArray(missingVal) && missingVal.length > 0
    ? missingVal.join(",")
    : Array.isArray(missingVal) && missingVal.length === 0
      ? "none"
      : missingVal != null
        ? String(missingVal)
        : "-";
  lines.push(`missing: ${missing}`);
  
  // Signals present
  const signalsPresent = r?.inputs?.signals_present;
  if (Array.isArray(signalsPresent) && signalsPresent.length > 0) {
    lines.push(`signals_present: ${signalsPresent.join(",")}`);
  }
  
  // Files checked
  const checkedFiles = r?.inputs?.checked_files;
  if (checkedFiles != null && typeof checkedFiles === 'number') {
    lines.push(`checked_files: ${checkedFiles}`);
  }
  
  // Files touched
  const filesTouched = r?.inputs?.files_touched;
  if (Array.isArray(filesTouched) && filesTouched.length > 0) {
    lines.push(`files_touched: ${filesTouched.length} file(s)`);
    if (filesTouched.length <= 5) {
      lines.push(`  ${filesTouched.join(", ")}`);
    } else {
      lines.push(`  ${filesTouched.slice(0, 5).join(", ")}... (+${filesTouched.length - 5} more)`);
    }
  }
  
  // Actor
  const actor = r?.actor;
  if (actor) {
    const actorType = actor.type ?? "-";
    const actorId = actor.id ?? "-";
    const actorClient = actor.client ?? "-";
    lines.push(`actor: ${actorType} (${actorId}) [${actorClient}]`);
  }
  
  // Policy snapshot
  const policy = r?.policy_snapshot_id ?? "-";
  lines.push(`policy_snapshot_id: ${policy}`);
  
  // Timestamps
  const timestamps = r?.timestamps;
  if (timestamps?.hw_monotonic_ms != null) {
    lines.push(`hw_monotonic_ms: ${timestamps.hw_monotonic_ms}`);
  }
  
  // Signature
  const signature = r?.signature;
  if (signature?.algo) {
    lines.push(`signature: ${signature.algo} (${signature.value ? signature.value.substring(0, 16) + '...' : 'none'})`);
  }
  
  return lines.join('\n');
}

export async function viewLastM5Receipt(
  fsReadFile: (path: string) => Promise<string>,
  receiptPath: string
): Promise<{ summary: string; receipt: any | null }> {
  const content = await fsReadFile(receiptPath);
  const receipt = parseLastJsonlLine(content);
  const summary = renderM5ReceiptSummary(receipt ?? {});
  return { summary, receipt };
}


