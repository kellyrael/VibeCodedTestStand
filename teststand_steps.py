"""TestStand Python Adapter — parameter-driven step entry points.

Each NumericLimitTest step in the sequence passes the waveform type,
frequency, amplitude, and (optionally) DC offset directly as step
parameters.  This makes every measurement fully configurable from
the TestStand sequence editor without touching Python code.

Entry points
------------
initialize_devices   -- Setup group  (Action)
measure_rms          -- Main group   (NumericLimitTest, returns V RMS)
measure_frequency    -- Main group   (NumericLimitTest, returns Hz)
disconnect_devices   -- Cleanup group (Action)
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from main import ScopeConfig, ScopeController, compute_stats, setup_loggers
from fgen import FgenConfig, FgenController
from test_scope_with_fgen import (
    SETTLE_S,
    HW_TOL,
    FREQ_TOL,
    _build_scope_config,
    _measure_frequency,
    _close_logger_handlers,
)

# ---------------------------------------------------------------------------
# Module-level shared state (one session across all steps in an execution)
# ---------------------------------------------------------------------------

_scope_ctrl: Optional[ScopeController] = None
_fgen_ctrl: Optional[FgenController] = None
_loggers: Optional[Dict] = None
_log_dir: Optional[Path] = None

# Cache the last acquisition so measure_frequency can reuse it when called
# immediately after measure_rms for the same parameters.
_last_acquisition: Dict[str, Any] = {}


def _require_controllers() -> Tuple[ScopeController, FgenController]:
    if _scope_ctrl is None or _fgen_ctrl is None:
        raise RuntimeError(
            "Devices are not initialised. "
            "The 'Initialize Devices' Setup step must run before any measurement."
        )
    return _scope_ctrl, _fgen_ctrl


def _acquisition_key(
    waveform: str,
    frequency_hz: float,
    amplitude_vpp: float,
    dc_offset_v: float,
) -> tuple:
    return (waveform.upper(), float(frequency_hz), float(amplitude_vpp), float(dc_offset_v))


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def initialize_devices(
    scope_resource: str = "Scope1",
    fgen_resource: str = "FGEN1",
    log_dir: str = "",
    *args: Any,
    **kwargs: Any,
) -> int:
    """Connect to the PXIe-5162 scope and PXIe-5433 FGEN.

    Hardware-only: raises immediately if either driver is unavailable.
    """
    global _scope_ctrl, _fgen_ctrl, _loggers, _log_dir

    if "simulate" in kwargs:
        raise ValueError(
            "Simulation is disabled for TestStand. Use hardware resources only."
        )

    resolved_log_dir = Path(log_dir) if log_dir else Path(__file__).resolve().parent / "logs"
    resolved_log_dir.mkdir(parents=True, exist_ok=True)

    loggers, _ = setup_loggers(resolved_log_dir)

    fgen = FgenController(
        FgenConfig(resource_name=fgen_resource),
        loggers=loggers,
        simulate=False,
    )
    fgen.connect()

    scope = ScopeController(
        _build_scope_config(scope_resource),
        loggers=loggers,
        simulate=False,
    )
    scope.connect()

    # Fail fast if either controller fell back to simulation
    if fgen.simulate or scope.simulate:
        try:
            fgen.disconnect()
        except Exception:
            pass
        try:
            scope.disconnect()
        except Exception:
            pass
        import main as _main_mod
        import fgen as _fgen_mod
        reasons = []
        niscope_err = getattr(_main_mod, "_niscope_import_error", None)
        nifgen_err  = getattr(_fgen_mod,  "_nifgen_import_error",  None)
        if niscope_err:
            reasons.append(f"niscope import failed: {niscope_err}")
        if nifgen_err:
            reasons.append(f"nifgen import failed: {nifgen_err}")
        if not reasons:
            reasons.append(
                "niscope or nifgen is None — verify NI-SCOPE and NI-FGEN "
                "drivers are installed and resources are reachable."
            )
        raise RuntimeError(
            "Hardware-only mode is enabled but driver initialisation fell back to simulation.\n"
            + "\n".join(reasons)
        )

    _scope_ctrl = scope
    _fgen_ctrl  = fgen
    _loggers    = loggers
    _log_dir    = resolved_log_dir
    _last_acquisition.clear()
    return 1


# ---------------------------------------------------------------------------
# Per-step measurement helpers
# ---------------------------------------------------------------------------

def _run_acquisition(
    waveform: str,
    frequency_hz: float,
    amplitude_vpp: float,
    dc_offset_v: float,
) -> Dict[str, Any]:
    """Configure the FGEN, acquire from the scope, return stats + raw samples."""
    scope, fgen = _require_controllers()
    key = _acquisition_key(waveform, frequency_hz, amplitude_vpp, dc_offset_v)

    # Return cached result if the same parameters were just measured.
    if _last_acquisition.get("key") == key:
        return _last_acquisition

    cfg = FgenConfig(
        resource_name=fgen.config.resource_name,
        channel="0",
        waveform=waveform.upper(),
        frequency=float(frequency_hz),
        amplitude=float(amplitude_vpp),
        dc_offset=float(dc_offset_v),
    )

    # Tune scope vertical range and trigger level to the signal.
    peak_swing = cfg.amplitude / 2.0 + abs(cfg.dc_offset)
    scope.config.vertical_range = max(2.0 * peak_swing * 1.3, 1.0)
    scope.config.trigger_level  = cfg.dc_offset + cfg.amplitude * 0.1

    try:
        fgen.configure(cfg)
        fgen.start_output()
        time.sleep(SETTLE_S)

        _, v_vals = scope.acquire()
        stats = compute_stats(v_vals)
        meas_freq = _measure_frequency(np.array(v_vals), scope.config.sample_rate)
    finally:
        try:
            fgen.stop_output()
        except Exception:
            pass
        time.sleep(0.05)

    result = {
        "key":       key,
        "rms":       stats["rms"],
        "pk_pk":     stats["pk_pk"],
        "mean":      stats["mean"],
        "frequency": meas_freq,
    }
    _last_acquisition.clear()
    _last_acquisition.update(result)
    return result


# ---------------------------------------------------------------------------
# Main step entry points
# ---------------------------------------------------------------------------

def measure_rms(
    waveform: str = "SINE",
    frequency_hz: float = 1000.0,
    amplitude_vpp: float = 2.0,
    dc_offset_v: float = 0.0,
    *args: Any,
    **kwargs: Any,
) -> float:
    """Drive the FGEN with the given parameters, acquire from the scope,
    and return the measured RMS voltage.

    The NumericLimitTest step applies the low/high limits configured in
    the sequence.
    """
    result = _run_acquisition(waveform, frequency_hz, amplitude_vpp, dc_offset_v)
    return float(result["rms"])


def measure_frequency(
    waveform: str = "SINE",
    frequency_hz: float = 1000.0,
    amplitude_vpp: float = 2.0,
    dc_offset_v: float = 0.0,
    *args: Any,
    **kwargs: Any,
) -> float:
    """Return the measured frequency for the given parameters.

    If measure_rms was just called with the same parameters, reuses the
    cached acquisition rather than driving the FGEN again.
    """
    result = _run_acquisition(waveform, frequency_hz, amplitude_vpp, dc_offset_v)
    return float(result["frequency"])


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def disconnect_devices(*args: Any, **kwargs: Any) -> int:
    """Disconnect the scope and FGEN and release all resources."""
    global _scope_ctrl, _fgen_ctrl, _loggers

    if _fgen_ctrl is not None:
        try:
            _fgen_ctrl.disconnect()
        except Exception:
            pass

    if _scope_ctrl is not None:
        try:
            _scope_ctrl.disconnect()
        except Exception:
            pass

    if _loggers is not None:
        for logger in _loggers.values():
            _close_logger_handlers(logger)

    _scope_ctrl = None
    _fgen_ctrl  = None
    _loggers    = None
    _last_acquisition.clear()
    return 1

