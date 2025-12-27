# Quick Start - Module 5 Extension Testing

## 1. Open Workspace
```
File → Open Folder → Select: test-workspace
```

## 2. Verify Extension
- Check status bar (bottom-right) for "OBS" pill
- Should show coverage percentage

## 3. Test Basic Features

### Test Diagnostics
1. Open `src/handlers/orders.ts`
2. Press `Ctrl+S` to save
3. Check Problems panel (`Ctrl+Shift+M`)
4. Should see: "Missing telemetry signals..." with 0% coverage

### Test Snippet Insertion
1. Right-click in `orders.ts` editor
2. Select "Insert Observability Snippet"
3. Verify snippet added at end of file
4. Check success message for coverage delta

### Test PII Redaction
1. Open `src/handlers/payments.ts`
2. Right-click → "Redact PII/Secrets"
3. Verify secrets replaced with hashes

### Test Smoke Tests
1. Press `Ctrl+Shift+P`
2. Type: "Run Observability Smoke Tests"
3. Wait for completion
4. Check Decision Panel for results

### Test Decision Panel
1. Press `Ctrl+Shift+P`
2. Type: "Open M5 Decision Panel"
3. Review coverage, files, and explainability

## Expected Results

- **Status Bar**: Shows minimum coverage (0% from orders.ts)
- **Problems Panel**: Shows diagnostics for each file
- **Decision Panel**: Shows file breakdown and coverage bars
- **Receipts**: Complete with all Module 5 fields

## Test Files Summary

| File | Coverage | Outcome | Purpose |
|------|----------|---------|---------|
| `orders.ts` | 0% | HARD | Missing all signals |
| `products.ts` | 16.7% | WARN | Missing 5 signals |
| `payments.ts` | 0% | HARD | PII/secrets present |
| `metrics.ts` | 0% | HARD | Dynamic keys |
| `complete.ts` | 100% | PASS | All signals present |
| `partial.ts` | 50% | HARD | Missing critical signals |
| `routes.ts` | 0% | HARD | Endpoint definitions |
| `cleanup.ts` | 0% | HARD | Background job |
| `helpers.ts` | Mixed | Mixed | Helper functions |

## All Features Testable

✅ F1: Telemetry Gap Detection  
✅ F2: Snippet Generation  
✅ F3: Schema & Policy Validation  
✅ F4: Coverage & Visualization  
✅ F5: Gates & Explainability  
✅ F6: PC-1 Trusted Actuation  
✅ F7: Evidence & Receipts  
✅ F8: Cross-Module Integration  

See `TESTING_GUIDE.md` for detailed test scenarios.

