#!/usr/bin/env python
"""Automated scope + FGEN test harness for PXIe-5162 / PXIe-5433."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from main import ScopeConfig, ScopeController, compute_stats, setup_loggers
from fgen import FgenConfig, FgenController, TestCase, TestResult, build_test_matrix
from system_link_reporter import SystemLinkReporter

SETTLE_S = 0.25
HW_TOL = 0.12
FREQ_TOL = 0.02


@dataclass
class SuiteLimits:
    rms_tolerance: float
    freq_tolerance: float = FREQ_TOL

    @property
    def max_rms_error_pct(self) -> float:
        return self.rms_tolerance * 100.0

    @property
    def max_freq_error_pct(self) -> float:
        return self.freq_tolerance * 100.0


@dataclass
class SuiteRuntime:
    scope_resource: str
    fgen_resource: str
    log_dir: Path
    loggers: Dict[str, logging.Logger]
    test_logger: logging.Logger
    test_log_path: Path
    scope_ctrl: ScopeController
    fgen_ctrl: FgenController
    cases: List[TestCase]
    limits: SuiteLimits
    mode_tag: str
    run_id: str
    systemlink_reporter: SystemLinkReporter
    separator: str = "=" * 80


@dataclass
class CaseExecution:
    index: int
    case: TestCase
    result: TestResult
    expected_rms_low: float
    expected_rms_high: float
    expected_frequency_hz: float
    measured_frequency_hz: float
    frequency_low_limit_hz: float
    frequency_high_limit_hz: float
    rms_error_pct: float
    freq_error_pct: float
    passed_rms: bool
    passed_freq: bool
    error_stage: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "index": self.index,
            "label": self.case.label,
            "waveform": self.case.fgen_config.waveform,
            "expected_rms_v": self.case.expected_rms_v,
            "measured_rms_v": self.result.measured_rms,
            "rms_low_limit_v": self.expected_rms_low,
            "rms_high_limit_v": self.expected_rms_high,
            "rms_error_pct": self.rms_error_pct,
            "expected_frequency_hz": self.expected_frequency_hz,
            "measured_frequency_hz": self.measured_frequency_hz,
            "frequency_low_limit_hz": self.frequency_low_limit_hz,
            "frequency_high_limit_hz": self.frequency_high_limit_hz,
            "frequency_error_pct": self.freq_error_pct,
            "measured_pk_pk_v": self.result.measured_pk_pk,
            "measured_mean_v": self.result.measured_mean,
            "passed_rms": self.passed_rms,
            "passed_frequency": self.passed_freq,
            "passed": self.result.passed,
            "error_stage": self.error_stage,
            "error_message": self.result.error_message,
        }


def _close_logger_handlers(logger: logging.Logger) -> None:
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass


def _make_test_logger(log_dir: Path) -> Tuple[logging.Logger, Path]:
    log_path = log_dir / "test_results.log"
    logger = logging.getLogger("scope_fgen_test")
    _close_logger_handlers(logger)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)
    return logger, log_path


def _measure_frequency(v_vals: np.ndarray, sample_rate: float) -> float:
    try:
        v_centered = v_vals - np.mean(v_vals)
        windowed = v_centered * np.hanning(len(v_centered))
        fft_vals = np.fft.fft(windowed)
        freqs = np.fft.fftfreq(len(fft_vals), 1.0 / sample_rate)
        positive_freqs = freqs[: len(freqs) // 2]
        positive_power = np.abs(fft_vals[: len(fft_vals) // 2])
        peak_idx = np.argmax(positive_power[1:]) + 1
        return abs(positive_freqs[peak_idx])
    except Exception:
        return 0.0


def resolve_suite_limits(
    rms_tolerance: Optional[float] = None,
    freq_tolerance: float = FREQ_TOL,
) -> SuiteLimits:
    return SuiteLimits(rms_tolerance=rms_tolerance if rms_tolerance is not None else HW_TOL, freq_tolerance=freq_tolerance)


def _build_scope_config(scope_resource: str) -> ScopeConfig:
    return ScopeConfig(
        resource_name=scope_resource,
        sample_rate=10_000_000.0,
        record_length=100_000,
        vertical_range=10.0,
        trigger_source="0",
        trigger_level=0.1,
        trigger_coupling="DC",
        timeout_s=10.0,
    )


def _case_rms_limits(case: TestCase, limits: SuiteLimits) -> Tuple[float, float]:
    return (
        case.expected_rms_v * (1.0 - limits.rms_tolerance),
        case.expected_rms_v * (1.0 + limits.rms_tolerance),
    )


def _case_frequency_limits(case: TestCase, limits: SuiteLimits) -> Tuple[float, float]:
    expected_freq = case.fgen_config.frequency
    return (
        expected_freq * (1.0 - limits.freq_tolerance),
        expected_freq * (1.0 + limits.freq_tolerance),
    )


def create_suite_runtime(
    scope_resource: str = "Scope1",
    fgen_resource: str = "FGEN1",
    log_dir: Path | None = None,
    rms_tolerance: Optional[float] = None,
    freq_tolerance: float = FREQ_TOL,
) -> SuiteRuntime:
    if log_dir is None:
        log_dir = _HERE / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    loggers, _paths = setup_loggers(log_dir)
    test_logger, test_log_path = _make_test_logger(log_dir)
    systemlink_reporter = SystemLinkReporter.from_environment(loggers.get("error"))
    run_id = str(uuid4())

    fgen_ctrl = FgenController(FgenConfig(resource_name=fgen_resource), loggers=loggers, simulate=False)
    fgen_ctrl.connect()
    scope_ctrl = ScopeController(_build_scope_config(scope_resource), loggers=loggers, simulate=False)
    scope_ctrl.connect()

    if fgen_ctrl.simulate or scope_ctrl.simulate:
        cleanup_suite_runtime(
            SuiteRuntime(
                scope_resource=scope_resource,
                fgen_resource=fgen_resource,
                log_dir=log_dir,
                loggers=loggers,
                test_logger=test_logger,
                test_log_path=test_log_path,
                scope_ctrl=scope_ctrl,
                fgen_ctrl=fgen_ctrl,
                cases=[],
                limits=SuiteLimits(rms_tolerance=HW_TOL, freq_tolerance=freq_tolerance),
                mode_tag="HARDWARE",
                run_id=run_id,
                systemlink_reporter=systemlink_reporter,
            )
        )
        import main as _main_mod
        import fgen as _fgen_mod

        reasons = []
        niscope_err = getattr(_main_mod, "_niscope_import_error", None)
        nifgen_err = getattr(_fgen_mod, "_nifgen_import_error", None)
        if niscope_err is not None:
            reasons.append(f"niscope import failed: {niscope_err}")
        if nifgen_err is not None:
            reasons.append(f"nifgen import failed: {nifgen_err}")
        if not reasons:
            reasons.append(
                "niscope or nifgen imported as None - verify NI-SCOPE and NI-FGEN system drivers are installed and resources Scope1/FGEN1 are reachable."
            )
        raise RuntimeError(
            "Hardware-only mode is enabled but driver initialisation fell back to simulation.\n" + "\n".join(reasons)
        )

    systemlink_reporter.publish_asset_utilization(
        asset_id=scope_resource,
        state="in_use",
        run_id=run_id,
        details={"asset_type": "scope"},
    )
    systemlink_reporter.publish_asset_utilization(
        asset_id=fgen_resource,
        state="in_use",
        run_id=run_id,
        details={"asset_type": "fgen"},
    )

    return SuiteRuntime(
        scope_resource=scope_resource,
        fgen_resource=fgen_resource,
        log_dir=log_dir,
        loggers=loggers,
        test_logger=test_logger,
        test_log_path=test_log_path,
        scope_ctrl=scope_ctrl,
        fgen_ctrl=fgen_ctrl,
        cases=build_test_matrix(fgen_resource=fgen_resource),
        limits=resolve_suite_limits(rms_tolerance, freq_tolerance),
        mode_tag="HARDWARE",
        run_id=run_id,
        systemlink_reporter=systemlink_reporter,
    )


def emit_suite_header(runtime: SuiteRuntime) -> None:
    hdr = (
        f"\n{runtime.separator}\n"
        f" PXIe-5433 ({runtime.fgen_resource}) -> PXIe-5162 ({runtime.scope_resource})  "
        f"Test Suite  [{runtime.mode_tag}]\n"
        f"{runtime.separator}\n"
        f" {'#':>3}  {'Label':<45}  {'ExpRMS':>8}  {'PassRange':>17}  {'MaxErr':>7}  {'MeasRMS':>8}  {'Err%':>6}  {'ExpFreq':>8}  {'MeasFreq':>8}  {'FreqErr%':>7}  Result\n"
        f" {'-'*3}  {'-'*45}  {'-'*8}  {'-'*17}  {'-'*7}  {'-'*8}  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*7}  {'-'*6}"
    )
    print(hdr)
    runtime.test_logger.info(
        "=== Test Suite START  mode=%s scope=%s fgen=%s ===",
        runtime.mode_tag,
        runtime.scope_resource,
        runtime.fgen_resource,
    )
    runtime.systemlink_reporter.publish_test_run_status(
        run_id=runtime.run_id,
        status="running",
        details={
            "mode": runtime.mode_tag,
            "scope_resource": runtime.scope_resource,
            "fgen_resource": runtime.fgen_resource,
            "case_count": len(runtime.cases),
        },
    )


def execute_test_case(
    runtime: SuiteRuntime,
    case: TestCase,
    index: int,
    limits: Optional[SuiteLimits] = None,
    emit_output: bool = True,
) -> CaseExecution:
    limits = limits or runtime.limits
    expected_low, expected_high = _case_rms_limits(case, limits)
    freq_low, freq_high = _case_frequency_limits(case, limits)

    peak_swing = case.fgen_config.amplitude / 2.0 + abs(case.fgen_config.dc_offset)
    runtime.scope_ctrl.config.vertical_range = max(2.0 * peak_swing * 1.3, 1.0)
    runtime.scope_ctrl.config.trigger_level = case.fgen_config.dc_offset + case.fgen_config.amplitude * 0.1

    measured_rms = 0.0
    measured_pk_pk = 0.0
    measured_mean = 0.0
    measured_freq = 0.0
    rms_err_pct = 0.0
    freq_err_pct = 0.0
    passed_rms = False
    passed_freq = False
    error_stage = ""
    error_message = ""

    runtime.systemlink_reporter.publish_test_case_status(
        run_id=runtime.run_id,
        case_index=index,
        case_label=case.label,
        status="running",
    )

    try:
        runtime.fgen_ctrl.configure(case.fgen_config)
        runtime.fgen_ctrl.start_output()
        time.sleep(SETTLE_S)

        _, v_vals = runtime.scope_ctrl.acquire()
        stats = compute_stats(v_vals)
        measured_rms = stats["rms"]
        measured_pk_pk = stats["pk_pk"]
        measured_mean = stats["mean"]
        measured_freq = _measure_frequency(np.array(v_vals), runtime.scope_ctrl.config.sample_rate)

        rms_err_pct = abs(measured_rms - case.expected_rms_v) / max(case.expected_rms_v, 1e-9) * 100.0
        freq_err_pct = (
            abs(measured_freq - case.fgen_config.frequency) / max(case.fgen_config.frequency, 1e-9) * 100.0
            if case.fgen_config.frequency > 0
            else 0.0
        )
        passed_rms = rms_err_pct / 100.0 <= limits.rms_tolerance
        passed_freq = freq_err_pct / 100.0 <= limits.freq_tolerance
    except Exception as exc:
        error_message = str(exc)
        error_stage = "FGEN" if "FGEN" in error_message.upper() else "ACQUIRE"
        runtime.test_logger.error("Case %02d [%s]: %s error: %s", index, case.label, error_stage or "TEST", exc)
    finally:
        try:
            runtime.fgen_ctrl.stop_output()
        except Exception:
            runtime.loggers["error"].exception("Failed to stop FGEN output for case %s", case.label)
        time.sleep(0.05)

    passed = passed_rms and passed_freq and not error_message
    result = TestResult(
        case=case,
        passed=passed,
        measured_rms=measured_rms,
        measured_pk_pk=measured_pk_pk,
        measured_mean=measured_mean,
        error_message=error_message,
    )
    execution = CaseExecution(
        index=index,
        case=case,
        result=result,
        expected_rms_low=expected_low,
        expected_rms_high=expected_high,
        expected_frequency_hz=case.fgen_config.frequency,
        measured_frequency_hz=measured_freq,
        frequency_low_limit_hz=freq_low,
        frequency_high_limit_hz=freq_high,
        rms_error_pct=rms_err_pct,
        freq_error_pct=freq_err_pct,
        passed_rms=passed_rms,
        passed_freq=passed_freq,
        error_stage=error_stage,
    )

    if emit_output:
        if error_message:
            print(
                f" {index:>3}  {case.label:<45}  {case.expected_rms_v:>8.4f}  "
                f"{expected_low:>8.4f}-{expected_high:<8.4f}  {limits.max_rms_error_pct:>6.1f}%  "
                f"{'N/A':>8}  {'N/A':>6}  {case.fgen_config.frequency:>8.1f}  {'N/A':>8}  {'N/A':>7}  "
                f"ERROR ({error_stage or 'TEST'})"
            )
        else:
            tag = "PASS" if passed else "FAIL"
            print(
                f" {index:>3}  {case.label:<45}  {case.expected_rms_v:>8.4f}  "
                f"{expected_low:>8.4f}-{expected_high:<8.4f}  {limits.max_rms_error_pct:>6.1f}%  "
                f"{measured_rms:>8.4f}  {rms_err_pct:>5.1f}%  {case.fgen_config.frequency:>8.1f}  "
                f"{measured_freq:>8.1f}  {freq_err_pct:>6.1f}%  {tag}"
            )

    runtime.test_logger.info(
        "Case %02d [%s]: expected_rms=%.4f range=[%.4f, %.4f] max_rms_err=%.1f%% "
        "meas_rms=%.4f rms_err=%.1f%% expected_freq=%.1f freq_range=[%.1f, %.1f] "
        "meas_freq=%.1f freq_err=%.1f%% pk_pk=%.4f mean=%.4f -> %s%s",
        index,
        case.label,
        case.expected_rms_v,
        expected_low,
        expected_high,
        limits.max_rms_error_pct,
        measured_rms,
        rms_err_pct,
        case.fgen_config.frequency,
        freq_low,
        freq_high,
        measured_freq,
        freq_err_pct,
        measured_pk_pk,
        measured_mean,
        "PASS" if passed else "FAIL",
        f" ({error_stage}: {error_message})" if error_message else "",
    )
    runtime.systemlink_reporter.publish_test_case_status(
        run_id=runtime.run_id,
        case_index=index,
        case_label=case.label,
        status="passed" if passed else "failed",
        details={
            "rms_error_pct": rms_err_pct,
            "freq_error_pct": freq_err_pct,
            "error_stage": error_stage,
            "error_message": error_message,
        },
    )
    return execution


def emit_suite_summary(
    runtime: SuiteRuntime,
    executions: List[CaseExecution],
    limits: Optional[SuiteLimits] = None,
) -> int:
    limits = limits or runtime.limits
    failures = sum(1 for execution in executions if not execution.result.passed)
    passed_n = sum(1 for execution in executions if execution.result.passed)
    total = len(executions)

    summary = (
        f"\n{runtime.separator}\n"
        f"  Result : {'ALL PASS' if failures == 0 else f'{failures} FAILURE(S)'}\n"
        f"  Passed : {passed_n} / {total}\n"
        f"  Mode   : {runtime.mode_tag}  (RMS tolerance +- {limits.rms_tolerance * 100:.0f}% | Freq tolerance +- {limits.freq_tolerance * 100:.0f}%)\n"
        f"  Log    : {runtime.test_log_path}\n"
        f"{runtime.separator}\n"
    )
    print(summary)
    runtime.test_logger.info("=== Test Suite COMPLETE  passed=%d/%d  failures=%d ===", passed_n, total, failures)
    runtime.systemlink_reporter.publish_test_run_status(
        run_id=runtime.run_id,
        status="passed" if failures == 0 else "failed",
        details={"passed_cases": passed_n, "failed_cases": failures, "total_cases": total},
    )
    return failures


def cleanup_suite_runtime(runtime: SuiteRuntime) -> None:
    try:
        runtime.fgen_ctrl.disconnect()
    finally:
        try:
            runtime.scope_ctrl.disconnect()
        finally:
            runtime.systemlink_reporter.publish_asset_utilization(
                asset_id=runtime.scope_resource,
                state="available",
                run_id=runtime.run_id,
                details={"asset_type": "scope"},
            )
            runtime.systemlink_reporter.publish_asset_utilization(
                asset_id=runtime.fgen_resource,
                state="available",
                run_id=runtime.run_id,
                details={"asset_type": "fgen"},
            )
            _close_logger_handlers(runtime.test_logger)
            for logger in runtime.loggers.values():
                _close_logger_handlers(logger)


def run_test_suite(
    scope_resource: str = "Scope1",
    fgen_resource: str = "FGEN1",
    log_dir: Path | None = None,
    rms_tolerance: Optional[float] = None,
    freq_tolerance: float = FREQ_TOL,
    **kwargs,
) -> int:
    runtime = create_suite_runtime(
        scope_resource=scope_resource,
        fgen_resource=fgen_resource,
        log_dir=log_dir,
        rms_tolerance=rms_tolerance,
        freq_tolerance=freq_tolerance,
    )
    executions: List[CaseExecution] = []
    try:
        emit_suite_header(runtime)
        for idx, case in enumerate(runtime.cases, start=1):
            executions.append(execute_test_case(runtime, case, idx))
        return emit_suite_summary(runtime, executions)
    finally:
        cleanup_suite_runtime(runtime)


def main() -> int:
    parser = argparse.ArgumentParser(description="NI PXIe-5433 / PXIe-5162 automated test harness")
    parser.add_argument("--scope", default="Scope1", metavar="RESOURCE", help="Scope resource name (default: Scope1)")
    parser.add_argument("--fgen", default="FGEN1", metavar="RESOURCE", help="FGEN resource name (default: FGEN1)")
    args = parser.parse_args()
    failures = run_test_suite(scope_resource=args.scope, fgen_resource=args.fgen)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

