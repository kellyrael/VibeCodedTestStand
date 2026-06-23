---
name: ni-systemlink-testmonitor-reporting
description: >
  Implement and troubleshoot NI SystemLink TestMonitor publishing for Python test workflows.
  Use when users ask to publish test results/steps to SystemLink, fix TLS certificate trust,
  map pass/fail statuses, or debug nisystemlink-clients API model/version issues.
  Covers TestMonitorClient result/step creation, REQUESTS_CA_BUNDLE configuration,
  self-signed certificate handling, and robust response parsing for partial-success models.
argument-hint: "Describe the test workflow, SystemLink server setup, and the publish issue you want to solve"
user-invocable: true
---

# NI SystemLink TestMonitor Reporting Skill

## Trigger

Use this skill when the user asks to:
- publish Python test results into NI SystemLink TestMonitor
- create Result + Step hierarchies from test-case execution data
- troubleshoot TLS/SSL certificate failures with SystemLink HTTPS endpoints
- fix per-step status mismatches (suite PASS but step FAIL)
- handle `nisystemlink-clients` response/model differences across versions

Also trigger on keywords: SystemLink, TestMonitor, nisystemlink-clients, create_results, create_steps, REQUESTS_CA_BUNDLE, self-signed certificate, publish results, step status.

---

## Overview

SystemLink publishing typically has four moving parts:
1. **Connection** (`TestMonitorClient`) to the discovered or configured server
2. **Result creation** (`CreateResultRequest`) for the overall test run
3. **Step creation** (`CreateStepRequest`) for each individual test case
4. **TLS trust setup** so HTTPS requests can validate the server certificate chain

For Python workflows, keep publishing optional and non-blocking so test execution continues even if SystemLink is unavailable.

---

## Critical Rules

1. **Prefer trusted TLS over disable-verify workarounds.**
   - Use `REQUESTS_CA_BUNDLE` with a valid PEM CA bundle.
   - Prefer a root CA PEM over leaf/server cert PEM.

2. **Do not assume one fixed API response shape for `create_results()`.**
   - Some versions expose top-level `id`.
   - Newer versions return `CreateResultsPartialSuccess(results=[Result(...)])`.
   - Always parse both patterns defensively.

3. **Create step status from real per-case fields.**
   - If your case object exposes `passed_rms` and `passed_freq`, derive pass/fail from those.
   - Do not rely on nonexistent attributes (for example `execution.passed`) unless verified.

4. **Provide `step_id` when required by model validation.**
   - Some `CreateStepRequest` models require `step_id` explicitly.

5. **Ensure measurements map to correct fields and units.**
   - RMS from the measured RMS value, frequency from measured frequency.
   - Keep limits and status aligned with each measurement type.

6. **Keep publisher failures non-fatal to the test run.**
   - Log exceptions with enough context to diagnose quickly.

---

## Recommended Implementation Pattern

```python
# 1) Configure CA trust
# - honor REQUESTS_CA_BUNDLE if valid
# - otherwise choose known workspace cert path(s)

# 2) Connect
client = TestMonitorClient()

# 3) Create suite result
result_response = client.create_results([result_request])

# 4) Extract result_id robustly
# - try result_response.id
# - else result_response.results[0].id

# 5) Build step requests
# - include step_id when required
# - compute step status from verified case fields

# 6) Create steps
client.create_steps(step_requests)
```

---

## Troubleshooting Checklist

- TLS error `CERTIFICATE_VERIFY_FAILED`
  - Verify `REQUESTS_CA_BUNDLE` path exists and points to PEM
  - Verify root CA cert matches SystemLink issuer

- `CreateResultsPartialSuccess` has no attribute `id`
  - Parse `results[0].id` from response model

- `CreateStepRequest` validation error for missing `step_id`
  - Add generated `step_id` (for example UUID)

- Suite PASS but steps FAIL
  - Verify step status logic uses actual case pass fields

- Results appear but measurements look wrong
  - Recheck field mapping (RMS vs frequency source fields)

---

## References

- `references/systemlink-testmonitor-lessons-learned.md`
- `SYSTEMLINK_INTEGRATION.md`
- `LESSONS_LEARNED.md`

