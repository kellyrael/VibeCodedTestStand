import argparse
import logging
import math
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

try:
    import niscope  # Provided by ni-hw-drivers
    _niscope_import_error: Exception | None = None
except Exception as _e:  # pragma: no cover - fallback when drivers are not installed
    niscope = None  # type: ignore[assignment]
    _niscope_import_error = _e

try:
    import nisyscfg  # Optional helper for device discovery on NI driver installs
    _nisyscfg_import_error: Exception | None = None
except Exception as _e:  # pragma: no cover - optional dependency
    nisyscfg = None  # type: ignore[assignment]
    _nisyscfg_import_error = _e

try:
    from fgen import FgenConfig, FgenController  # sibling module
except Exception:  # pragma: no cover
    FgenConfig = None  # type: ignore[assignment,misc]
    FgenController = None  # type: ignore[assignment]


@dataclass
class ScopeConfig:
    resource_name: str = "Scope1"
    channel: str = "0"
    sample_rate: float = 10_000_000.0
    record_length: int = 10_000
    num_records: int = 1
    vertical_range: float = 5.0
    coupling: str = "DC"
    trigger_source: str = "0"
    trigger_level: float = 0.1
    trigger_coupling: str = "DC"   # DC | AC | HF_REJECT | LF_REJECT
    timeout_s: float = 5.0


@dataclass
class DeviceDetails:
    model: str = "—"
    serial: str = "—"
    bus_slot: str = "—"
    channel_count: str = "—"
    max_sample_rate: str = "—"
    firmware: str = "—"


def query_device_details(resource_name: str, simulate: bool = False) -> DeviceDetails:
    """Return device details for *resource_name*.

    Tries three strategies in order:
    1. nisyscfg hardware resource properties (no instrument open needed).
    2. niscope.Session attribute inspection (opens a temporary session).
    3. Simulated / placeholder values when drivers are unavailable.
    """
    details = DeviceDetails()

    if nisyscfg is not None:
        try:
            with nisyscfg.Session() as session:
                for hw in session.find_hardware():
                    alias = (
                        getattr(hw, "expert_user_alias", None)
                        or getattr(hw, "expert_name", None)
                        or getattr(hw, "resource_name", None)
                    )
                    if alias and str(alias).strip() == resource_name.strip():
                        details.model = str(getattr(hw, "product_name", "—")).strip() or "—"
                        details.serial = str(getattr(hw, "serial_number", "—")).strip() or "—"
                        chassis = getattr(hw, "chassis_number", None)
                        slot = getattr(hw, "slot_number", None)
                        if chassis is not None and slot is not None:
                            details.bus_slot = f"Chassis {chassis}, Slot {slot}"
                        elif slot is not None:
                            details.bus_slot = f"Slot {slot}"
                        details.firmware = str(getattr(hw, "firmware_revision", "—")).strip() or "—"
                        break
        except Exception:
            pass

    if niscope is not None:
        _sentinel = object()
        _SCOPE_ATTRS = {
            "model": "instrument_model",
            "serial": "serial_number",
            "channel_count": "channel_count",
            "max_sample_rate": "max_real_time_sampling_rate",
            "firmware": "firmware_revision",
        }

        def _read_session_attrs(sess: object) -> None:
            for field, attr in _SCOPE_ATTRS.items():
                val = getattr(sess, attr, _sentinel)
                if val is _sentinel:
                    continue
                str_val = str(val).strip()
                if not str_val or str_val == "None":
                    continue
                if field == "max_sample_rate":
                    try:
                        details.max_sample_rate = f"{float(str_val) / 1e9:.3f} GS/s"
                        continue
                    except ValueError:
                        pass
                if field == "channel_count":
                    details.channel_count = str_val
                elif field == "model" and details.model == "—":
                    details.model = str_val
                elif field == "serial" and details.serial == "—":
                    details.serial = str_val
                elif field == "firmware" and details.firmware == "—":
                    details.firmware = str_val

            pxi_chassis = getattr(sess, "pxi_chassis", None)
            slot = getattr(sess, "slot_number", None)
            bus = getattr(sess, "bus_number", None)
            if details.bus_slot == "—":
                if pxi_chassis is not None and slot is not None:
                    details.bus_slot = f"Chassis {pxi_chassis}, Slot {slot}"
                elif bus is not None and slot is not None:
                    details.bus_slot = f"Bus {bus}, Slot {slot}"
                elif slot is not None:
                    details.bus_slot = f"Slot {slot}"

        try:
            options = "Simulate=1, DriverSetup=Model:5162" if simulate else ""
            with niscope.Session(resource_name=resource_name, options=options) as sess:
                _read_session_attrs(sess)
        except Exception:
            pass

    if simulate and details.model == "—":
        details.model = "PXIe-5162 (Simulated)"
        details.serial = "SIM-000001"
        details.bus_slot = "Chassis 1, Slot 2"
        details.channel_count = "2"
        details.max_sample_rate = "5.000 GS/s"
        details.firmware = "Simulated"

    return details


def discover_scope_resources(preferred: str = "Scope1") -> List[str]:
    resources: List[str] = []

    def _add_candidates(raw: object) -> None:
        if raw is None:
            return
        if isinstance(raw, str):
            parts = [p.strip() for p in raw.replace(";", ",").split(",")]
            resources.extend([p for p in parts if p])
            return
        if isinstance(raw, (list, tuple, set)):
            for item in raw:
                if item is not None:
                    value = str(item).strip()
                    if value:
                        resources.append(value)

    if niscope is not None:
        for getter_name in ("get_device_names", "get_resource_names"):
            getter = getattr(niscope.Session, getter_name, None)
            if not callable(getter):
                continue
            try:
                _add_candidates(getter())
            except Exception:
                # Discovery APIs vary by driver version; ignore unsupported forms.
                pass

    if not resources and nisyscfg is not None:
        try:
            with nisyscfg.Session() as session:
                for resource in session.find_hardware():
                    product_name = str(getattr(resource, "product_name", "")).lower()
                    if not any(key in product_name for key in ("scope", "digitizer", "5162", "pxie")):
                        continue
                    candidate = (
                        getattr(resource, "expert_user_alias", None)
                        or getattr(resource, "expert_name", None)
                        or getattr(resource, "resource_name", None)
                    )
                    if candidate:
                        resources.append(str(candidate).strip())
        except Exception:
            pass

    unique: List[str] = []
    for resource_name in resources:
        if resource_name and resource_name not in unique:
            unique.append(resource_name)

    preferred = preferred.strip() if preferred else ""
    if preferred and preferred not in unique:
        unique.insert(0, preferred)
    if "Scope1" not in unique:
        unique.append("Scope1")
    return unique


def setup_loggers(log_dir: Path) -> Tuple[Dict[str, logging.Logger], Dict[str, Path]]:
    log_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "status": log_dir / "status.log",
        "error": log_dir / "error.log",
        "measurement": log_dir / "measurement.log",
    }

    def _make_logger(name: str, file_path: Path) -> logging.Logger:
        logger = logging.getLogger(name)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
        logger.setLevel(logging.INFO)
        logger.propagate = False
        handler = logging.FileHandler(file_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
        return logger

    loggers = {
        "status": _make_logger("scope_status", paths["status"]),
        "error": _make_logger("scope_error", paths["error"]),
        "measurement": _make_logger("scope_measurement", paths["measurement"]),
    }

    if paths["measurement"].stat().st_size == 0:
        loggers["measurement"].info("timestamp,resource,channel,samples,mean,rms,pk_pk,min,max")

    return loggers, paths


class ScopeController:
    def __init__(self, config: ScopeConfig, loggers: Dict[str, logging.Logger], simulate: bool = False):
        self.config = config
        self.loggers = loggers
        self.simulate = simulate or niscope is None
        self.session = None
        self.connected = False

        # Simulation waveform parameters — can be set externally to match an FGEN.
        self.sim_frequency: float = 20_000.0   # Hz
        self.sim_amplitude: float = 1.25       # peak (half of pk-pk)
        self.sim_waveform: str    = "SINE"
        self.sim_dc_offset: float = 0.0

    def connect(self) -> None:
        if self.connected:
            return

        if self.simulate:
            self.connected = True
            self.loggers["status"].info("Connected in simulation mode (resource=%s).", self.config.resource_name)
            return

        try:
            self.session = niscope.Session(resource_name=self.config.resource_name)
            self.connected = True
            self.loggers["status"].info("Connected to NI-SCOPE device: %s", self.config.resource_name)
        except Exception as exc:
            self.loggers["error"].exception("Failed to connect to %s", self.config.resource_name)
            raise RuntimeError(f"Connection failed: {exc}") from exc

    def disconnect(self) -> None:
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                self.loggers["error"].exception("Error while closing scope session")
        self.session = None
        self.connected = False
        self.loggers["status"].info("Disconnected from scope.")

    def acquire(self) -> Tuple[List[float], List[float]]:
        if not self.connected:
            raise RuntimeError("Scope is not connected.")

        if self.simulate:
            t_vals, v_vals = self._simulate_waveform()
        else:
            t_vals, v_vals = self._read_hw_waveform()

        stats = compute_stats(v_vals)
        self.loggers["measurement"].info(
            "%s,%s,%s,%d,%.6f,%.6f,%.6f,%.6f,%.6f",
            time.strftime("%Y-%m-%dT%H:%M:%S"),
            self.config.resource_name,
            self.config.channel,
            len(v_vals),
            stats["mean"],
            stats["rms"],
            stats["pk_pk"],
            stats["min"],
            stats["max"],
        )
        self.loggers["status"].info("Acquired %d samples.", len(v_vals))
        return t_vals, v_vals

    def _simulate_waveform(self) -> Tuple[List[float], List[float]]:
        dt = 1.0 / max(self.config.sample_rate, 1.0)
        t_vals = [i * dt for i in range(self.config.record_length)]

        freq   = self.sim_frequency
        amp    = self.sim_amplitude      # peak amplitude
        offset = self.sim_dc_offset
        noise  = 0.02 * amp              # ±1% of peak as noise floor
        wf     = self.sim_waveform.upper()

        def _noise() -> float:
            return noise * random.uniform(-1.0, 1.0)

        if wf == "SQUARE":
            v_vals = [
                (amp if math.sin(2.0 * math.pi * freq * t) >= 0 else -amp) + offset + _noise()
                for t in t_vals
            ]
        elif wf == "TRIANGLE":
            # Triangle: linearly rises from -amp to +amp then back
            v_vals = [
                amp * (2.0 * abs(2.0 * ((freq * t + 0.25) % 1.0) - 1.0) - 1.0) + offset + _noise()
                for t in t_vals
            ]
        elif wf == "RAMP_UP":
            v_vals = [
                amp * (2.0 * ((freq * t) % 1.0) - 1.0) + offset + _noise()
                for t in t_vals
            ]
        elif wf == "RAMP_DOWN":
            v_vals = [
                amp * (1.0 - 2.0 * ((freq * t) % 1.0)) + offset + _noise()
                for t in t_vals
            ]
        else:  # SINE (default)
            v_vals = [
                amp * math.sin(2.0 * math.pi * freq * t) + offset + _noise()
                for t in t_vals
            ]
        return t_vals, v_vals

    def _read_hw_waveform(self) -> Tuple[List[float], List[float]]:
        try:
            if niscope is None:
                raise RuntimeError("ni-hw-drivers is not available")

            # Abort any in-progress acquisition before reconfiguring.
            try:
                self.session.abort()
            except Exception:
                pass  # benign if not in an acquisition state

            coupling_map = {
                "AC": niscope.VerticalCoupling.AC,
                "DC": niscope.VerticalCoupling.DC,
                "GND": niscope.VerticalCoupling.GND,
            }
            coupling = coupling_map.get(self.config.coupling.upper(), niscope.VerticalCoupling.DC)

            trigger_coupling_map = {
                "DC":        niscope.TriggerCoupling.DC,
                "AC":        niscope.TriggerCoupling.AC,
                "HF_REJECT": niscope.TriggerCoupling.HF_REJECT,
                "LF_REJECT": niscope.TriggerCoupling.LF_REJECT,
            }
            trigger_coupling = trigger_coupling_map.get(
                self.config.trigger_coupling.upper(), niscope.TriggerCoupling.DC
            )

            self.session.configure_vertical(
                range=self.config.vertical_range,
                coupling=coupling,
                probe_attenuation=1.0,
            )
            self.session.configure_horizontal_timing(
                min_sample_rate=self.config.sample_rate,
                min_num_pts=self.config.record_length,
                ref_position=50.0,
                num_records=self.config.num_records,
                enforce_realtime=True,
            )
            self.session.configure_trigger_edge(
                trigger_source=self.config.trigger_source,
                level=self.config.trigger_level,
                trigger_coupling=trigger_coupling,
            )

            with self.session.initiate():
                waveforms = self.session.channels[self.config.channel].fetch(
                    num_samples=self.config.record_length,
                    timeout=self.config.timeout_s,
                )

            first = waveforms[0]
            samples = [float(v) for v in first.samples]
            dt = float(getattr(first, "x_increment", 1.0 / max(self.config.sample_rate, 1.0)))
            t_vals = [i * dt for i in range(len(samples))]
            return t_vals, samples
        except Exception as exc:
            self.loggers["error"].exception("Hardware acquisition failed")
            raise RuntimeError(f"Acquisition failed: {exc}") from exc


def compute_stats(samples: List[float]) -> Dict[str, float]:
    if not samples:
        return {"mean": 0.0, "rms": 0.0, "pk_pk": 0.0, "min": 0.0, "max": 0.0}

    total = sum(samples)
    mean = total / len(samples)
    rms = math.sqrt(sum(x * x for x in samples) / len(samples))
    min_v = min(samples)
    max_v = max(samples)
    return {
        "mean": mean,
        "rms": rms,
        "pk_pk": max_v - min_v,
        "min": min_v,
        "max": max_v,
    }


class ScopeApp(tk.Tk):
    def __init__(self, base_dir: Path):
        super().__init__()
        self.title("PXIe-5162 Scope UI (Scope1)")
        self.geometry("1200x780")

        self.base_dir = base_dir
        self.loggers, self.log_paths = setup_loggers(base_dir / "logs")

        self.controller: Optional[ScopeController] = None
        self.polling = False
        self.poll_job = None
        self.fgen_controller = None   # FgenController, created on demand

        self._build_ui()
        self._refresh_log_views()

    def _build_ui(self) -> None:
        cfg_frame = ttk.LabelFrame(self, text="Scope Configuration")
        cfg_frame.pack(fill="x", padx=10, pady=10)

        self.resource_var = tk.StringVar(value="Scope1")
        self.channel_var = tk.StringVar(value="0")
        self.sample_rate_var = tk.StringVar(value="10000000")
        self.record_length_var = tk.StringVar(value="10000")
        self.num_records_var = tk.StringVar(value="1")
        self.vertical_range_var = tk.StringVar(value="5.0")
        self.coupling_var = tk.StringVar(value="DC")
        self.trigger_source_var = tk.StringVar(value="0")
        self.trigger_level_var = tk.StringVar(value="0.1")
        self.trigger_coupling_var = tk.StringVar(value="DC")
        self.timeout_var = tk.StringVar(value="5.0")
        self.interval_ms_var = tk.StringVar(value="500")
        self.simulate_var = tk.BooleanVar(value=(niscope is None))

        fields = [
            ("Resource", self.resource_var),
            ("Channel", self.channel_var),
            ("Sample Rate (S/s)", self.sample_rate_var),
            ("Record Length", self.record_length_var),
            ("Num Records", self.num_records_var),
            ("Vertical Range (V)", self.vertical_range_var),
            ("Trigger Source", self.trigger_source_var),
            ("Trigger Level (V)", self.trigger_level_var),
            ("Timeout (s)", self.timeout_var),
            ("Interval (ms)", self.interval_ms_var),
        ]

        for idx, (label, var) in enumerate(fields):
            ttk.Label(cfg_frame, text=label).grid(row=idx // 5, column=(idx % 5) * 2, padx=6, pady=4, sticky="e")
            if label == "Resource":
                self.resource_combo = ttk.Combobox(cfg_frame, textvariable=var, width=12)
                self.resource_combo.grid(row=idx // 5, column=(idx % 5) * 2 + 1, padx=6, pady=4, sticky="w")
            else:
                ttk.Entry(cfg_frame, textvariable=var, width=14).grid(
                    row=idx // 5, column=(idx % 5) * 2 + 1, padx=6, pady=4, sticky="w"
                )

        ttk.Button(cfg_frame, text="Refresh Devices", command=self.on_refresh_devices).grid(
            row=2, column=3, padx=6, pady=4, sticky="w"
        )

        self.resource_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_device_details())

        ttk.Label(cfg_frame, text="Coupling").grid(row=2, column=0, padx=6, pady=4, sticky="e")
        ttk.Combobox(
            cfg_frame,
            textvariable=self.coupling_var,
            values=["DC", "AC", "GND"],
            width=12,
            state="readonly",
        ).grid(row=2, column=1, padx=6, pady=4, sticky="w")

        ttk.Label(cfg_frame, text="Trig Coupling").grid(row=2, column=4, padx=6, pady=4, sticky="e")
        ttk.Combobox(
            cfg_frame,
            textvariable=self.trigger_coupling_var,
            values=["DC", "AC", "HF_REJECT", "LF_REJECT"],
            width=10,
            state="readonly",
        ).grid(row=2, column=5, padx=6, pady=4, sticky="w")

        ttk.Checkbutton(cfg_frame, text="Simulation Mode", variable=self.simulate_var).grid(
            row=2, column=2, padx=6, pady=4, sticky="w"
        )

        # ── Device Details panel ─────────────────────────────────────────────
        dev_frame = ttk.LabelFrame(self, text="Detected Device Details")
        dev_frame.pack(fill="x", padx=10, pady=(0, 6))

        detail_fields = [
            ("Model", "detail_model_var"),
            ("Serial Number", "detail_serial_var"),
            ("Bus / Slot", "detail_bus_var"),
            ("Channels", "detail_ch_var"),
            ("Max Sample Rate", "detail_sr_var"),
            ("Firmware", "detail_fw_var"),
        ]
        for col_idx, (lbl, attr) in enumerate(detail_fields):
            setattr(self, attr, tk.StringVar(value="—"))
            ttk.Label(dev_frame, text=lbl + ":").grid(row=0, column=col_idx * 2, padx=8, pady=4, sticky="e")
            ttk.Label(dev_frame, textvariable=getattr(self, attr), foreground="#333", width=18, anchor="w").grid(
                row=0, column=col_idx * 2 + 1, padx=8, pady=4, sticky="w"
            )

        ttk.Button(dev_frame, text="Query Details", command=self._update_device_details).grid(
            row=0, column=len(detail_fields) * 2, padx=8, pady=4
        )

        # ── Action buttons ────────────────────────────────────────────────────
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill="x", padx=10)

        ttk.Button(buttons_frame, text="Connect", command=self.on_connect).pack(side="left", padx=4, pady=6)
        ttk.Button(buttons_frame, text="Disconnect", command=self.on_disconnect).pack(side="left", padx=4, pady=6)
        ttk.Button(buttons_frame, text="Acquire Once", command=self.on_acquire_once).pack(side="left", padx=4, pady=6)
        ttk.Button(buttons_frame, text="Start Continuous", command=self.on_start_continuous).pack(side="left", padx=4, pady=6)
        ttk.Button(buttons_frame, text="Stop", command=self.on_stop).pack(side="left", padx=4, pady=6)
        ttk.Button(buttons_frame, text="Refresh Logs", command=self._refresh_log_views).pack(side="left", padx=4, pady=6)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(buttons_frame, textvariable=self.status_var, foreground="navy").pack(side="right", padx=4)

        # ── FGEN Control panel ────────────────────────────────────────────────
        fgen_outer = ttk.LabelFrame(self, text="FGEN Control  (PXIe-5433)")
        fgen_outer.pack(fill="x", padx=10, pady=(0, 4))

        self.fgen_resource_var = tk.StringVar(value="FGEN1")
        self.fgen_channel_var  = tk.StringVar(value="0")
        self.fgen_waveform_var = tk.StringVar(value="SINE")
        self.fgen_freq_var     = tk.StringVar(value="1000")
        self.fgen_amp_var      = tk.StringVar(value="2.0")
        self.fgen_offset_var   = tk.StringVar(value="0.0")
        self.fgen_status_var   = tk.StringVar(value="Not connected")

        # Row 0 – parameter fields
        fgen_fields = [
            ("Resource",       self.fgen_resource_var, None),
            ("Channel",        self.fgen_channel_var,  None),
            ("Frequency (Hz)", self.fgen_freq_var,     None),
            ("Amplitude Vpk-pk", self.fgen_amp_var,    None),
            ("DC Offset (V)",  self.fgen_offset_var,   None),
        ]
        for col, (lbl, var, _) in enumerate(fgen_fields):
            ttk.Label(fgen_outer, text=lbl).grid(row=0, column=col * 2, padx=6, pady=3, sticky="e")
            ttk.Entry(fgen_outer, textvariable=var, width=11).grid(
                row=0, column=col * 2 + 1, padx=6, pady=3, sticky="w"
            )

        ttk.Label(fgen_outer, text="Waveform").grid(row=0, column=10, padx=6, pady=3, sticky="e")
        ttk.Combobox(
            fgen_outer,
            textvariable=self.fgen_waveform_var,
            values=["SINE", "SQUARE", "TRIANGLE", "RAMP_UP", "RAMP_DOWN", "DC"],
            width=10,
            state="readonly",
        ).grid(row=0, column=11, padx=6, pady=3, sticky="w")

        # Row 1 – buttons
        fgen_btn_row = ttk.Frame(fgen_outer)
        fgen_btn_row.grid(row=1, column=0, columnspan=12, sticky="w", padx=4, pady=3)

        ttk.Button(fgen_btn_row, text="Connect FGEN",    command=self.on_fgen_connect).pack(side="left", padx=4)
        ttk.Button(fgen_btn_row, text="Disconnect FGEN", command=self.on_fgen_disconnect).pack(side="left", padx=4)
        ttk.Button(fgen_btn_row, text="Start Output",    command=self.on_fgen_start).pack(side="left", padx=4)
        ttk.Button(fgen_btn_row, text="Stop Output",     command=self.on_fgen_stop).pack(side="left", padx=4)
        ttk.Button(fgen_btn_row, text="Run Test Suite",  command=self.on_run_test_suite).pack(side="left", padx=4)
        ttk.Label(fgen_btn_row, textvariable=self.fgen_status_var, foreground="darkgreen").pack(
            side="left", padx=10
        )

        # ── Waveform plot ─────────────────────────────────────────────────────
        plot_frame = ttk.LabelFrame(self, text="Waveform")
        plot_frame.pack(fill="both", expand=True, padx=10, pady=6)

        self.plot_canvas = tk.Canvas(plot_frame, bg="white", height=330)
        self.plot_canvas.pack(fill="both", expand=True, padx=6, pady=6)

        self.measurement_text = tk.Text(self, height=5)
        self.measurement_text.pack(fill="x", padx=10, pady=6)

        logs_frame = ttk.LabelFrame(self, text="Logs")
        logs_frame.pack(fill="both", expand=True, padx=10, pady=8)

        notebook = ttk.Notebook(logs_frame)
        notebook.pack(fill="both", expand=True)

        self.status_log_text = tk.Text(notebook)
        self.error_log_text = tk.Text(notebook)
        self.measure_log_text = tk.Text(notebook)
        self.test_log_text = tk.Text(notebook)
        notebook.add(self.status_log_text, text="Status Log")
        notebook.add(self.error_log_text, text="Error Log")
        notebook.add(self.measure_log_text, text="Measurement Log")
        notebook.add(self.test_log_text, text="Test Results")

        self.on_refresh_devices()
        self.geometry("1200x980")  # taller to fit FGEN panel

    def on_refresh_devices(self) -> None:
        current = self.resource_var.get().strip() or "Scope1"
        resources = discover_scope_resources(current)
        self.resource_combo.configure(values=resources)
        if self.resource_var.get().strip() not in resources:
            self.resource_var.set(resources[0])
        self.loggers["status"].info("Resource options: %s", ", ".join(resources))
        self.status_var.set(f"Resource options updated ({len(resources)})")
        self._update_device_details()

    def _update_device_details(self) -> None:
        resource = self.resource_var.get().strip() or "Scope1"
        simulate = self.simulate_var.get() or niscope is None
        self.status_var.set(f"Querying details for {resource}…")

        def _query() -> None:
            # If there's an open session, read directly from it; otherwise probe.
            if (
                self.controller is not None
                and self.controller.connected
                and not self.controller.simulate
                and self.controller.session is not None
            ):
                det = DeviceDetails()
                sess = self.controller.session
                _sentinel = object()
                _SCOPE_ATTRS = {
                    "model": "instrument_model",
                    "serial": "serial_number",
                    "channel_count": "channel_count",
                    "max_sample_rate": "max_real_time_sampling_rate",
                    "firmware": "firmware_revision",
                }
                for field, attr in _SCOPE_ATTRS.items():
                    val = getattr(sess, attr, _sentinel)
                    if val is _sentinel:
                        continue
                    str_val = str(val).strip()
                    if not str_val or str_val == "None":
                        continue
                    if field == "max_sample_rate":
                        try:
                            det.max_sample_rate = f"{float(str_val) / 1e9:.3f} GS/s"
                            continue
                        except ValueError:
                            pass
                    if field == "channel_count":
                        det.channel_count = str_val
                    elif field == "model":
                        det.model = str_val
                    elif field == "serial":
                        det.serial = str_val
                    elif field == "firmware":
                        det.firmware = str_val
                pxi_chassis = getattr(sess, "pxi_chassis", None)
                slot = getattr(sess, "slot_number", None)
                bus = getattr(sess, "bus_number", None)
                if pxi_chassis is not None and slot is not None:
                    det.bus_slot = f"Chassis {pxi_chassis}, Slot {slot}"
                elif bus is not None and slot is not None:
                    det.bus_slot = f"Bus {bus}, Slot {slot}"
                elif slot is not None:
                    det.bus_slot = f"Slot {slot}"
            else:
                det = query_device_details(resource, simulate=simulate)

            self.loggers["status"].info(
                "Device details [%s]: model=%s serial=%s bus=%s channels=%s maxSR=%s fw=%s",
                resource, det.model, det.serial, det.bus_slot,
                det.channel_count, det.max_sample_rate, det.firmware,
            )
            self.after(0, lambda: self._apply_device_details(det))

        threading.Thread(target=_query, daemon=True).start()

    def _apply_device_details(self, det: DeviceDetails) -> None:
        self.detail_model_var.set(det.model)
        self.detail_serial_var.set(det.serial)
        self.detail_bus_var.set(det.bus_slot)
        self.detail_ch_var.set(det.channel_count)
        self.detail_sr_var.set(det.max_sample_rate)
        self.detail_fw_var.set(det.firmware)
        self.status_var.set(f"Details loaded for {self.resource_var.get().strip()}")
        self._refresh_log_views()

    # ------------------------------------------------------------------
    # FGEN helpers
    # ------------------------------------------------------------------

    def _fgen_config_from_ui(self):
        if FgenConfig is None:
            raise RuntimeError("fgen.py module not found — ensure fgen.py is in the same folder.")
        return FgenConfig(
            resource_name=self.fgen_resource_var.get().strip(),
            channel=self.fgen_channel_var.get().strip(),
            waveform=self.fgen_waveform_var.get().strip(),
            frequency=float(self.fgen_freq_var.get()),
            amplitude=float(self.fgen_amp_var.get()),
            dc_offset=float(self.fgen_offset_var.get()),
        )

    def _sync_scope_sim_to_fgen(self) -> None:
        """Copy FGEN UI settings to the scope simulator so live plots look right."""
        if self.controller is None or not self.controller.simulate:
            return
        try:
            cfg = self._fgen_config_from_ui()
            self.controller.sim_frequency = cfg.frequency
            self.controller.sim_amplitude = cfg.amplitude / 2.0
            self.controller.sim_waveform  = cfg.waveform
            self.controller.sim_dc_offset = cfg.dc_offset
        except (ValueError, RuntimeError):
            pass

    def on_fgen_connect(self) -> None:
        if FgenController is None:
            messagebox.showerror("FGEN Error", "fgen.py module not found.")
            return
        try:
            cfg = self._fgen_config_from_ui()
            simulate = self.simulate_var.get() or niscope is None
            self.fgen_controller = FgenController(cfg, self.loggers, simulate=simulate)
            self.fgen_controller.connect()
            self.fgen_status_var.set(
                f"Connected ({'sim' if self.fgen_controller.simulate else 'hw'})"
            )
            self._refresh_log_views()
        except Exception as exc:
            self.loggers["error"].exception("FGEN connect failed")
            messagebox.showerror("FGEN Connection Error", str(exc))
            self.fgen_status_var.set("Connection failed")

    def on_fgen_disconnect(self) -> None:
        if self.fgen_controller is not None:
            self.fgen_controller.disconnect()
            self.fgen_controller = None
        self.fgen_status_var.set("Disconnected")
        self._refresh_log_views()

    def on_fgen_start(self) -> None:
        if self.fgen_controller is None:
            messagebox.showwarning("FGEN", "Connect the FGEN first.")
            return
        try:
            cfg = self._fgen_config_from_ui()
            self.fgen_controller.configure(cfg)
            self.fgen_controller.start_output()
            self._sync_scope_sim_to_fgen()
            self.fgen_status_var.set(
                f"Output ON — {cfg.waveform} {cfg.frequency:.0f} Hz {cfg.amplitude:.3f} Vpk-pk"
            )
            self._refresh_log_views()
        except Exception as exc:
            self.loggers["error"].exception("FGEN start failed")
            messagebox.showerror("FGEN Error", str(exc))
            self.fgen_status_var.set("Start failed")

    def on_fgen_stop(self) -> None:
        if self.fgen_controller is not None:
            self.fgen_controller.stop_output()
        self.fgen_status_var.set("Output OFF")
        self._refresh_log_views()

    def on_run_test_suite(self) -> None:
        """Launch the automated FGEN→Scope test suite in a background thread."""
        def _run() -> None:
            try:
                from test_scope_with_fgen import run_test_suite
                simulate = self.simulate_var.get() or niscope is None
                scope_res = self.resource_var.get().strip() or "Scope1"
                fgen_res  = self.fgen_resource_var.get().strip() or "FGEN1"
                self.after(0, lambda: self.fgen_status_var.set("Test suite running…"))
                failures = run_test_suite(
                    scope_resource=scope_res,
                    fgen_resource=fgen_res,
                    simulate=simulate,
                    log_dir=self.base_dir / "logs",
                )
                result_msg = (
                    "Test suite complete — ALL PASSED ✓"
                    if failures == 0
                    else f"Test suite done — {failures} FAILURE(S) ✗"
                )
                self.after(0, lambda: self.fgen_status_var.set(result_msg))
                self.after(0, self._refresh_log_views)
            except Exception as exc:
                self.loggers["error"].exception("Test suite error")
                self.after(0, lambda: messagebox.showerror("Test Suite Error", str(exc)))
                self.after(0, lambda: self.fgen_status_var.set("Test suite error"))

        threading.Thread(target=_run, daemon=True).start()

    def _config_from_ui(self) -> ScopeConfig:
        return ScopeConfig(
            resource_name=self.resource_var.get().strip(),
            channel=self.channel_var.get().strip(),
            sample_rate=float(self.sample_rate_var.get()),
            record_length=int(self.record_length_var.get()),
            num_records=int(self.num_records_var.get()),
            vertical_range=float(self.vertical_range_var.get()),
            coupling=self.coupling_var.get().strip(),
            trigger_source=self.trigger_source_var.get().strip(),
            trigger_level=float(self.trigger_level_var.get()),
            trigger_coupling=self.trigger_coupling_var.get().strip(),
            timeout_s=float(self.timeout_var.get()),
        )

    def on_connect(self) -> None:
        try:
            config = self._config_from_ui()
            self.controller = ScopeController(config, self.loggers, simulate=self.simulate_var.get())
            self.controller.connect()
            self.status_var.set(f"Connected ({'simulation' if self.controller.simulate else 'hardware'})")
            self._refresh_log_views()
            self._update_device_details()
        except Exception as exc:
            self.loggers["error"].exception("Connect action failed")
            messagebox.showerror("Connection Error", str(exc))
            self.status_var.set("Connection failed")
            self._refresh_log_views()

    def on_disconnect(self) -> None:
        self.on_stop()
        if self.controller is not None:
            self.controller.disconnect()
            self.status_var.set("Disconnected")
            self._refresh_log_views()

    def on_acquire_once(self) -> None:
        if self.controller is None:
            messagebox.showwarning("Not Connected", "Connect to the scope first.")
            return

        thread = threading.Thread(target=self._acquire_and_update_ui, daemon=True)
        thread.start()

    def _acquire_and_update_ui(self) -> None:
        try:
            t_vals, v_vals = self.controller.acquire()
            stats = compute_stats(v_vals)
            self.after(ms=0, func=lambda: self._update_plot(t_vals, v_vals))
            self.after(ms=0, func=lambda: self._update_measurement_text(stats, len(v_vals)))
            self.after(ms=0, func=self._refresh_log_views)
            self.after(ms=0, func=lambda: self.status_var.set("Acquisition complete"))
        except Exception as exc:
            self.loggers["error"].exception("Acquire action failed")
            self.after(ms=0, func=lambda: messagebox.showerror("Acquisition Error", str(exc)))
            self.after(ms=0, func=lambda: self.status_var.set("Acquisition failed"))
            self.after(ms=0, func=self._refresh_log_views)

    def on_start_continuous(self) -> None:
        if self.controller is None:
            messagebox.showwarning("Not Connected", "Connect to the scope first.")
            return

        self.polling = True
        self.status_var.set("Continuous acquisition running")
        self._continuous_tick()

    def _continuous_tick(self) -> None:
        if not self.polling:
            return
        self.on_acquire_once()
        try:
            interval_ms = max(50, int(self.interval_ms_var.get()))
        except ValueError:
            interval_ms = 500
        self.poll_job = self.after(interval_ms, self._continuous_tick)

    def on_stop(self) -> None:
        self.polling = False
        if self.poll_job is not None:
            self.after_cancel(self.poll_job)
            self.poll_job = None
        self.status_var.set("Stopped")

    def _update_measurement_text(self, stats: Dict[str, float], count: int) -> None:
        self.measurement_text.delete("1.0", tk.END)
        self.measurement_text.insert(
            tk.END,
            (
                f"Samples: {count}\n"
                f"Mean: {stats['mean']:.6f} V\n"
                f"RMS: {stats['rms']:.6f} V\n"
                f"Pk-Pk: {stats['pk_pk']:.6f} V\n"
                f"Min/Max: {stats['min']:.6f} / {stats['max']:.6f} V\n"
            ),
        )

    def _update_plot(self, t_vals: List[float], v_vals: List[float]) -> None:
        self.plot_canvas.delete("all")
        if not t_vals or not v_vals:
            return

        width = max(self.plot_canvas.winfo_width(), 10)
        height = max(self.plot_canvas.winfo_height(), 10)
        left, top, right, bottom = 45, 20, width - 15, height - 35

        self.plot_canvas.create_rectangle(left, top, right, bottom, outline="#888")

        min_t, max_t = t_vals[0], t_vals[-1]
        min_v, max_v = min(v_vals), max(v_vals)
        if abs(max_v - min_v) < 1e-12:
            max_v += 0.5
            min_v -= 0.5

        def to_xy(t: float, v: float) -> Tuple[float, float]:
            x = left + (t - min_t) * (right - left) / max(max_t - min_t, 1e-12)
            y = bottom - (v - min_v) * (bottom - top) / (max_v - min_v)
            return x, y

        step = max(1, len(t_vals) // 2000)
        points: List[float] = []
        for idx in range(0, len(t_vals), step):
            x, y = to_xy(t_vals[idx], v_vals[idx])
            points.extend([x, y])

        if len(points) >= 4:
            self.plot_canvas.create_line(*points, fill="#0d47a1", width=1.3)

        self.plot_canvas.create_text(left, bottom + 15, text="0 s", anchor="w")
        self.plot_canvas.create_text(right, bottom + 15, text=f"{max_t:.6e} s", anchor="e")
        self.plot_canvas.create_text(left - 5, top, text=f"{max_v:.3f} V", anchor="e")
        self.plot_canvas.create_text(left - 5, bottom, text=f"{min_v:.3f} V", anchor="e")

    def _refresh_log_views(self) -> None:
        self._load_text(self.status_log_text, self.log_paths["status"])
        self._load_text(self.error_log_text, self.log_paths["error"])
        self._load_text(self.measure_log_text, self.log_paths["measurement"])
        test_log = self.base_dir / "logs" / "test_results.log"
        self._load_text(self.test_log_text, test_log)

    @staticmethod
    def _load_text(widget: tk.Text, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            content = f"Failed to read {file_path.name}: {exc}"

        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)


def run_self_test(base_dir: Path) -> int:
    loggers, paths = setup_loggers(base_dir / "logs")
    controller = ScopeController(ScopeConfig(), loggers=loggers, simulate=True)
    controller.connect()
    _, samples = controller.acquire()
    stats = compute_stats(samples)
    controller.disconnect()

    print("Self-test complete")
    print(f"Samples: {len(samples)}")
    print(f"RMS: {stats['rms']:.6f} V")
    print(f"Status log: {paths['status']}")
    print(f"Error log: {paths['error']}")
    print(f"Measurement log: {paths['measurement']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NI PXIe-5162 signal acquisition UI")
    parser.add_argument("--self-test", action="store_true", help="Run a quick simulation test and exit")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent

    if args.self_test:
        return run_self_test(base_dir)

    app = ScopeApp(base_dir)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
