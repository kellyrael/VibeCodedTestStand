# niscope Reference — NI-SCOPE Python API

**Package**: `niscope` (via `pip install niscope`)
**Runtime**: NI-SCOPE driver (ni.com/downloads)
**Instruments**: PXI/PXIe Oscilloscopes and Digitizers (NI 5110, 5111, 5113, 5160, 5162, 5164, 5165, 5185, 5186, 5620, 5621, 5911, 5912, 5922, PXI-5900)
**Current Version**: 1.4.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Session Creation](#session-creation)
2. [Key Enums](#key-enums)
3. [Essential Properties](#essential-properties)
4. [Core Methods](#core-methods)
5. [Waveform Data Structures](#waveform-data-structures)
6. [Canonical Examples](#canonical-examples)
7. [Triggering](#triggering)
8. [Measurements](#measurements)
9. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Session Creation

```python
import niscope

# Basic session
with niscope.Session(resource_name="PXI1Slot5") as session:
    pass

# With simulation
options = "Simulate=1, DriverSetup=Model:5164; BoardType:PXIe"
with niscope.Session(resource_name="PXI1Slot5", options=options) as session:
    pass

# Reset on open
with niscope.Session(resource_name="PXI1Slot5", reset_device=True) as session:
    pass
```

### Session Constructor Parameters

| Parameter       | Type   | Default  | Description                                         |
|-----------------|--------|----------|-----------------------------------------------------|
| `resource_name` | str    | Required | Device name (e.g., `"PXI1Slot5"`, `"Dev1"`)        |
| `id_query`      | bool   | False    | Verify device compatibility on open                 |
| `reset_device`  | bool   | False    | Reset device to known state on open                 |
| `options`       | dict/str | {}     | Session options (simulate, driver_setup, etc.)      |

### Channel Access

```python
session.channels["0"]         # Single channel
session.channels["0,1"]       # Multiple channels by name
session.channels[0]           # Single channel by index
session.channels[[0, 1, 2]]   # Multiple channels by index list
```

---

## Key Enums

### niscope.VerticalCoupling

| Value | Description                     |
|-------|---------------------------------|
| `AC`  | AC coupling (blocks DC offset)  |
| `DC`  | DC coupling (full signal)       |
| `GND` | Ground reference                |

### niscope.TriggerType

| Value        | Description                              |
|--------------|------------------------------------------|
| `EDGE`       | Trigger on voltage threshold crossing    |
| `HYSTERESIS` | Edge trigger with noise rejection band   |
| `DIGITAL`    | Trigger from digital input               |
| `WINDOW`     | Trigger when signal enters/leaves window |
| `SOFTWARE`   | Trigger via software command             |
| `TV`         | Trigger on video signal                  |
| `GLITCH`     | Trigger on narrow pulse (glitch)         |
| `WIDTH`      | Trigger on pulse within width bounds     |
| `RUNT`       | Trigger on pulse that crosses one threshold but not another |
| `IMMEDIATE`  | Free-run, no trigger condition           |

### niscope.TriggerSlope

| Value          | Description             |
|----------------|-------------------------|
| `POSITIVE`     | Rising edge             |
| `NEGATIVE`     | Falling edge            |
| `SLOPE_EITHER` | Either edge             |

### niscope.TriggerCoupling

| Value             | Description                        |
|-------------------|------------------------------------|
| `AC`              | AC coupling                        |
| `DC`              | DC coupling                        |
| `HF_REJECT`       | High-frequency rejection           |
| `LF_REJECT`       | Low-frequency rejection            |
| `AC_PLUS_HF_REJECT` | AC coupling + HF rejection      |

### niscope.AcquisitionType

| Value      | Description                                   |
|------------|-----------------------------------------------|
| `NORMAL`   | Standard acquisition                          |
| `FLEXRES`  | Flexible resolution (NI 5922)                 |
| `DDC`      | Digital down-conversion (NI 5620/5621)        |

### niscope.AcquisitionStatus

| Value            | Description                  |
|------------------|------------------------------|
| `COMPLETE`       | Acquisition finished         |
| `IN_PROGRESS`    | Acquisition still running    |
| `STATUS_UNKNOWN` | Status cannot be determined  |

### niscope.FetchRelativeTo

| Value          | Description                              |
|----------------|------------------------------------------|
| `READ_POINTER` | Relative to current read position        |
| `PRETRIGGER`   | Relative to pretrigger point             |
| `NOW`          | Relative to current time                 |
| `START`        | Relative to start of acquisition         |
| `TRIGGER`      | Relative to trigger event                |

### niscope.WhichTrigger

| Value            | Description                    |
|------------------|--------------------------------|
| `START`          | Start trigger                  |
| `ARM_REFERENCE`  | Arm reference trigger          |
| `REFERENCE`      | Reference trigger              |
| `ADVANCE`        | Advance trigger                |

### niscope.TriggerWindowMode

| Value                | Description                    |
|----------------------|--------------------------------|
| `ENTERING`           | Signal entering window         |
| `LEAVING`            | Signal leaving window          |
| `ENTERING_OR_LEAVING`| Either direction               |

### niscope.VideoSignalFormat

| Value               | Description        |
|---------------------|--------------------|
| `NTSC`              | NTSC standard      |
| `PAL`               | PAL standard       |
| `SECAM`             | SECAM standard     |
| `M_PAL`             | M-PAL standard     |
| `VIDEO_480I_59_94_` | 480i @ 59.94 fps   |
| `VIDEO_480I_60_`    | 480i @ 60 fps      |
| `VIDEO_480P_`       | 480p               |
| `VIDEO_576I_`       | 576i               |
| `VIDEO_576P_`       | 576p               |
| `VIDEO_720P_`       | 720p               |
| `VIDEO_1080I_`      | 1080i              |
| `VIDEO_1080P_24_`   | 1080p @ 24 fps     |

### niscope.ScalarMeasurement (selected)

Common scalar measurements for `fetch_measurement_stats()`:

| Value                | Description                    |
|----------------------|--------------------------------|
| `RISE_TIME`          | Signal rise time               |
| `FALL_TIME`          | Signal fall time               |
| `FREQUENCY`          | Signal frequency               |
| `PERIOD`             | Signal period                  |
| `VOLTAGE_RMS`        | RMS voltage                    |
| `VOLTAGE_PEAK_TO_PEAK`| Peak-to-peak voltage          |
| `VOLTAGE_MAX`        | Maximum voltage                |
| `VOLTAGE_MIN`        | Minimum voltage                |
| `VOLTAGE_HIGH`       | High-level voltage             |
| `VOLTAGE_LOW`        | Low-level voltage              |
| `VOLTAGE_AVERAGE`    | Average voltage                |
| `VOLTAGE_CYCLE_RMS`  | Cycle RMS voltage              |
| `VOLTAGE_CYCLE_AVERAGE`| Cycle average voltage         |
| `WIDTH_POS`          | Positive pulse width           |
| `WIDTH_NEG`          | Negative pulse width           |
| `DUTY_CYCLE_POS`     | Positive duty cycle            |
| `DUTY_CYCLE_NEG`     | Negative duty cycle            |
| `OVERSHOOT`          | Overshoot percentage           |
| `PRESHOOT`           | Preshoot percentage            |

### niscope.ArrayMeasurement (selected)

Common array measurements for `fetch_array_measurement()`:

| Value                    | Description                     |
|--------------------------|---------------------------------|
| `ARRAY_GAIN`             | Gain per sample                 |
| `MULTI_ACQ_VOLTAGE_HISTOGRAM` | Voltage histogram          |
| `MULTI_ACQ_TIME_HISTOGRAM`    | Time histogram             |
| `MULTI_ACQ_AVERAGE`      | Multi-acquisition average       |
| `POLYNOMIAL_INTERPOLATION` | Interpolated waveform         |
| `FFT_PHASE_SPECTRUM`     | FFT phase spectrum              |
| `FFT_AMP_SPECTRUM_VOLTS_RMS` | FFT amplitude in Vrms      |

---

## Essential Properties

### Horizontal / Timing Properties

| Property                    | Type      | Description                                   |
|-----------------------------|-----------|-----------------------------------------------|
| `horz_record_length`        | int       | Actual samples per record (read-only after configure) |
| `horz_sample_rate`          | float     | Effective sample rate in Hz (read-only)       |
| `horz_time_per_record`      | timedelta | Time per record (read-only)                   |
| `horz_record_ref_position`  | float     | Reference position (0-100%)                   |
| `horz_num_records`          | int       | Number of records to acquire                  |
| `horz_min_num_pts`          | int       | Minimum points requested                      |
| `horz_enforce_realtime`     | bool      | Enforce real-time sampling                    |
| `min_sample_rate`           | float     | Requested minimum sample rate                 |
| `acquisition_type`          | Enum      | NORMAL, FLEXRES, DDC                          |

### Vertical / Channel Properties (per-channel via `session.channels[...]`)

| Property                   | Type   | Description                                   |
|----------------------------|--------|-----------------------------------------------|
| `vertical_range`           | float  | Vertical range in volts (peak-to-peak)        |
| `vertical_offset`          | float  | Vertical offset from ground (V)               |
| `vertical_coupling`        | Enum   | AC, DC, or GND                                |
| `probe_attenuation`        | float  | Probe attenuation factor (1, 10, 100, etc.)   |
| `channel_enabled`          | bool   | Enable/disable channel                        |
| `input_impedance`          | float  | Input impedance (50 Ω or 1 MΩ)               |
| `max_input_frequency`      | float  | Bandwidth limit (Hz), 0 = full bandwidth      |

### Trigger Properties

| Property                  | Type      | Description                                |
|---------------------------|-----------|--------------------------------------------|
| `trigger_type`            | Enum      | EDGE, WINDOW, DIGITAL, IMMEDIATE, etc.     |
| `trigger_source`          | str       | Trigger source channel (e.g., `"0"`)       |
| `trigger_level`           | float     | Trigger threshold voltage                  |
| `trigger_slope`           | Enum      | POSITIVE, NEGATIVE, SLOPE_EITHER           |
| `trigger_coupling`        | Enum      | AC, DC, HF_REJECT, LF_REJECT              |
| `trigger_delay_time`      | timedelta | Delay after trigger before acquisition     |
| `trigger_holdoff`         | timedelta | Minimum time between triggers              |
| `trigger_impedance`       | float     | Trigger input impedance (50 or 1M)         |

### Device Properties (read-only)

| Property                        | Type  | Description                         |
|---------------------------------|-------|-------------------------------------|
| `channel_count`                 | int   | Number of channels                  |
| `instrument_model`              | str   | Model number                        |
| `serial_number`                 | str   | Serial number                       |
| `device_temperature`            | float | Temperature in °C                   |
| `onboard_memory_size`           | int   | Total memory in bytes               |
| `resolution`                    | int   | Bits of valid data                  |

---

## Core Methods

### Configuration Methods

```python
# Configure vertical (per channel)
session.channels["0"].configure_vertical(
    range=10.0,                # 10 V peak-to-peak
    coupling=niscope.VerticalCoupling.DC,
    offset=0.0,                # optional, default 0
    probe_attenuation=1.0,     # optional, default 1
    enabled=True               # optional, default True
)

# Configure horizontal timing
session.configure_horizontal_timing(
    min_sample_rate=50_000_000,  # 50 MS/s
    min_num_pts=1000,
    ref_position=50.0,           # Trigger at midpoint (%)
    num_records=1,
    enforce_realtime=True
)

# Configure channel characteristics
session.channels["0"].configure_chan_characteristics(
    input_impedance=1_000_000,   # 1 MΩ
    max_input_frequency=0        # 0 = full bandwidth
)
```

### Trigger Configuration

```python
# Edge trigger (most common)
session.configure_trigger_edge(
    trigger_source="0",
    level=0.5,
    slope=niscope.TriggerSlope.POSITIVE,
    trigger_coupling=niscope.TriggerCoupling.DC,
    holdoff=0.0,
    delay=0.0
)

# Immediate trigger (free-run)
session.configure_trigger_immediate()

# Software trigger
session.configure_trigger_software(holdoff=0.0, delay=0.0)

# Window trigger
session.configure_trigger_window(
    trigger_source="0",
    low_level=-1.0,
    high_level=1.0,
    window_mode=niscope.TriggerWindowMode.ENTERING,
    trigger_coupling=niscope.TriggerCoupling.DC,
    holdoff=0.0,
    delay=0.0
)

# Hysteresis trigger (edge with noise band)
session.configure_trigger_hysteresis(
    trigger_source="0",
    level=0.5,
    hysteresis=0.1,
    slope=niscope.TriggerSlope.POSITIVE,
    trigger_coupling=niscope.TriggerCoupling.DC,
    holdoff=0.0,
    delay=0.0
)

# Digital trigger
session.configure_trigger_digital(
    trigger_source="PFI0",
    slope=niscope.TriggerSlope.POSITIVE,
    holdoff=0.0,
    delay=0.0
)

# Video trigger
session.configure_trigger_video(
    trigger_source="0",
    signal_format=niscope.VideoSignalFormat.NTSC,
    event=niscope.VideoTriggerEvent.FIELD1,
    polarity=niscope.VideoPolarity.POSITIVE,
    trigger_coupling=niscope.TriggerCoupling.DC,
    enable_dc_restore=False,
    line_number=1,
    holdoff=0.0,
    delay=0.0
)
```

### Acquisition Methods

```python
# fetch() — Get waveforms from buffer (requires prior initiate)
# Returns list of WaveformInfo objects
waveforms = session.channels["0,1"].fetch(
    num_samples=1000,
    relative_to=niscope.FetchRelativeTo.PRETRIGGER,
    offset=0,
    record_number=0,
    num_records=1,
    timeout=5.0
)

# fetch_into() — Fetch into pre-allocated numpy array (for performance)
import numpy as np
waveform_array = np.zeros(1000, dtype=np.float64)
waveform_info = session.channels["0"].fetch_into(
    waveform=waveform_array,
    relative_to=niscope.FetchRelativeTo.READ_POINTER,
    offset=0,
    record_number=0,
    num_records=1,
    timeout=5.0
)

# read() — High-level: configure + initiate + fetch in one call
waveforms = session.channels["0"].read(
    num_samples=1000,
    relative_to=niscope.FetchRelativeTo.PRETRIGGER,
    offset=0,
    record_number=0,
    num_records=1,
    timeout=5.0
)

# fetch_array_measurement() — Get processed measurement arrays
measurements = session.channels["0"].fetch_array_measurement(
    array_meas_function=niscope.ArrayMeasurement.ARRAY_GAIN,
    meas_wfm_size=1000
)

# fetch_measurement_stats() — Get scalar measurement statistics
stats = session.channels["0"].fetch_measurement_stats(
    scalar_meas_function=niscope.ScalarMeasurement.FREQUENCY
)
```

### Session Control

```python
# Initiate acquisition (use as context manager)
with session.initiate():
    waveforms = session.channels["0,1"].fetch(num_samples=1000)
# Automatically aborts on exit

# Check acquisition status
status = session.acquisition_status()
# Returns: AcquisitionStatus.COMPLETE or AcquisitionStatus.IN_PROGRESS

# Send software trigger
session.send_software_trigger_edge(which_trigger=niscope.WhichTrigger.START)

# Auto-setup (automatically configure based on input signal)
session.auto_setup()

# Abort acquisition
session.abort()

# Reset
session.reset()
```

### Calibration

```python
session.self_cal(option=niscope.Option.SELF_CALIBRATE_ALL_CHANNELS)
cal_date = session.get_self_cal_last_date_and_time()
cal_temp = session.get_self_cal_last_temp()
```

### Waveform Processing

```python
# Add measurement processing step to channel
session.channels["0"].add_waveform_processing(
    meas_function=niscope.ArrayMeasurement.MULTI_ACQ_AVERAGE
)

# Clear all processing
session.channels["0"].clear_waveform_processing()

# Clear measurement statistics
session.channels["0"].clear_waveform_measurement_stats(
    clearable_measurement=niscope.ClearableMeasurement.ALL_MEASUREMENTS
)
```

---

## Waveform Data Structures

### WaveformInfo

Returned by `fetch()`, `read()`, and `fetch_into()`:

```python
waveform.channel              # str — channel name (e.g., "0")
waveform.record               # int — record number
waveform.samples              # numpy array — waveform voltage data
waveform.absolute_initial_x   # float — timestamp of first sample (seconds)
waveform.relative_initial_x   # float — time from trigger to first sample
waveform.x_increment          # float — time between samples (seconds)
waveform.offset               # float — vertical offset for scaling
waveform.gain                 # float — vertical gain for scaling

# Scaling formula: voltage = samples * gain + offset
```

### MeasurementStats

Returned by `fetch_measurement_stats()`:

```python
stat.result       # float — measurement value
stat.mean         # float — average across all stats
stat.stdev        # float — standard deviation
stat.min_val      # float — minimum value
stat.max_val      # float — maximum value
stat.num_in_stats # int — count of measurements in stats
stat.channel      # str — channel name
stat.record       # int — record number
```

---

## Canonical Examples

### Example 1: Single-Shot Waveform Acquisition

The most fundamental oscilloscope operation.

```python
import niscope

def acquire_waveform(resource_name, voltage_range=10.0, sample_rate=50e6, num_points=1000):
    """Acquire a single waveform from channel 0."""
    with niscope.Session(resource_name) as session:
        # Configure vertical
        session.channels["0"].configure_vertical(
            range=voltage_range,
            coupling=niscope.VerticalCoupling.DC
        )

        # Configure horizontal timing
        session.configure_horizontal_timing(
            min_sample_rate=sample_rate,
            min_num_pts=num_points,
            ref_position=50.0,
            num_records=1,
            enforce_realtime=True
        )

        # Configure edge trigger
        session.configure_trigger_edge(
            trigger_source="0",
            level=0.0,
            slope=niscope.TriggerSlope.POSITIVE
        )

        # Acquire
        with session.initiate():
            waveforms = session.channels["0"].fetch(num_records=1)

        return waveforms[0]

# Usage
wfm = acquire_waveform("PXI1Slot5")
print(f"Acquired {len(wfm.samples)} samples at {1.0/wfm.x_increment:.0f} S/s")
```

### Example 2: Multi-Channel, Multi-Record Acquisition

```python
import niscope

def acquire_multi_channel(resource_name, num_records=10):
    """Acquire multiple triggered records from two channels."""
    with niscope.Session(resource_name) as session:
        # Configure channels independently
        session.channels["0"].configure_vertical(
            range=1.0, coupling=niscope.VerticalCoupling.AC
        )
        session.channels["1"].configure_vertical(
            range=10.0, coupling=niscope.VerticalCoupling.DC
        )

        # Configure timing
        session.configure_horizontal_timing(
            min_sample_rate=100_000_000,
            min_num_pts=5000,
            ref_position=10.0,   # 10% pre-trigger
            num_records=num_records,
            enforce_realtime=True
        )

        # Immediate trigger (free-run)
        session.configure_trigger_immediate()

        # Acquire
        with session.initiate():
            waveforms = session.channels["0,1"].fetch(num_records=num_records)

        # Filter by channel
        ch0_waveforms = [wfm for wfm in waveforms if wfm.channel == "0"]
        ch1_waveforms = [wfm for wfm in waveforms if wfm.channel == "1"]

        return ch0_waveforms, ch1_waveforms

# Usage
ch0, ch1 = acquire_multi_channel("PXI1Slot5", num_records=20)
print(f"Channel 0: {len(ch0)} records, Channel 1: {len(ch1)} records")
```

### Example 3: Continuous Streaming Acquisition

```python
import niscope
import numpy as np

def stream_acquisition(resource_name, total_samples=1_000_000, samples_per_fetch=1000):
    """Stream data continuously using fetch_into for performance."""
    with niscope.Session(resource_name) as session:
        session.channels["0"].configure_vertical(
            range=1.0, coupling=niscope.VerticalCoupling.DC
        )
        session.configure_horizontal_timing(
            min_sample_rate=1_000_000,
            min_num_pts=1,
            ref_position=0.0,
            num_records=1,
            enforce_realtime=True
        )
        session.configure_trigger_software()

        waveform = np.zeros(total_samples, dtype=np.float64)
        current_pos = 0

        with session.initiate():
            session.send_software_trigger_edge(niscope.WhichTrigger.START)
            while current_pos < total_samples:
                session.channels["0"].fetch_into(
                    waveform[current_pos:current_pos + samples_per_fetch],
                    relative_to=niscope.FetchRelativeTo.READ_POINTER
                )
                current_pos += samples_per_fetch

        return waveform
```

### Example 4: Measurement Statistics

```python
import niscope

def measure_signal_stats(resource_name, num_records=100):
    """Acquire multiple records and measure frequency statistics."""
    with niscope.Session(resource_name) as session:
        session.channels["0"].configure_vertical(
            range=10.0, coupling=niscope.VerticalCoupling.DC
        )
        session.configure_horizontal_timing(
            min_sample_rate=1e6,
            min_num_pts=10000,
            ref_position=50.0,
            num_records=num_records,
            enforce_realtime=True
        )
        session.configure_trigger_edge(
            trigger_source="0",
            level=1.0,
            trigger_coupling=niscope.TriggerCoupling.DC
        )

        with session.initiate():
            stats = session.channels["0"].fetch_measurement_stats(
                scalar_meas_function=niscope.ScalarMeasurement.FREQUENCY
            )

        for s in stats:
            print(f"Record {s.record}: Freq={s.result:.1f} Hz, "
                  f"Mean={s.mean:.1f}, StdDev={s.stdev:.2f}")

        return stats
```

---

## Triggering

### Edge Trigger (Most Common)

```python
session.configure_trigger_edge(
    trigger_source="0",          # Channel 0
    level=0.5,                   # 500 mV threshold
    slope=niscope.TriggerSlope.POSITIVE,
    trigger_coupling=niscope.TriggerCoupling.DC
)
```

### Window Trigger

Trigger when signal enters or exits a voltage window.

```python
session.configure_trigger_window(
    trigger_source="0",
    low_level=-0.5,
    high_level=0.5,
    window_mode=niscope.TriggerWindowMode.LEAVING,  # Trigger when signal leaves window
    trigger_coupling=niscope.TriggerCoupling.DC
)
```

### Multi-Stage Triggering

Use arm/reference triggers for multi-stage trigger setups:

```python
# Set up arm reference trigger (gate) + edge trigger
session.trigger_type = niscope.TriggerType.EDGE
session.trigger_source = "0"
session.trigger_level = 1.0
session.arm_ref_trig_src = "PXI_Trig0"  # Arm from external source
```

---

## Measurements

### Scalar Measurements

```python
with session.initiate():
    # Measure frequency
    freq_stats = session.channels["0"].fetch_measurement_stats(
        scalar_meas_function=niscope.ScalarMeasurement.FREQUENCY
    )

    # Measure rise time
    rise_stats = session.channels["0"].fetch_measurement_stats(
        scalar_meas_function=niscope.ScalarMeasurement.RISE_TIME
    )

    # Measure peak-to-peak
    vpp_stats = session.channels["0"].fetch_measurement_stats(
        scalar_meas_function=niscope.ScalarMeasurement.VOLTAGE_PEAK_TO_PEAK
    )
```

### Measurement Reference Levels

Configure how reference levels are computed for timing measurements:

```python
session.channels["0"].meas_chan_low_ref_level = 10.0    # 10% for low reference
session.channels["0"].meas_chan_mid_ref_level = 50.0    # 50% for mid reference
session.channels["0"].meas_chan_high_ref_level = 90.0   # 90% for high reference
session.channels["0"].meas_percentage_method = niscope.PercentageMethod.BASETOP
```

---

## Driver-Specific Gotchas

1. **Channel names are always strings**: Even when you use integer indices like `channels[0]`, the `channel` attribute in `WaveformInfo` is always a string `"0"`. Filter with string comparison.

2. **`ref_position` is a percentage (0-100)**: Use `50.0` for trigger at midpoint, `0.0` for all post-trigger data, `100.0` for all pre-trigger data. Not a 0-1 float.

3. **Vertical range is peak-to-peak**: If you set `range=10.0`, the scope acquires ±5 V. The displayed voltage range is centered around `vertical_offset`.

4. **`enforce_realtime=True` prevents equivalent-time sampling**: For single-shot captures, always set this to `True`. Setting it to `False` allows the scope to use RIS (Random Interleaved Sampling) which requires repetitive signals.

5. **`fetch()` vs `read()`**: `fetch()` requires a prior `initiate()`. `read()` is a convenience that handles initiate internally. Use `fetch()` for streaming or complex acquisition sequences.

6. **Multi-record waveform interleaving**: When fetching multi-record, multi-channel data, waveforms are returned as a flat list. Use `wfm.channel` and `wfm.record` attributes to filter.

7. **Probe attenuation is NOT auto-detected**: Always set `probe_attenuation` to match your physical probe (1.0 for 1x, 10.0 for 10x). Incorrect values mean incorrect voltage readings.

8. **Input impedance affects bandwidth**: High-impedance (1 MΩ) has lower bandwidth than 50 Ω. Check your instrument's specifications for the bandwidth at each impedance setting.

9. **`auto_setup()` modifies all settings**: This is a convenience for quick checks but will override your carefully configured vertical, horizontal, and trigger settings. Don't use it in production test code.

10. **Timeout must account for trigger wait**: If using edge triggers, the `timeout` in `fetch()` must be long enough for the trigger event to occur plus acquisition time. Use `niscope.NISCOPE_VAL_MAX_TIME_NONE` for infinite wait if appropriate.

11. **Self-calibration temperature drift**: For highest accuracy, run `self_cal()` after the instrument has warmed up (typically 15-30 minutes after power-on) and whenever ambient temperature changes significantly.
