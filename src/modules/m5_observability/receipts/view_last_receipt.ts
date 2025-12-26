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
  const outcome = r?.decision?.outcome ?? "-";
  const coverage = r?.inputs?.telemetry_coverage_pct ?? "-";
  const missingVal = r?.inputs?.signals_missing;
  const missing = Array.isArray(missingVal)
    ? missingVal.join(",")
    : missingVal != null
      ? String(missingVal)
      : "-";
  const policy = r?.policy_snapshot_id ?? "-";

  return `outcome: ${outcome}\ncoverage: ${coverage}\nmissing: ${missing}\npolicy_snapshot_id: ${policy}`;
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


