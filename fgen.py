"""NI PXIe-5433 (FGEN1) function generator controller using ni-hw-drivers (nifgen).

Provides FgenController, FgenConfig, and test-matrix helpers used by
both the interactive UI (main.py) and the CLI test harness
(test_scope_with_fgen.py).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import nifgen  # Provided by ni-hw-drivers
    _nifgen_import_error: Exception | None = None
except Exception as _e:  # pragma: no cover
    nifgen = None  # type: ignore[assignment]
    _nifgen_import_error = _e


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class FgenConfig:
    resource_name: str = "FGEN1"
    channel: str = "0"
    waveform: str = "SINE"      # SINE | SQUARE | TRIANGLE | RAMP_UP | RAMP_DOWN | DC
    frequency: float = 1_000.0  # Hz
    amplitude: float = 1.0      # V pk-pk
    dc_offset: float = 0.0      # V
    start_phase: float = 0.0    # degrees


# ---------------------------------------------------------------------------
# Expected-value helpers
# ---------------------------------------------------------------------------

def expected_rms(waveform: str, amplitude_pk_pk: float, dc_offset: float = 0.0) -> float:
    """Return theoretical RMS for a standard waveform.

    Parameters
    ----------
    waveform : str
        One of SINE, SQUARE, TRIANGLE, RAMP_UP, RAMP_DOWN, DC.
    amplitude_pk_pk : float
        Peak-to-peak amplitude in volts (as configured on the FGEN).
    dc_offset : float
        DC offset in volts.  RMS = sqrt(ac_rms² + dc_offset²).
    """
    w = waveform.upper()
    half = amplitude_pk_pp = amplitude_pk_pk / 2.0  # peak (half of pk-pk)

    if w == "SINE":
        ac_rms = half / math.sqrt(2.0)
    elif w == "SQUARE":
        ac_rms = half  # symmetric ±half square wave
    elif w in ("TRIANGLE", "RAMP_UP", "RAMP_DOWN"):
        ac_rms = half / math.sqrt(3.0)
    else:  # DC or unknown
        ac_rms = 0.0

    return math.sqrt(ac_rms ** 2 + dc_offset ** 2)


def expected_pk_pk(amplitude_pk_pk: float) -> float:
    """Pass-through for clarity in test assertions."""
    return amplitude_pk_pk


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class FgenController:
    """Drive a PXIe-5433 function generator with graceful simulation fallback."""

    _WAVEFORM_MAP: Dict[str, object] = {}  # populated lazily when nifgen loads

    def __init__(
        self,
        config: FgenConfig,
        loggers: Dict[str, logging.Logger],
        simulate: bool = False,
    ) -> None:
        self.config = config
        self.loggers = loggers
        self.simulate = simulate or nifgen is None
        self.session = None
        self.connected = False
        self.running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        if self.connected:
            return
        if self.simulate:
            self.connected = True
            self.loggers["status"].info(
                "FGEN connected in simulation mode (resource=%s).", self.config.resource_name
            )
            return
        try:
            self.session = nifgen.Session(resource_name=self.config.resource_name)
            self.connected = True
            self.loggers["status"].info("FGEN connected to %s.", self.config.resource_name)
        except Exception as exc:
            self.loggers["error"].exception("FGEN failed to connect to %s", self.config.resource_name)
            raise RuntimeError(f"FGEN connection failed: {exc}") from exc

    def disconnect(self) -> None:
        self.stop_output()
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                self.loggers["error"].exception("Error closing FGEN session")
        self.session = None
        self.connected = False
        self.loggers["status"].info("FGEN disconnected.")

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Optional[FgenConfig] = None) -> None:
        if config is not None:
            self.config = config
        if not self.connected:
            raise RuntimeError("FGEN is not connected.")

        if self.simulate:
            self.loggers["status"].info(
                "FGEN configured (sim): waveform=%s freq=%.2f Hz amp=%.4f Vpk-pk offset=%.4f V",
                self.config.waveform, self.config.frequency,
                self.config.amplitude, self.config.dc_offset,
            )
            return

        try:
            if not FgenController._WAVEFORM_MAP and nifgen is not None:
                FgenController._WAVEFORM_MAP = {
                    "SINE": nifgen.Waveform.SINE,
                    "SQUARE": nifgen.Waveform.SQUARE,
                    "TRIANGLE": nifgen.Waveform.TRIANGLE,
                    "RAMP_UP": nifgen.Waveform.RAMP_UP,
                    "RAMP_DOWN": nifgen.Waveform.RAMP_DOWN,
                    "DC": nifgen.Waveform.DC,
                }

            waveform = FgenController._WAVEFORM_MAP.get(
                self.config.waveform.upper(), nifgen.Waveform.SINE
            )
            self.session.output_mode = nifgen.OutputMode.FUNC
            self.session.channels[self.config.channel].configure_standard_waveform(
                waveform=waveform,
                amplitude=self.config.amplitude / 2.0,   # API expects peak; config stores pk-pk
                frequency=self.config.frequency,
                dc_offset=self.config.dc_offset / 2.0,   # API expects peak-referenced; config stores absolute V
                start_phase=self.config.start_phase,
            )
            self.loggers["status"].info(
                "FGEN configured: waveform=%s freq=%.2f Hz amp=%.4f Vpk-pk offset=%.4f V",
                self.config.waveform, self.config.frequency,
                self.config.amplitude, self.config.dc_offset,
            )
        except Exception as exc:
            self.loggers["error"].exception("FGEN configure failed")
            raise RuntimeError(f"FGEN configure failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Output control
    # ------------------------------------------------------------------

    def start_output(self) -> None:
        if not self.connected:
            raise RuntimeError("FGEN is not connected.")
        if self.running:
            return
        if self.simulate:
            self.running = True
            self.loggers["status"].info("FGEN output STARTED (simulation).")
            return
        try:
            self.session.initiate()
            self.running = True
            self.loggers["status"].info("FGEN output STARTED.")
        except Exception as exc:
            self.loggers["error"].exception("FGEN start_output failed")
            raise RuntimeError(f"FGEN start failed: {exc}") from exc

    def stop_output(self) -> None:
        if not self.running:
            return
        if self.simulate:
            self.running = False
            self.loggers["status"].info("FGEN output STOPPED (simulation).")
            return
        if self.session is not None:
            try:
                self.session.abort()
            except Exception:
                self.loggers["error"].exception("FGEN stop_output failed")
        self.running = False
        self.loggers["status"].info("FGEN output STOPPED.")


# ---------------------------------------------------------------------------
# Test matrix
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    label: str
    fgen_config: FgenConfig
    expected_rms_v: float
    expected_pk_pk_v: float
    tolerance: float = 0.15   # 15% relative tolerance


@dataclass
class TestResult:
    case: TestCase
    passed: bool
    measured_rms: float
    measured_pk_pk: float
    measured_mean: float
    error_message: str = ""

    @property
    def rms_error_pct(self) -> float:
        denom = max(self.case.expected_rms_v, 1e-9)
        return abs(self.measured_rms - self.case.expected_rms_v) / denom * 100.0

    @property
    def pk_pk_error_pct(self) -> float:
        denom = max(self.case.expected_pk_pk_v, 1e-9)
        return abs(self.measured_pk_pk - self.case.expected_pk_pk_v) / denom * 100.0


def build_test_matrix(
    fgen_resource: str = "FGEN1",
    fgen_channel: str = "0",
) -> List[TestCase]:
    """Return a comprehensive test matrix covering frequencies, amplitudes, and waveforms."""
    cases: List[TestCase] = []

    def _add(label: str, waveform: str, freq: float, amp: float, offset: float = 0.0) -> None:
        cases.append(TestCase(
            label=label,
            fgen_config=FgenConfig(
                resource_name=fgen_resource,
                channel=fgen_channel,
                waveform=waveform,
                frequency=freq,
                amplitude=amp,
                dc_offset=offset,
            ),
            expected_rms_v=expected_rms(waveform, amp, offset),
            expected_pk_pk_v=amp,
        ))

    # ── Sine – frequency sweep (2 Vpk-pk) ─────────────────────────────────
    _add("SINE  100 Hz   2.0 Vpk-pk",   "SINE",     100.0,        2.0)
    _add("SINE   1 kHz   2.0 Vpk-pk",   "SINE",   1_000.0,        2.0)
    _add("SINE  10 kHz   2.0 Vpk-pk",   "SINE",  10_000.0,        2.0)
    _add("SINE 100 kHz   2.0 Vpk-pk",   "SINE", 100_000.0,        2.0)
    _add("SINE   1 MHz   2.0 Vpk-pk",   "SINE", 1_000_000.0,      2.0)

    # ── Sine – amplitude sweep (1 kHz) ─────────────────────────────────────
    _add("SINE   1 kHz   0.5 Vpk-pk",   "SINE",   1_000.0,        0.5)
    _add("SINE   1 kHz   1.0 Vpk-pk",   "SINE",   1_000.0,        1.0)
    _add("SINE   1 kHz   4.0 Vpk-pk",   "SINE",   1_000.0,        4.0)

    # ── Waveform types (1 kHz, 2 Vpk-pk) ──────────────────────────────────
    _add("SQUARE   1 kHz  2.0 Vpk-pk",  "SQUARE",   1_000.0,      2.0)
    _add("TRIANGLE 1 kHz  2.0 Vpk-pk",  "TRIANGLE", 1_000.0,      2.0)
    _add("RAMP_UP  1 kHz  2.0 Vpk-pk",  "RAMP_UP",  1_000.0,      2.0)

    # ── DC offset (within PXIe-5433 hardware limit of ±500 mV) ───────────
    label = "SINE   1 kHz   2.0 Vpk-pk +0.4V offset"
    cases.append(TestCase(
        label=label,
        fgen_config=FgenConfig(
            resource_name=fgen_resource,
            channel=fgen_channel,
            waveform="SINE",
            frequency=1_000.0,
            amplitude=2.0,
            dc_offset=0.4,
        ),
        expected_rms_v=expected_rms("SINE", 2.0, 0.4),
        expected_pk_pk_v=2.0,
    ))

    return cases

