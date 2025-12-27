# Test Workspace Summary

## Structure

```
test-workspace/
├── policy_observability.json    # Module 5 policy configuration
├── package.json                  # Node.js project config
├── tsconfig.json                 # TypeScript config
├── README.md                     # Overview and setup
├── QUICK_START.md                # Quick testing guide
├── TESTING_GUIDE.md              # Detailed test scenarios
├── .vscode/
│   └── settings.json             # VS Code workspace settings
└── src/
    ├── handlers/
    │   ├── orders.ts            # 0% coverage, HARD block
    │   ├── products.ts          # 16.7% coverage, WARN
    │   ├── payments.ts          # 0% coverage, PII/secrets
    │   ├── metrics.ts           # 0% coverage, dynamic keys
    │   ├── complete.ts          # 100% coverage, PASS
    │   └── partial.ts           # 50% coverage, critical missing
    ├── api/
    │   └── routes.ts            # Endpoint definitions
    ├── jobs/
    │   └── cleanup.ts           # Background job
    └── utils/
        └── helpers.ts           # Mixed coverage helpers
```

## Test Coverage

### Feature Coverage:
- ✅ **F1.1**: Required-Signal Checker (all test files)
- ✅ **F1.2**: PII/Secrets Detector (`payments.ts`)
- ✅ **F1.3**: Cardinality Bomb Detector (`metrics.ts`)
- ✅ **F1.4**: Telemetry Coverage Calculator (all files)
- ✅ **F2.1**: Logging Snippet Generator (test insertion)
- ✅ **F2.2**: Metrics Snippet Generator (test insertion)
- ✅ **F2.3**: Correlation/Tracing Injector (test injection)
- ✅ **F3.3**: Dynamic-Key Blocker (`metrics.ts`)
- ✅ **F3.4**: PII Redaction Quick-Fix (`payments.ts`)
- ✅ **F4.1**: Coverage Bar (Decision Panel)
- ✅ **F4.2**: Before/After Delta Reporter (snippet insertion)
- ✅ **F5.1**: Outcome Engine (smoke tests)
- ✅ **F5.2**: Rule Explainability Panel (receipts)
- ✅ **F7.1**: Receipt Writer (smoke tests)
- ✅ **F7.2**: Privacy-Safe CI Artifacts (export)

## Test Scenarios

### Scenario A: HARD Block (Missing All Signals)
**File**: `src/handlers/orders.ts`
- Missing: All 6 required signals
- Expected: CC-OB-0401, 0% coverage, Error severity

### Scenario B: WARN (Partial Coverage)
**File**: `src/handlers/products.ts`
- Has: `status` (1/6 signals)
- Missing: 5 signals
- Expected: CC-OB-0201, 16.7% coverage, Warning severity

### Scenario C: PASS (Full Coverage)
**File**: `src/handlers/complete.ts`
- Has: All 6 required signals
- Expected: CC-OB-0101, 100% coverage, Info severity

### Scenario D: PII/Secrets Detection
**File**: `src/handlers/payments.ts`
- Contains: API key, email, token
- Expected: PII redaction replaces with hashes

### Scenario E: Dynamic Key Detection
**File**: `src/handlers/metrics.ts`
- Contains: `labels[user.${id}]`, `tags[${key}]`
- Expected: CC-OB-0401, "Dynamic keys detected" error

### Scenario F: Critical Signals Missing
**File**: `src/handlers/partial.ts`
- Has: `latency_ms`, `status`, `error_code`
- Missing: `request_id`, `trace_id`, `hw_ts_ms` (critical)
- Expected: CC-OB-0401, HARD block (critical missing)

### Scenario G: Endpoint Discovery
**File**: `src/api/routes.ts`
- Contains: `router.get()`, `router.post()`, `router.put()`
- Expected: Endpoints discovered in receipt `inputs.endpoints_touched`

### Scenario H: Job Discovery
**File**: `src/jobs/cleanup.ts`
- Contains: Background job functions
- Expected: Jobs discovered in receipt

### Scenario I: Mixed Coverage
**File**: `src/utils/helpers.ts`
- Contains: Functions with different signal coverage
- Expected: Overall coverage calculated per file

## Expected Outcomes

### Overall Coverage:
- **Minimum**: 0% (from orders.ts, payments.ts, metrics.ts, etc.)
- **Average**: ~18.5% (weighted across all files)

### Diagnostics Summary:
- **HARD Block**: 6 files (orders, payments, metrics, partial, routes, cleanup)
- **WARN**: 1 file (products)
- **PASS**: 1 file (complete)
- **Mixed**: 1 file (helpers)

### Receipt Fields (after smoke test):
```json
{
  "module": "M5_observability_v1",
  "gate_id": "observability_v1",
  "decision": {
    "outcome": "hard_block",
    "rationale": "OBS: HARD [missing_critical=request_id,trace_id,hw_ts_ms; pii=0]",
    "explainability": {
      "fired_rules": [
        {"rule_id": "OBS-EXPL-0001", "threshold": "...", "why": "..."},
        {"rule_id": "OBS-EXPL-0002", "threshold": "...", "why": "..."}
      ],
      "smallest_fix": {
        "type": "snippet",
        "action_id": "zeroui.m5.insertObsSnippet",
        "summary": "Add required observability signals"
      }
    }
  },
  "inputs": {
    "files_touched": [
      "src/handlers/orders.ts",
      "src/handlers/products.ts",
      "src/handlers/payments.ts",
      "src/handlers/metrics.ts",
      "src/handlers/complete.ts",
      "src/handlers/partial.ts",
      "src/api/routes.ts",
      "src/jobs/cleanup.ts",
      "src/utils/helpers.ts"
    ],
    "signals_present": ["status"],
    "signals_missing": ["latency_ms", "error_code", "request_id", "trace_id", "hw_ts_ms"],
    "telemetry_coverage_pct": 18.5
  }
}
```

## Quick Test Commands

1. **Open Decision Panel**: `Ctrl+Shift+P` → "Open M5 Decision Panel"
2. **Run Smoke Tests**: `Ctrl+Shift+P` → "Run Observability Smoke Tests"
3. **Insert Snippet**: Right-click → "Insert Observability Snippet"
4. **Redact PII**: Right-click → "Redact PII/Secrets"
5. **Inject Correlation**: Right-click → "Inject Correlation IDs"

## Verification Checklist

After opening the workspace and testing:

- [ ] Status bar shows OBS pill with coverage
- [ ] Problems panel shows diagnostics for each file
- [ ] Decision Panel opens and displays data
- [ ] Snippet insertion works
- [ ] PII redaction works
- [ ] Smoke tests generate receipts
- [ ] Receipts have all required fields
- [ ] Explainability shows in Decision Panel
- [ ] Coverage delta shown in snippet messages
- [ ] Dynamic keys detected
- [ ] PC-1 called before writes (check console)

## Notes

- All test files are TypeScript (`.ts`) to match extension's code file detection
- Policy file is in root directory (required by extension)
- Receipts are stored in VS Code extension storage (not in workspace)
- Extension only checks code files (ignores config, docs, etc.)

