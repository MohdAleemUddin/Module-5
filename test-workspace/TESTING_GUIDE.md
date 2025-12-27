# Module 5 Extension - Complete Testing Guide

## Quick Start

1. **Open Workspace**: Open `test-workspace` folder in VS Code
2. **Activate Extension**: The Module 5 extension should activate automatically
3. **Check Status Bar**: Look for the "OBS" pill in the bottom-right status bar
4. **Open Decision Panel**: Press `Ctrl+Shift+P` → "Open M5 Decision Panel"

## Test Scenarios

### Scenario 1: Basic Diagnostics (F1.1)

**Steps**:
1. Open `src/handlers/orders.ts`
2. Save the file (`Ctrl+S`)
3. Check Problems panel (`Ctrl+Shift+M`)

**Expected**:
- Error diagnostic: "Missing telemetry signals: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms. Coverage: 0.0%"
- Code: `CC-OB-0401` (HARD block)
- Status bar shows: `❌ OBS 0%`

**Verify**:
- [ ] Diagnostic appears immediately after save
- [ ] Coverage is 0%
- [ ] Severity is Error (red)
- [ ] Code matches CC-OB-0401

---

### Scenario 2: Partial Coverage (F1.4)

**Steps**:
1. Open `src/handlers/products.ts`
2. Save the file
3. Check Problems panel

**Expected**:
- Warning diagnostic: "Missing telemetry signals: latency_ms, error_code, request_id, trace_id, hw_ts_ms. Coverage: 16.7%"
- Code: `CC-OB-0201` (WARN)
- Status bar shows: `⚠️ OBS 0%` (minimum across all files)

**Verify**:
- [ ] Coverage is 16.7% (1 out of 6 signals)
- [ ] Severity is Warning (yellow)
- [ ] Status bar shows minimum (0% from other files)

---

### Scenario 3: Pass Case (F1.1)

**Steps**:
1. Open `src/handlers/complete.ts`
2. Save the file
3. Check Problems panel

**Expected**:
- Info diagnostic: "All required telemetry signals present"
- Code: `CC-OB-0101` (PASS)
- Coverage: 100%

**Verify**:
- [ ] Diagnostic is Info (blue)
- [ ] Coverage is 100%
- [ ] All 6 signals detected

---

### Scenario 4: Snippet Insertion (F2.1)

**Steps**:
1. Open `src/handlers/orders.ts`
2. Right-click in editor → "Insert Observability Snippet"
3. Check if snippet was inserted

**Expected**:
- Snippet inserted at end of file
- Contains `// <CC_OBS_SNIPPET>` marker
- Contains all required signals
- Success message: "Observability snippet inserted. Coverage: 0.0% → 83.3% (Δ+83.3%)"

**Verify**:
- [ ] Snippet appears at end of file
- [ ] Contains marker comments
- [ ] Contains: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
- [ ] Delta message shows coverage improvement
- [ ] Try again → should be idempotent (no duplicate)

---

### Scenario 5: Metrics Snippet (F2.2)

**Steps**:
1. Open any file
2. Right-click → "Insert Metrics Snippet"

**Expected**:
- Snippet with sample_rate, labels, counter/histogram/timer comments
- Contains `CC_OBS_SNIPPET` marker

**Verify**:
- [ ] Snippet includes sample_rate from policy
- [ ] Labels are safe (no dynamic keys)
- [ ] Idempotent (no duplicate on second try)

---

### Scenario 6: Correlation Injection (F2.3)

**Steps**:
1. Open `src/handlers/orders.ts`
2. Right-click → "Inject Correlation IDs"

**Expected**:
- Helper function added for request_id/trace_id
- Contains `CC_OBS_SNIPPET` marker

**Verify**:
- [ ] Helper function added
- [ ] Idempotent (won't add if already exists)

---

### Scenario 7: PII Redaction (F1.2, F3.4)

**Steps**:
1. Open `src/handlers/payments.ts`
2. Right-click → "Redact PII/Secrets"
3. Check file after redaction

**Expected**:
- `apiKey` → `h:<sha256_hash>`
- `userEmail` → `h:<sha256_hash>`
- `authToken` → `h:<sha256_hash>`
- Success message: "Applied 3 redactions"
- Receipt entry in `receipts_m5.jsonl`

**Verify**:
- [ ] All PII/secrets replaced with hashes
- [ ] Original values not visible
- [ ] Receipt shows `pc1_attested: true`
- [ ] Mapping file created for reverse lookup

---

### Scenario 8: Dynamic Key Detection (F1.3, F3.3)

**Steps**:
1. Open `src/handlers/metrics.ts`
2. Save the file
3. Check Problems panel

**Expected**:
- Error: "Dynamic keys detected: labels[user.${userId}], ... Use static keys instead."
- Code: `CC-OB-0401` (HARD block)

**Verify**:
- [ ] Dynamic key pattern detected
- [ ] Diagnostic shows specific dynamic keys found
- [ ] Severity is Error

---

### Scenario 9: Decision Panel (F4.1, F5.2)

**Steps**:
1. Open multiple test files and save them
2. Press `Ctrl+Shift+P` → "Open M5 Decision Panel"
3. Review the panel

**Expected**:
- Status card showing overall outcome (PASS/WARN/SOFT/HARD)
- Coverage bar with minimum and average
- File-by-file breakdown
- Missing signals summary
- Last smoke test receipt (if run)

**Verify**:
- [ ] Status card color matches outcome
- [ ] Minimum coverage shown (weakest file)
- [ ] Average coverage shown
- [ ] File cards show individual coverage
- [ ] Missing signals listed as badges

---

### Scenario 10: Smoke Tests (F7.1)

**Steps**:
1. Press `Ctrl+Shift+P` → "Run Observability Smoke Tests"
2. Wait for completion
3. Check Decision Panel for receipt
4. Or check `receipts_m5.jsonl` in extension storage

**Expected Receipt Fields**:
```json
{
  "module": "M5_observability_v1",
  "gate_id": "observability_v1",
  "decision": {
    "outcome": "hard_block|warn|pass",
    "rationale": "OBS: ...",
    "explainability": {
      "fired_rules": [...],
      "smallest_fix": {...}
    }
  },
  "actor": {"type": "human", "id": "vscode-user", "client": "vscode"},
  "inputs": {
    "files_touched": ["src/handlers/orders.ts", ...],
    "signals_present": ["status", ...],
    "signals_missing": ["latency_ms", ...],
    "telemetry_coverage_pct": 18.5,
    "pii_findings": [],
    "cardinality_findings": []
  },
  "actions": {
    "snippet_inserted": false,
    "redactions_applied": [],
    "notes": []
  },
  "execution_mode": "normal",
  "policy_snapshot_id": "PB-...",
  "pc1_attested": false,
  "pc1": {"authoriser_gate": "ok", "rate_limiter": "ok", "dual_channel": "ok"},
  "timestamps": {"hw_monotonic_ms": 0, "hw_clock_khz": 1},
  "signature": {
    "algo": "stub-sha256",
    "value": "<64-char-hex-hash>"
  },
  "roi_tags": []
}
```

**Verify**:
- [ ] All required fields present
- [ ] `gate_id` is "observability_v1" (not "observability_smoke_v1")
- [ ] `signature.value` is actual hash (not "stub")
- [ ] `inputs.files_touched` contains test files
- [ ] `decision.explainability` shows fired rules
- [ ] Receipt is valid JSONL (one line)

---

### Scenario 11: Coverage Delta (F4.2)

**Steps**:
1. Open `src/handlers/orders.ts` (0% coverage)
2. Insert observability snippet
3. Check success message

**Expected**:
- Message: "Observability snippet inserted. Coverage: 0.0% → 83.3% (Δ+83.3%)"
- Delta tracked in snapshots

**Verify**:
- [ ] Before coverage captured
- [ ] After coverage calculated
- [ ] Delta shown in message
- [ ] ROI tags generated if delta > 0

---

### Scenario 12: Explainability (F5.2)

**Steps**:
1. Run smoke tests
2. Open Decision Panel
3. Scroll to "Last Smoke Test Receipt" section
4. Check explainability section

**Expected**:
- Fired rules list with:
  - Rule ID (OBS-EXPL-0001, OBS-EXPL-0002, etc.)
  - Threshold
  - Why it fired
- Smallest fix suggestion

**Verify**:
- [ ] Fired rules shown
- [ ] Thresholds match policy
- [ ] "Why" messages are clear
- [ ] Smallest fix suggests action

---

### Scenario 13: PC-1 Integration (F6.2)

**Steps**:
1. Open Developer Tools (`Help` → `Toggle Developer Tools`)
2. Open Console tab
3. Insert a snippet or redact PII
4. Check console for PC-1 logs

**Expected**:
- Console shows PC-1 check being called
- Receipt shows `pc1_attested: true` after write

**Verify**:
- [ ] PC-1 wrapper called before writes
- [ ] Receipt includes PC-1 attestation
- [ ] No writes without PC-1 check

---

### Scenario 14: Policy-Driven PII Rules (F1.2)

**Steps**:
1. Edit `policy_observability.json`
2. Add/modify `obs.pii_rules`
3. Run PII redaction on `payments.ts`
4. Verify new rules are used

**Expected**:
- PII rules loaded from policy
- Redaction uses policy rules (not hardcoded)

**Verify**:
- [ ] Rules loaded from policy
- [ ] Custom rules work
- [ ] Falls back to defaults if policy missing

---

### Scenario 15: Status Bar Updates (F4.1)

**Steps**:
1. Open multiple files with different coverage
2. Watch status bar (OBS pill)
3. Save files one by one

**Expected**:
- Status bar updates dynamically
- Shows minimum coverage (not average)
- Color changes: green (pass), yellow (warn), red (error)

**Verify**:
- [ ] Updates on file save
- [ ] Shows minimum coverage
- [ ] Color matches outcome
- [ ] Click opens Decision Panel

---

## Advanced Testing

### Test Idempotency
1. Insert snippet → verify inserted
2. Insert again → should be noop (no duplicate)
3. Check file → only one snippet block

### Test Coverage Calculation
1. Open `src/utils/helpers.ts`
2. Check diagnostics → should show mixed results
3. Verify coverage is calculated per file, not per function

### Test Receipt Signing
1. Run smoke tests
2. Check receipt `signature.value`
3. Verify it's 64-char hex (not "stub")
4. Modify receipt → signature should be invalid

### Test Explainability Rules
1. Create file with only critical signals missing → should fire OBS-EXPL-0001
2. Create file with coverage < warn threshold → should fire OBS-EXPL-0002
3. Create file with coverage < block threshold → should fire OBS-EXPL-0003

## Troubleshooting

### Diagnostics Not Appearing
- Check file extension (only code files are checked)
- Ensure file is saved
- Check Problems panel filter
- Verify extension is activated

### Snippets Not Inserting
- Check Python is installed and in PATH
- Check console for errors
- Verify policy file exists
- Check PC-1 logs (should allow in dev mode)

### Receipts Not Generated
- Check extension storage path
- Verify smoke tests completed successfully
- Check console for Python errors
- Ensure policy file is valid JSON

### Coverage Stuck at 0% or 100%
- Clear diagnostics: `Ctrl+Shift+P` → "Clear All Diagnostics"
- Re-save files
- Check that signals are in code (not comments/strings)

## Success Criteria

All features should work:
- ✅ Diagnostics appear on save
- ✅ Coverage calculated correctly
- ✅ Snippets insert with PC-1
- ✅ PII redaction works
- ✅ Dynamic keys detected
- ✅ Smoke tests generate complete receipts
- ✅ Decision Panel shows all data
- ✅ Explainability displays correctly
- ✅ Delta tracking works
- ✅ Status bar updates dynamically

