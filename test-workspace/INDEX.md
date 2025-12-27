# Test Workspace Index

## 📁 Files Overview

### Configuration Files
- **`policy_observability.json`** - Module 5 policy with all required keys and PII rules
- **`package.json`** - Node.js project configuration
- **`tsconfig.json`** - TypeScript compiler configuration
- **`.vscode/settings.json`** - VS Code workspace settings

### Documentation
- **`README.md`** - Overview, setup, and test file descriptions
- **`QUICK_START.md`** - Quick testing guide (start here!)
- **`TESTING_GUIDE.md`** - Detailed test scenarios for all features
- **`TEST_WORKSPACE_SUMMARY.md`** - Complete summary of test workspace
- **`INDEX.md`** - This file (navigation index)

### Test Code Files

#### Handlers (6 files)
1. **`src/handlers/orders.ts`** - Missing all signals (HARD block, 0%)
2. **`src/handlers/products.ts`** - Missing 5 signals (WARN, 16.7%)
3. **`src/handlers/payments.ts`** - PII/secrets + missing signals (HARD block, 0%)
4. **`src/handlers/metrics.ts`** - Dynamic keys + missing signals (HARD block, 0%)
5. **`src/handlers/complete.ts`** - All signals present (PASS, 100%)
6. **`src/handlers/partial.ts`** - Missing critical signals (HARD block, 50%)

#### API Routes (1 file)
7. **`src/api/routes.ts`** - Endpoint definitions (for endpoint discovery)

#### Background Jobs (1 file)
8. **`src/jobs/cleanup.ts`** - Background job (for job discovery)

#### Utilities (1 file)
9. **`src/utils/helpers.ts`** - Mixed coverage helper functions

## 🎯 Test Coverage by Feature

### F1: Telemetry Gap Detection
- ✅ Required-Signal Checker: All 9 test files
- ✅ PII/Secrets Detector: `payments.ts`
- ✅ Cardinality Bomb Detector: `metrics.ts`
- ✅ Coverage Calculator: All files

### F2: Snippet Generation
- ✅ Logging Snippet: Test with `orders.ts`
- ✅ Metrics Snippet: Test with any file
- ✅ Correlation Injector: Test with `orders.ts`

### F3: Schema & Policy Validation
- ✅ Dynamic-Key Blocker: `metrics.ts`
- ✅ PII Redaction: `payments.ts`

### F4: Golden-Signals Coverage & Viz
- ✅ Coverage Bar: Decision Panel
- ✅ Delta Reporter: Snippet insertion

### F5: Gates & Explainability
- ✅ Outcome Engine: Smoke tests
- ✅ Explainability Panel: Receipts

### F7: Evidence & Receipts
- ✅ Receipt Writer: Smoke tests
- ✅ Privacy-Safe Export: Receipt structure

## 🚀 Quick Start

1. **Open Workspace**: `File → Open Folder → test-workspace`
2. **Check Status Bar**: Look for "OBS" pill (bottom-right)
3. **Open a Test File**: Try `src/handlers/orders.ts`
4. **Save File**: Press `Ctrl+S`
5. **Check Problems**: Press `Ctrl+Shift+M`
6. **Open Decision Panel**: `Ctrl+Shift+P` → "Open M5 Decision Panel"

## 📋 Test Checklist

### Basic Functionality
- [ ] Diagnostics appear on file save
- [ ] Status bar shows coverage
- [ ] Decision Panel opens and displays data
- [ ] Problems panel shows correct diagnostics

### Snippet Features
- [ ] Insert observability snippet works
- [ ] Insert metrics snippet works
- [ ] Inject correlation IDs works
- [ ] Snippets are idempotent (no duplicates)

### Advanced Features
- [ ] PII redaction replaces secrets with hashes
- [ ] Dynamic keys detected in diagnostics
- [ ] Smoke tests generate complete receipts
- [ ] Receipts have all required fields
- [ ] Explainability shows in Decision Panel
- [ ] Coverage delta shown in messages

## 📊 Expected Results

| File | Signals Present | Coverage | Outcome | Diagnostic Code |
|------|----------------|----------|---------|---------------------|
| orders.ts | 0/6 | 0% | HARD | CC-OB-0401 |
| products.ts | 1/6 | 16.7% | WARN | CC-OB-0201 |
| payments.ts | 0/6 | 0% | HARD | CC-OB-0401 |
| metrics.ts | 0/6 | 0% | HARD | CC-OB-0401 |
| complete.ts | 6/6 | 100% | PASS | CC-OB-0101 |
| partial.ts | 3/6 | 50% | HARD | CC-OB-0401 |
| routes.ts | 0/6 | 0% | HARD | CC-OB-0401 |
| cleanup.ts | 0/6 | 0% | HARD | CC-OB-0401 |
| helpers.ts | Mixed | Mixed | Mixed | Mixed |

**Overall Minimum Coverage**: 0%  
**Overall Average Coverage**: ~18.5%

## 🔍 Feature Testing Order

1. **Start**: Open `QUICK_START.md` for basic tests
2. **Basic**: Test diagnostics with `orders.ts` and `products.ts`
3. **Snippets**: Test snippet insertion with `orders.ts`
4. **PII**: Test PII redaction with `payments.ts`
5. **Advanced**: Test smoke tests and Decision Panel
6. **Complete**: Follow `TESTING_GUIDE.md` for all scenarios

## 📝 Notes

- All test files are TypeScript (`.ts`) to match extension's code file detection
- Policy file must be in root directory
- Receipts are stored in VS Code extension storage (not in workspace)
- Extension only checks code files (ignores config, docs, etc.)
- Comments and strings are stripped before signal detection
- Word boundaries prevent false positives

## ✅ Success Criteria

After testing, you should see:
- ✅ All 9 test files show diagnostics
- ✅ Status bar shows minimum coverage (0%)
- ✅ Decision Panel shows file breakdown
- ✅ Snippets insert correctly
- ✅ PII redaction works
- ✅ Smoke tests generate complete receipts
- ✅ All Module 5 features working

---

**Total Files**: 17  
**Test Code Files**: 9  
**Documentation Files**: 5  
**Config Files**: 3

