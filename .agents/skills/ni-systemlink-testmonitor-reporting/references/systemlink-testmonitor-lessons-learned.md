# SystemLink TestMonitor Lessons Learned (Project-Specific)

## Scope
This reference captures practical issues encountered while integrating `test_scope_with_fgen.py` with SystemLink TestMonitor.

## Issues and Fixes

### 1) TLS certificate trust
- **Issue:** HTTPS publish failed with self-signed chain verification errors.
- **Fix:** Export and trust the SystemLink root CA cert in PEM format.
- **Pattern:** Set `REQUESTS_CA_BUNDLE` or auto-discover `certs/systemlink-root-ca.pem`.

### 2) `create_results` response model drift
- **Issue:** Code expected `result_response.id`, but newer model returned `CreateResultsPartialSuccess(results=[...])`.
- **Fix:** Support both legacy and current response shapes.

### 3) `CreateStepRequest` requires `step_id`
- **Issue:** Pydantic validation failed for missing `step_id`.
- **Fix:** Generate a UUID step id per step.

### 4) Step statuses incorrectly failed
- **Issue:** Step status used nonexistent `execution.passed`, defaulting to false.
- **Fix:** Compute step pass/fail from explicit fields (`passed_rms` and `passed_freq`).

### 5) RMS measurement mapping bug
- **Issue:** RMS inclusion was gated by a frequency field check.
- **Fix:** Read RMS directly from `execution.result.measured_rms`.

## Validation Signals
- Publish success should show:
  - `Created TestMonitor Result ID: <id>`
  - `Created TestMonitor Steps: <count>`
- The suite result and step statuses should align with test-case outcomes.

## Guardrails
- Keep publishing optional and non-blocking.
- Log full exception context for publish failures.
- Avoid disabling SSL verification globally in production paths.

