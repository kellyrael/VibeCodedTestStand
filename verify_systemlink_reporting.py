#!/usr/bin/env python
"""End-to-end verification of SystemLink reporting against the live server.

Runs the full test suite pipeline (setup → cases → summary → cleanup) with
all NI hardware mocked, reports to the real SystemLink server, and then
queries the Test Monitor and APM APIs to confirm every event was recorded.

Usage
-----
    python verify_systemlink_reporting.py
"""
from __future__ import annotations

import json
import ssl
import sys
import time
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
from urllib.request import Request, urlopen

# Import reporter at module level so .env is loaded before any env-var checks.
from system_link_reporter import SystemLinkReporter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
_failures: List[str] = []


def _check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  {OK}  {label}")
    else:
        print(f"  {FAIL}  {label}" + (f"  ({detail})" if detail else ""))
        _failures.append(label)


def _sl_get(path: str) -> Optional[Dict[str, Any]]:
    import os
    base = os.getenv("SYSTEMLINK_URL", "").rstrip("/")
    key = os.getenv("SYSTEMLINK_API_KEY", "")
    url = f"{base}{path}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(url, headers={"x-ni-api-key": key})
    try:
        with urlopen(req, timeout=10, context=ctx) as r:
            return json.loads(r.read())
    except Exception as exc:
        print(f"  [WARN] GET {path} failed: {exc}")
        return None


def _sl_post(path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    import os
    base = os.getenv("SYSTEMLINK_URL", "").rstrip("/")
    key = os.getenv("SYSTEMLINK_API_KEY", "")
    url = f"{base}{path}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"x-ni-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=10, context=ctx) as r:
            return json.loads(r.read())
    except Exception as exc:
        print(f"  [WARN] POST {path} failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Fake runtime construction
# ---------------------------------------------------------------------------

def _make_fake_case(label: str = "SINE 1kHz 2Vpp") -> SimpleNamespace:
    return SimpleNamespace(
        label=label,
        expected_rms_v=0.7071,
        expected_pk_pk_v=2.0,
        fgen_config=SimpleNamespace(
            waveform="SINE",
            frequency=1000.0,
            amplitude=2.0,
            dc_offset=0.0,
            resource_name="FGEN1",
            channel="0",
        ),
    )


def _make_fake_runtime(run_id: str, reporter) -> SimpleNamespace:
    import logging
    from pathlib import Path
    return SimpleNamespace(
        scope_resource="Scope1",
        fgen_resource="FGEN1",
        mode_tag="HARDWARE",
        log_dir=Path("."),
        test_log_path=Path("logs/test_results.log"),
        test_logger=logging.getLogger("fake"),
        loggers={},
        limits=SimpleNamespace(
            rms_tolerance=0.12, freq_tolerance=0.02,
            max_rms_error_pct=12.0, max_freq_error_pct=2.0,
        ),
        cases=[_make_fake_case()],
        run_id=run_id,
        systemlink_reporter=reporter,
        scope_ctrl=MagicMock(),
        fgen_ctrl=MagicMock(),
        separator="=" * 80,
    )


def _make_fake_execution(runtime) -> SimpleNamespace:
    from test_scope_with_fgen import CaseExecution, TestResult
    case = runtime.cases[0]
    result = TestResult(
        case=case, passed=True, measured_rms=0.705, measured_pk_pk=1.99,
        measured_mean=0.0, error_message="",
    )
    return CaseExecution(
        index=1, case=case, result=result,
        expected_rms_low=0.622, expected_rms_high=0.792,
        expected_frequency_hz=1000.0, measured_frequency_hz=999.5,
        frequency_low_limit_hz=980.0, frequency_high_limit_hz=1020.0,
        rms_error_pct=0.3, freq_error_pct=0.05,
        passed_rms=True, passed_freq=True, error_stage="",
    )


# ---------------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------------

def _run_live_verification() -> None:
    import os
    import test_scope_with_fgen as tswf

    from uuid import uuid4
    run_id = f"verify-{str(uuid4())[:8]}"

    reporter = SystemLinkReporter.from_environment()
    runtime = _make_fake_runtime(run_id, reporter)

    print(f"\n── Run ID: {run_id}")

    print("\n── Step 1: assets → in_use + test run → running ───────────────────")
    reporter.publish_asset_utilization("Scope1", "in_use", run_id, {"asset_type": "scope"})
    reporter.publish_asset_utilization("FGEN1",  "in_use", run_id, {"asset_type": "fgen"})
    tswf.emit_suite_header(runtime)

    print("\n── Step 2: case running → passed ───────────────────────────────────")
    execution = _make_fake_execution(runtime)
    reporter.publish_test_case_status(run_id, 1, "SINE 1kHz 2Vpp", "running")
    reporter.publish_test_case_status(run_id, 1, "SINE 1kHz 2Vpp", "passed", {"rms_error_pct": 0.3})

    print("\n── Step 3: test run → passed ────────────────────────────────────────")
    tswf.emit_suite_summary(runtime, [execution])

    print("\n── Step 4: assets → available ───────────────────────────────────────")
    reporter.publish_asset_utilization("Scope1", "available", run_id, {"asset_type": "scope"})
    reporter.publish_asset_utilization("FGEN1",  "available", run_id, {"asset_type": "fgen"})

    time.sleep(0.5)  # allow server to commit

    sl_result_id = reporter._result_ids.get(run_id)

    print("\n━━ Assertions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    _check("Reporter.enabled is True", reporter.enabled)
    _check("SystemLink result ID was returned", bool(sl_result_id), f"id={sl_result_id}")

    # -- Verify Test Monitor result --
    if sl_result_id:
        tm_data = _sl_get(f"/nitestmonitor/v2/results/{sl_result_id}")
        if tm_data:
            result_status = tm_data.get("status", {}).get("statusType", "")
            prog_name = tm_data.get("programName", "")
            props = tm_data.get("properties", {})
            _check("Test Monitor result exists", True)
            _check(
                "Result programName is FgenScopeTest",
                prog_name == "FgenScopeTest",
                f"got '{prog_name}'",
            )
            _check(
                "Result status is PASSED",
                result_status == "PASSED",
                f"got '{result_status}'",
            )
            _check(
                "Result properties contain runId",
                props.get("runId") == run_id,
                f"runId='{props.get('runId')}'",
            )
        else:
            _check("Test Monitor result exists", False, "could not retrieve result")

        # -- Verify steps --
        steps_data = _sl_post(
            "/nitestmonitor/v2/query-steps",
            {"resultIds": [sl_result_id]},
        )
        if steps_data:
            steps = steps_data.get("steps", [])
            _check("At least one step was created", len(steps) >= 1, f"got {len(steps)}")
            if steps:
                s = steps[0]
                step_status = s.get("status", {}).get("statusType", "")
                _check("Step status is PASSED", step_status == "PASSED", f"got '{step_status}'")
        else:
            _check("Steps were created", False, "could not query steps")

    # -- Verify APM asset properties --
    for asset_name, asset_uuid in [
        ("Scope1", "688779da-7fe5-497b-905a-5182144e94d2"),
        ("FGEN1",  "e4489d58-a2e2-4ea5-a3eb-ecbc21de4b96"),
    ]:
        apm_data = _sl_get(f"/niapm/v1/assets/{asset_uuid}")
        if apm_data:
            props = apm_data.get("properties", {})
            in_use_cleared = props.get("inUseByRunId", "NOTSET") == ""
            _check(
                f"{asset_name} APM inUseByRunId cleared after cleanup",
                in_use_cleared,
                f"inUseByRunId='{props.get('inUseByRunId', 'NOTSET')}'",
            )
        else:
            _check(f"{asset_name} APM asset reachable", False)

    if sl_result_id:
        print(f"\n  SystemLink Test Monitor result: https://localhost/nitestmonitor#/results/{sl_result_id}")


def main() -> int:
    import os
    print("SystemLink Live Reporting Verification")
    print("=" * 60)
    print(f"Server:  {os.getenv('SYSTEMLINK_URL', '(not set)')}")

    if not os.getenv("SYSTEMLINK_URL") or not os.getenv("SYSTEMLINK_API_KEY"):
        print("\nERROR: Set SYSTEMLINK_URL and SYSTEMLINK_API_KEY before running.")
        return 1

    _run_live_verification()

    if _failures:
        print(f"\n\033[91m{len(_failures)} assertion(s) FAILED:\033[0m")
        for f in _failures:
            print(f"  - {f}")
        return 1

    print(f"\n\033[92mAll assertions passed.\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




