from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from test_scope_with_fgen import (
    CaseExecution,
    SuiteRuntime,
    cleanup_suite_runtime,
    create_suite_runtime,
    emit_suite_summary,
    execute_test_case,
    resolve_suite_limits,
)

_SEQUENCE_NAME = "ScopeFgenValidationSequence"
_ACTIVE_RUNTIMES: Dict[str, SuiteRuntime] = {}
_DEFAULT_HANDLE: Optional[str] = None
_LAST_CASE_RESULT: Dict[str, Any] = {}


def _require_handle(handle: str) -> SuiteRuntime:
    runtime = _ACTIVE_RUNTIMES.get(handle)
    if runtime is None:
        raise KeyError(f"Unknown or expired sequence handle: {handle}")
    return runtime


def _case_definition(index: int, execution_runtime: SuiteRuntime) -> Dict[str, Any]:
    case = execution_runtime.cases[index - 1]
    rms_low = case.expected_rms_v * (1.0 - execution_runtime.limits.rms_tolerance)
    rms_high = case.expected_rms_v * (1.0 + execution_runtime.limits.rms_tolerance)
    freq_low = case.fgen_config.frequency * (1.0 - execution_runtime.limits.freq_tolerance)
    freq_high = case.fgen_config.frequency * (1.0 + execution_runtime.limits.freq_tolerance)
    return {
        "index": index,
        "label": case.label,
        "waveform": case.fgen_config.waveform,
        "frequency_hz": case.fgen_config.frequency,
        "amplitude_vpp": case.fgen_config.amplitude,
        "dc_offset_v": case.fgen_config.dc_offset,
        "expected_rms_v": case.expected_rms_v,
        "expected_pk_pk_v": case.expected_pk_pk_v,
        "rms_low_limit_v": rms_low,
        "rms_high_limit_v": rms_high,
        "frequency_low_limit_hz": freq_low,
        "frequency_high_limit_hz": freq_high,
    }


def _serialize_execution(execution: CaseExecution) -> Dict[str, Any]:
    payload = execution.as_dict()
    payload["step_type"] = "NumericLimitTest"
    payload["rms_result"] = {
        "measurement": execution.result.measured_rms,
        "low_limit": execution.expected_rms_low,
        "high_limit": execution.expected_rms_high,
        "units": "V RMS",
        "passed": execution.passed_rms,
    }
    payload["frequency_result"] = {
        "measurement": execution.measured_frequency_hz,
        "low_limit": execution.frequency_low_limit_hz,
        "high_limit": execution.frequency_high_limit_hz,
        "units": "Hz",
        "passed": execution.passed_freq,
    }
    return payload


def _serialize_runtime(handle: str, runtime: SuiteRuntime) -> Dict[str, Any]:
    return {
        "sequence_name": _SEQUENCE_NAME,
        "handle": handle,
        "scope_resource": runtime.scope_resource,
        "fgen_resource": runtime.fgen_resource,
        "mode": runtime.mode_tag,
        "log_dir": str(runtime.log_dir),
        "test_log_path": str(runtime.test_log_path),
        "limits": {
            "rms_tolerance": runtime.limits.rms_tolerance,
            "freq_tolerance": runtime.limits.freq_tolerance,
            "max_rms_error_pct": runtime.limits.max_rms_error_pct,
            "max_freq_error_pct": runtime.limits.max_freq_error_pct,
        },
        "case_count": len(runtime.cases),
        "cases": [_case_definition(i, runtime) for i in range(1, len(runtime.cases) + 1)],
    }


def get_sequence_definition() -> Dict[str, Any]:
    return {
        "sequence_name": _SEQUENCE_NAME,
        "adapter": "Python",
        "description": "Setup initializes the scope and function generator once, Main runs each test case with limit checks, and Cleanup disconnects the devices.",
        "groups": {
            "Setup": [
                {
                    "name": "Initialize Devices",
                    "type": "Action",
                    "module": "teststand_sequence",
                    "function": "initialize_devices",
                    "stores_result_as": "FileGlobals.SequenceContext",
                }
            ],
            "Main": [
                {
                    "name": "Get Test Cases",
                    "type": "Action",
                    "module": "teststand_sequence",
                    "function": "get_test_cases",
                    "parameters": {
                        "handle": "FileGlobals.SequenceContext.handle",
                    },
                    "stores_result_as": "Locals.TestCases",
                },
                {
                    "name": "For Each Test Case",
                    "type": "ForEach",
                    "items": "Locals.TestCases",
                    "steps": [
                        {
                            "name": "Run Test Case",
                            "type": "Action",
                            "module": "teststand_sequence",
                            "function": "run_case",
                            "parameters": {
                                "handle": "FileGlobals.SequenceContext.handle",
                                "case_index": "Locals.LoopItem.index",
                            },
                            "stores_result_as": "Locals.StepResult",
                        },
                        {
                            "name": "RMS Limit",
                            "type": "NumericLimitTest",
                            "measurement": "Locals.StepResult.measured_rms_v",
                            "low_limit": "Locals.StepResult.rms_low_limit_v",
                            "high_limit": "Locals.StepResult.rms_high_limit_v",
                            "units": "V RMS",
                        },
                        {
                            "name": "Frequency Limit",
                            "type": "NumericLimitTest",
                            "measurement": "Locals.StepResult.measured_frequency_hz",
                            "low_limit": "Locals.StepResult.frequency_low_limit_hz",
                            "high_limit": "Locals.StepResult.frequency_high_limit_hz",
                            "units": "Hz",
                        },
                    ],
                },
            ],
            "Cleanup": [
                {
                    "name": "Disconnect Devices",
                    "type": "Action",
                    "module": "teststand_sequence",
                    "function": "disconnect_devices",
                }
            ],
        },
    }


def setup_sequence(
    scope_resource: str = "Scope1",
    fgen_resource: str = "FGEN1",
    log_dir: Optional[str] = None,
    rms_tolerance: Optional[float] = None,
    freq_tolerance: float = 0.02,
) -> Dict[str, Any]:
    runtime = create_suite_runtime(
        scope_resource=scope_resource,
        fgen_resource=fgen_resource,
        log_dir=Path(log_dir) if log_dir else None,
        rms_tolerance=rms_tolerance,
        freq_tolerance=freq_tolerance,
    )
    handle = str(uuid4())
    _ACTIVE_RUNTIMES[handle] = runtime
    return _serialize_runtime(handle, runtime)


def get_test_cases(handle: str) -> List[Dict[str, Any]]:
    runtime = _require_handle(handle)
    return [_case_definition(i, runtime) for i in range(1, len(runtime.cases) + 1)]


def run_case(
    handle: str,
    case_index: int,
    rms_tolerance: Optional[float] = None,
    freq_tolerance: Optional[float] = None,
) -> Dict[str, Any]:
    runtime = _require_handle(handle)
    if case_index < 1 or case_index > len(runtime.cases):
        raise IndexError(f"case_index must be in range 1..{len(runtime.cases)}")

    limits = runtime.limits
    if rms_tolerance is not None or freq_tolerance is not None:
        limits = resolve_suite_limits(
            rms_tolerance=rms_tolerance if rms_tolerance is not None else runtime.limits.rms_tolerance,
            freq_tolerance=freq_tolerance if freq_tolerance is not None else runtime.limits.freq_tolerance,
        )

    execution = execute_test_case(
        runtime,
        runtime.cases[case_index - 1],
        case_index,
        limits=limits,
        emit_output=False,
    )
    payload = _serialize_execution(execution)
    payload["handle"] = handle
    return payload


def run_main(
    handle: str,
    rms_tolerance: Optional[float] = None,
    freq_tolerance: Optional[float] = None,
) -> Dict[str, Any]:
    runtime = _require_handle(handle)
    limits = runtime.limits
    if rms_tolerance is not None or freq_tolerance is not None:
        limits = resolve_suite_limits(
            rms_tolerance=rms_tolerance if rms_tolerance is not None else runtime.limits.rms_tolerance,
            freq_tolerance=freq_tolerance if freq_tolerance is not None else runtime.limits.freq_tolerance,
        )

    executions: List[CaseExecution] = []
    for index, case in enumerate(runtime.cases, start=1):
        executions.append(execute_test_case(runtime, case, index, limits=limits, emit_output=False))

    failures = emit_suite_summary(runtime, executions, limits=limits)
    return {
        "sequence_name": _SEQUENCE_NAME,
        "handle": handle,
        "failures": failures,
        "passed": failures == 0,
        "case_count": len(executions),
        "results": [_serialize_execution(execution) for execution in executions],
    }


def cleanup_sequence(handle: str) -> Dict[str, Any]:
    runtime = _ACTIVE_RUNTIMES.pop(handle, None)
    if runtime is None:
        return {
            "handle": handle,
            "cleaned_up": False,
            "message": "Handle was already cleaned up or was never created.",
        }

    cleanup_suite_runtime(runtime)
    return {
        "handle": handle,
        "cleaned_up": True,
        "message": "Scope and FGEN disconnected.",
    }


def initialize_devices(*args: Any, **kwargs: Any) -> int:
    """TestStand setup step: initialize once and retain a default runtime handle."""
    global _DEFAULT_HANDLE
    if "simulate" in kwargs:
        raise ValueError("Simulation is disabled for TestStand. Use hardware resources only.")

    context = setup_sequence(*args, **kwargs)
    _DEFAULT_HANDLE = context["handle"]

    runtime = _require_handle(_DEFAULT_HANDLE)
    return 1


def run_case_rms(case_index: int, *args: Any, **kwargs: Any) -> float:
    """TestStand numeric step: execute case and return measured RMS for limits."""
    if _DEFAULT_HANDLE is None:
        raise RuntimeError("Devices are not initialized. Call initialize_devices first.")
    result = run_case(_DEFAULT_HANDLE, int(case_index), *args, **kwargs)
    _LAST_CASE_RESULT.clear()
    _LAST_CASE_RESULT.update(result)
    return float(result["measured_rms_v"])


def run_case_frequency(case_index: int, *args: Any, **kwargs: Any) -> float:
    """TestStand numeric step: return measured frequency for the same case index."""
    if _DEFAULT_HANDLE is None:
        raise RuntimeError("Devices are not initialized. Call initialize_devices first.")

    expected_index = int(case_index)
    if not _LAST_CASE_RESULT or int(_LAST_CASE_RESULT.get("index", -1)) != expected_index:
        result = run_case(_DEFAULT_HANDLE, expected_index, *args, **kwargs)
        _LAST_CASE_RESULT.clear()
        _LAST_CASE_RESULT.update(result)

    return float(_LAST_CASE_RESULT["measured_frequency_hz"])


def disconnect_devices(*args: Any, **kwargs: Any) -> int:
    """TestStand cleanup step: disconnect and clear module-level state."""
    global _DEFAULT_HANDLE
    if _DEFAULT_HANDLE is not None:
        cleanup_sequence(_DEFAULT_HANDLE)
    _DEFAULT_HANDLE = None
    _LAST_CASE_RESULT.clear()
    return 1


