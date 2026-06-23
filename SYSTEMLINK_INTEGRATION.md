# SystemLink Integration Guide

This project now supports publishing test results to **NI SystemLink TestMonitor** service.

## Prerequisites

- NI SystemLink service running on the network with TestMonitor enabled
- Python package installed: `pip install nisystemlink-clients>=2.20.0` (auto-installed via `requirements.txt`)

## Quick Start

### 1. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 2. Run Tests with SystemLink Publishing

```powershell
# Publish results to SystemLink (auto-discovers server via NI Discovery Service)
python test_scope_with_fgen.py --publish-to-systemlink

# With custom resources
python test_scope_with_fgen.py --scope MyScope --fgen MyFgen --publish-to-systemlink
```

### 3. View Results in SystemLink

Once published, results appear in the **NI SystemLink web interface** under:
- **TestMonitor** → **Results** section
- Filter by `program_name` = `"Scope/FGEN Validation - Scope1/FGEN1"` (or your resource names)

## What Gets Published

Each test suite publication includes:

**Result (Test Session)**
- Program name (test suite identifier)
- Overall pass/fail status
- Timestamp (UTC)
- Operator: "automated_test"
- System ID: "{scope_resource}_{fgen_resource}"
- Keywords: ["scope_fgen_validation"]
- Properties: scope/fgen resources, test type

**Steps (Individual Test Cases)**
- One step per test case (waveform generated + measurement acquired)
- Step name: Test case label (e.g., "SINE 100 Hz 2.0 Vpk-pk")
- Step status: PASSED / FAILED
- Measurements table:
  - **RMS**: measured vs. low/high limits (V RMS)
  - **Frequency**: measured vs. low/high limits (Hz)

## Graceful Degradation

If SystemLink is unavailable:
- Tests still run normally
- A warning is logged
- No errors — systemlink publishing is optional

## API Architecture

### `systemlink_reporter.py`

**Main Classes:**
- `SystemLinkReporter` — connects to TestMonitor, publishes results
- `create_reporter()` — factory function with fallback

**Methods:**
- `connect()` — establish connection to SystemLink
- `disconnect()` — close connection
- `publish_test_suite_result()` — convert CaseExecution objects into TestMonitor Result + Steps
- `close()` — alias for disconnect()

**Example:**

```python
from systemlink_reporter import create_reporter
import logging

logger = logging.getLogger("my_app")

# Create reporter (returns None if nisystemlink-clients unavailable)
reporter = create_reporter(logger=logger)

if reporter:
    reporter.connect()
    try:
        result_id = reporter.publish_test_suite_result(
            suite_name="My Test Suite",
            scope_resource="Scope1",
            fgen_resource="FGEN1",
            executions=[...],  # List[CaseExecution]
            passed=True,
        )
        print(f"Published result ID: {result_id}")
    finally:
        reporter.disconnect()
```

## Troubleshooting

### "Failed to connect to SystemLink TestMonitor"
- **Cause:** SystemLink server not reachable or TestMonitor service not running
- **Fix:** Verify SystemLink is installed and running; check network connectivity

### SSL Certificate Verification Error
- **Cause:** SystemLink uses self-signed or internally-signed HTTPS certificates
- **Fix:** The code automatically disables SSL verification for local SystemLink instances. See [SYSTEMLINK_SSL_FIX.md](./SYSTEMLINK_SSL_FIX.md) for details.
- **Alternative:** If you have valid CA certificates, set the environment variable:
  ```powershell
  $env:REQUESTS_CA_BUNDLE = "C:\path\to\ca-bundle.crt"
  ```

### "nisystemlink-clients not installed"
- **Cause:** Dependency not installed
- **Fix:** Run `pip install nisystemlink-clients` or install from `requirements.txt`

### Results not appearing in SystemLink web UI
- **Cause:** Wrong workspace or connectivity issue
- **Fix:** Check SystemLink logs for errors; verify TestMonitor service status

## API Reference

### StatusType Enum Values
- `PASSED` — test case passed
- `FAILED` — test case failed
- `RUNNING` — test case in progress
- `SKIPPED` — test case skipped
- `ERRORED` — test encountered an error
- Other: `WAITING`, `LOOPING`, `TERMINATED`, `TIMED_OUT`, `CUSTOM`, `DONE`

### Test Data Structure
Results are structured as:
```
Result (TestMonitor Result)
├── program_name: "Scope/FGEN Validation - Scope1/FGEN1"
├── status: PASSED | FAILED
├── started_at: datetime (UTC)
└── Step[] (one per test case)
    ├── name: "SINE 100 Hz 2.0 Vpk-pk"
    ├── step_type: "waveform_measurement"
    ├── status: PASSED | FAILED
    └── Measurement[] (RMS, Frequency)
        ├── name: "RMS"
        ├── measurement: "1.4142" (value)
        ├── LOW/HIGH limits
        ├── status: "PASSED"
        └── units: "V RMS"
```

## Integration Examples

### From the UI (main.py)

Future enhancement: Add SystemLink toggle to the Tkinter UI for easy result publishing.

### From TestStand

The teststand_sequence.py adapter can be extended to optionally publish to SystemLink:

```python
def run_main(handle: str, publish_to_systemlink: bool = False):
    # ... existing run_main logic ...
    if publish_to_systemlink:
        from systemlink_reporter import create_reporter
        reporter = create_reporter()
        if reporter:
            reporter.connect()
            reporter.publish_test_suite_result(...)
            reporter.disconnect()
```

## References

- [NI SystemLink Python Docs](https://python-docs.systemlink.io/)
- [SystemLink TestMonitor API](https://python-docs.systemlink.io/en/stable/api_reference/testmonitor.html)
- [nisystemlink-clients GitHub](https://github.com/ni/nisystemlink-clients-python)

