# Module 5 Extension Test Workspace

This workspace contains test files to verify all Module 5 observability extension features.

## Setup

1. Open this folder (`test-workspace`) in VS Code
2. Ensure the Module 5 extension is installed and activated
3. The `policy_observability.json` file should be in the root

## Test Files

### 1. `src/handlers/orders.ts` - HARD BLOCK
- **Status**: Missing ALL required signals
- **Expected**: HARD block diagnostic (CC-OB-0401)
- **Coverage**: 0%
- **Test**: Open file, save, check Problems panel

### 2. `src/handlers/products.ts` - WARN
- **Status**: Missing 5 out of 6 signals (has `status`)
- **Expected**: WARN diagnostic (CC-OB-0201)
- **Coverage**: 16.7%
- **Test**: Open file, save, check Problems panel

### 3. `src/handlers/payments.ts` - PII/SECRETS
- **Status**: Contains PII/secrets + missing signals
- **Expected**: 
  - HARD block for missing signals
  - PII detection when running "Redact PII/Secrets" command
- **Test**: 
  - Open file, save (check diagnostics)
  - Right-click → "Redact PII/Secrets" (should redact: apiKey, userEmail, authToken)

### 4. `src/handlers/metrics.ts` - DYNAMIC KEYS
- **Status**: Contains dynamic keys + missing signals
- **Expected**: 
  - HARD block for dynamic keys (CC-OB-0401)
  - Message: "Dynamic keys detected: ..."
- **Test**: Open file, save, check Problems panel

### 5. `src/handlers/complete.ts` - PASS
- **Status**: Has ALL required signals
- **Expected**: PASS diagnostic (CC-OB-0101)
- **Coverage**: 100%
- **Test**: Open file, save, check Problems panel

### 6. `src/handlers/partial.ts` - SOFT BLOCK
- **Status**: Missing critical signals (request_id, trace_id, hw_ts_ms)
- **Expected**: HARD block (critical signals missing)
- **Coverage**: 50%
- **Test**: Open file, save, check Problems panel

### 7. `src/api/routes.ts` - ENDPOINT DISCOVERY
- **Status**: Missing signals, contains endpoint definitions
- **Expected**: Endpoints should be discovered in receipts
- **Test**: Run "Run Observability Smoke Tests", check receipt for `endpoints_touched`

### 8. `src/jobs/cleanup.ts` - JOB DISCOVERY
- **Status**: Missing signals, background job
- **Expected**: Jobs should be discovered in receipts
- **Test**: Run "Run Observability Smoke Tests", check receipt

### 9. `src/utils/helpers.ts` - MIXED COVERAGE
- **Status**: Mixed - some functions have signals, some don't
- **Expected**: Overall coverage calculated
- **Test**: Open file, save, check diagnostics

## Testing Features

### Feature 1: Telemetry Gap Detection
1. Open any test file
2. Save the file
3. Check Problems panel for diagnostics
4. Verify coverage percentage in status bar (OBS pill)
5. Open Decision Panel to see file-by-file breakdown

### Feature 2: Snippet Generation
1. Open `src/handlers/orders.ts` (missing all signals)
2. Right-click → "Insert Observability Snippet"
3. Verify snippet is inserted with `CC_OBS_SNIPPET` marker
4. Check coverage delta in success message
5. Try again (should be idempotent - no duplicate)

**Test Metrics Snippet**:
1. Open any file
2. Right-click → "Insert Metrics Snippet"
3. Verify snippet with sample_rate and labels

**Test Correlation Injection**:
1. Open `src/handlers/orders.ts`
2. Right-click → "Inject Correlation IDs"
3. Verify helper function is added

### Feature 3: PII/Secrets Detection & Redaction
1. Open `src/handlers/payments.ts`
2. Right-click → "Redact PII/Secrets"
3. Verify:
   - `apiKey` → `h:<hash>`
   - `userEmail` → `h:<hash>`
   - `authToken` → `h:<hash>`
4. Check receipt in `receipts_m5.jsonl` for redaction entry

### Feature 4: Dynamic Key Detection
1. Open `src/handlers/metrics.ts`
2. Save file
3. Check Problems panel for "Dynamic keys detected" error
4. Verify it's a HARD block (CC-OB-0401)

### Feature 5: Coverage Calculation
1. Open Decision Panel (Command: "Open M5 Decision Panel")
2. Verify:
   - Minimum coverage across all files
   - Average coverage
   - File-by-file breakdown
   - Missing signals summary

### Feature 6: Smoke Tests
1. Run Command: "Run Observability Smoke Tests"
2. Check receipt in `receipts_m5.jsonl`:
   - Verify all required fields present
   - Check `inputs.files_touched` contains test files
   - Check `inputs.signals_present` and `inputs.signals_missing`
   - Check `decision.outcome` and `decision.rationale`
   - Check `decision.explainability` (fired rules)
   - Check `pc1_attested` and `pc1` object
   - Check `signature.value` (should be actual hash, not "stub")

### Feature 7: Delta Tracking
1. Open `src/handlers/orders.ts`
2. Note current coverage (should be 0%)
3. Insert observability snippet
4. Check success message: "Coverage: 0.0% → 83.3% (Δ+83.3%)"
5. Verify ROI tags in receipt

### Feature 8: Explainability
1. Run smoke tests
2. Open Decision Panel
3. Scroll to "Last Smoke Test Receipt" section
4. Verify explainability shows:
   - Fired rules (OBS-EXPL-0001, OBS-EXPL-0002, etc.)
   - Thresholds
   - Why each rule fired
   - Smallest fix suggestion

## Expected Outcomes

### Diagnostics Summary:
- `orders.ts`: 0% coverage, HARD block
- `products.ts`: 16.7% coverage, WARN
- `payments.ts`: 0% coverage, HARD block (PII + missing signals)
- `metrics.ts`: 0% coverage, HARD block (dynamic keys)
- `complete.ts`: 100% coverage, PASS
- `partial.ts`: 50% coverage, HARD block (critical missing)
- `routes.ts`: 0% coverage, HARD block
- `cleanup.ts`: 0% coverage, HARD block
- `helpers.ts`: Mixed (functions analyzed separately)

### Minimum Coverage:
Should be **0%** (weakest file: orders.ts, payments.ts, metrics.ts, etc.)

### Average Coverage:
Should be approximately **18.5%** (weighted average across all files)

## Verification Checklist

- [ ] All files show correct diagnostics in Problems panel
- [ ] Status bar (OBS pill) shows minimum coverage
- [ ] Decision Panel shows file-by-file breakdown
- [ ] Snippet insertion works and is idempotent
- [ ] PII redaction works and creates receipt
- [ ] Dynamic key detection works
- [ ] Smoke tests generate complete receipts
- [ ] Receipts have all required fields
- [ ] Explainability shows in Decision Panel
- [ ] Delta tracking shows in snippet insertion messages
- [ ] PC-1 is called before all writes (check console logs)
- [ ] Coverage calculation uses minimum (not average) for overall status

## Notes

- The extension should only check code files (`.ts`, `.js`, `.py`, etc.), not config files
- Comments and strings are stripped before signal detection
- Word boundaries are used to avoid false positives
- Receipts are written to VS Code global storage (not in workspace)

