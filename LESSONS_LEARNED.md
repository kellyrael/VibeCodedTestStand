# Lessons Learned: SystemLink Integration for Scope/FGEN Validation

Date: 2026-06-11
Project: `PythonProject3`
Primary scripts: `test_scope_with_fgen.py`, `systemlink_reporter.py`

## Objective
Integrate SystemLink TestMonitor publishing into the Scope/FGEN validation workflow without breaking existing test execution.

## What Worked Well
- Optional publishing behind `--publish-to-systemlink` preserved existing test behavior.
- Graceful failure handling prevented publish issues from blocking hardware tests.
- End-to-end publishing now works with automatic CA bundle discovery from workspace certs.
- Result and step creation is now compatible with newer `nisystemlink-clients` response/model shapes.

## Key Issues Encountered and Resolutions

### 1) TLS/Certificate validation blocked publishing
- Symptom: `SSLCertVerificationError` when posting to `/nitestmonitor/v2/results`.
- Root cause: SystemLink used a self-signed chain; Python requests did not trust it.
- Resolution:
  - Exported server/root certificates into `certs/`.
  - Verified that the root CA cert is the correct trust anchor.
  - Updated `systemlink_reporter.py` to auto-configure `REQUESTS_CA_BUNDLE` from:
    1. `certs/systemlink-root-ca.pem` (preferred)
    2. `certs/systemlink-server.pem` (fallback)

### 2) Version mismatch in API response shape
- Symptom: `'CreateResultsPartialSuccess' object has no attribute 'id'`.
- Root cause: Newer `nisystemlink-clients` returns `CreateResultsPartialSuccess(results=[...])` instead of top-level `id`.
- Resolution: Added response-shape-aware extraction of result ID (supports both legacy and current structures).

### 3) Step model validation failure
- Symptom: `CreateStepRequest` validation error requiring `step_id`.
- Root cause: Newer model requires `step_id`.
- Resolution: Added `step_id=str(uuid4())` when building each step.

### 4) Suite pass but steps fail in UI
- Symptom: overall result `PASSED`, individual steps `FAILED`.
- Root cause: step status used nonexistent `execution.passed` field; defaulted false.
- Resolution: Step status now computed from `CaseExecution` fields:
  - `passed_exec = passed_rms and passed_freq`

### 5) Measurement mapping bug
- Symptom: RMS measurement gating used frequency field and could produce incorrect/missing RMS data.
- Root cause: wrong attribute check in step measurement builder.
- Resolution: RMS now reads from `execution.result.measured_rms` directly and only when present.

## Final Verified State
- Test suite runs and publishes successfully to SystemLink.
- Log confirms:
  - result created
  - 12 steps created
- Auto cert configuration works without manual env var setup in normal runs.

## Practical Best Practices Going Forward
- Pin or test against specific `nisystemlink-clients` versions when possible.
- Code defensively around SDK response/model changes.
- Prefer trusted CA configuration over SSL-disable workarounds.
- Keep publishing optional and non-blocking for test execution reliability.
- Validate data mapping to UI semantics (suite status vs per-step status).

## Recommended Follow-Up Actions
1. Add a lightweight integration smoke test for `systemlink_reporter.py` (result + one step creation).
2. Document cert refresh process in case SystemLink certs are rotated.
3. Consider adding a startup log summary that prints selected CA bundle path and publish target.
4. Optionally add a CI check that validates reporter model compatibility for installed SDK version.

## Files Most Impacted
- `systemlink_reporter.py`
- `test_scope_with_fgen.py`
- `requirements.txt`
- `SYSTEMLINK_INTEGRATION.md`

