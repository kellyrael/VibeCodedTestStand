# nidcpower Reference — NI-DCPower Python API

**Package**: `nidcpower` (via `pip install nidcpower`)
**Runtime**: NI-DCPower driver (ni.com/downloads)
**Instruments**: PXIe-4135, PXIe-4136/4137, PXIe-4138/4139, PXIe-4140/4141, PXIe-4143/4144,
PXIe-4145, PXIe-4147, PXIe-4151, PXIe-4154, PXIe-4162/4163, PXI-4110, PXIe-4112/4113, PXI-4130, PXI-4132
**Current Version**: 1.5.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Session Creation](#session-creation)
2. [Key Enums](#key-enums)
3. [Essential Properties](#essential-properties)
4. [Core Methods](#core-methods)
5. [Measurement Data Structures](#measurement-data-structures)
6. [Canonical Examples](#canonical-examples)
7. [Advanced Sequences](#advanced-sequences)
8. [LCR Measurements](#lcr-measurements)
9. [Electronic Load / Sinking](#electronic-load--sinking)
10. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Session Creation

```python
import nidcpower

# Basic — single channel
with nidcpower.Session(resource_name="PXI1Slot2/0") as session:
    pass

# Multi-channel — channels in resource_name (v1.4+)
with nidcpower.Session(resource_name="PXI1Slot2/0,PXI1Slot2/1") as session:
    pass

# Legacy — channels parameter (still supported)
with nidcpower.Session(resource_name="PXI1Slot2", channels="0,1") as session:
    pass

# Simulation
options = "Simulate=1, DriverSetup=Model:4162; BoardType:PXIe"
with nidcpower.Session(resource_name="PXI1Slot2/0", options=options) as session:
    pass

# Reset on open
with nidcpower.Session(resource_name="PXI1Slot2/0", reset=True) as session:
    pass
```

### Independent Channels

When you initialize with independent channels (the default in newer versions), each channel
can be configured and initiated independently. You can initiate a subset while others remain
in the Uncommitted state.

---

## Key Enums

These are the enum classes you'll use most often. **Always use the enum, never raw strings or ints.**

### nidcpower.OutputFunction
Controls what the SMU sources.

| Value                  | Description                                    |
|------------------------|------------------------------------------------|
| `DC_VOLTAGE`           | Source constant DC voltage                     |
| `DC_CURRENT`           | Source constant DC current                     |
| `PULSE_VOLTAGE`        | Source pulsed voltage                          |
| `PULSE_CURRENT`        | Source pulsed current                          |
| `CONSTANT_RESISTANCE`  | Simulate constant resistance (v1.5+)           |
| `CONSTANT_POWER`       | Simulate constant power load (v1.5+)           |

### nidcpower.SourceMode
Controls how source values are applied.

| Value          | Description                                              |
|----------------|----------------------------------------------------------|
| `SINGLE_POINT` | One source value at a time; change via property writes   |
| `SEQUENCE`     | Hardware-timed sequence of source values                 |

### nidcpower.MeasureWhen
Controls when measurements are acquired.

| Value                                 | Description                                              |
|---------------------------------------|----------------------------------------------------------|
| `AUTOMATICALLY_AFTER_SOURCE_COMPLETE` | Measure after each source settling (most common)         |
| `ON_DEMAND`                           | Measure only when `measure()` or `measure_multiple()` called |
| `ON_MEASURE_TRIGGER`                  | Measure on external trigger                              |

### nidcpower.Sense
Controls sense mode (remote vs local).

| Value       | Description                                      |
|-------------|--------------------------------------------------|
| `LOCAL`     | 2-wire sensing at the output terminals           |
| `REMOTE`    | 4-wire Kelvin sensing at the DUT                 |

### nidcpower.TransientResponse
Controls output transient response speed.

| Value    | Description                       |
|----------|-----------------------------------|
| `NORMAL` | Balanced stability and speed      |
| `FAST`   | Faster settling, less stability   |
| `SLOW`   | Maximum stability                 |
| `CUSTOM` | User-defined compensation         |

### nidcpower.ComplianceLimitSymmetry

| Value        | Description                                              |
|--------------|----------------------------------------------------------|
| `SYMMETRIC`  | Same positive and negative limit (use `current_limit`)   |
| `ASYMMETRIC` | Different pos/neg limits (use `current_limit_high/low`)  |

### nidcpower.Event
Events for `wait_for_event()` and event-based triggering.

| Value                     | Description                      |
|---------------------------|----------------------------------|
| `SOURCE_COMPLETE`         | Source output has settled         |
| `MEASURE_COMPLETE`        | Measurement acquisition done     |
| `SEQUENCE_ITERATION_COMPLETE` | One sequence step done       |
| `SEQUENCE_ENGINE_DONE`    | Entire sequence finished         |
| `PULSE_COMPLETE`          | Pulse output complete            |
| `READY_FOR_PULSE_TRIGGER` | Ready for next pulse trigger     |

### nidcpower.CurrentLimitBehavior

| Value      | Description                                                 |
|------------|-------------------------------------------------------------|
| `REGULATE` | Limit current while maintaining output (constant current)   |
| `TRIP`     | Disable output entirely when limit is reached               |

### nidcpower.AutoZero

| Value  | Description                                       |
|--------|---------------------------------------------------|
| `OFF`  | No auto zero                                      |
| `ONCE` | Zero after first measurement, reuse for subsequent |
| `ON`   | Zero before every measurement (most accurate)     |

### nidcpower.ApertureTimeUnits

| Value                | Description         |
|----------------------|---------------------|
| `SECONDS`            | Time in seconds     |
| `POWER_LINE_CYCLES`  | Time in PLCs (e.g., 1 PLC = 1/60s at 60Hz) |

### nidcpower.InstrumentMode (for LCR-capable devices)

| Value          | Description           |
|----------------|-----------------------|
| `SMU_PS`       | Standard SMU mode     |
| `LCR`          | LCR measurement mode  |

### nidcpower.ConductionVoltageMode (for electronic loads)

| Value       | Description                                   |
|-------------|-----------------------------------------------|
| `AUTOMATIC` | Enabled for DC_CURRENT/CONSTANT_POWER, disabled otherwise |
| `ENABLED`   | Always enabled                                 |
| `DISABLED`  | Always disabled                                |

---

## Essential Properties

### Source Configuration

| Property                    | Type    | Description                                     |
|-----------------------------|---------|-------------------------------------------------|
| `source_mode`               | Enum    | SINGLE_POINT or SEQUENCE                        |
| `output_function`           | Enum    | DC_VOLTAGE, DC_CURRENT, PULSE_*, CONSTANT_*     |
| `voltage_level`             | float   | DC voltage to source (volts)                    |
| `current_level`             | float   | DC current to source (amps)                     |
| `voltage_level_range`       | float   | Voltage range (sets resolution/accuracy)        |
| `current_limit`             | float   | Current compliance limit (amps, symmetric)      |
| `current_limit_range`       | float   | Range for current limit                         |
| `current_limit_high`        | float   | Positive compliance limit (asymmetric)          |
| `current_limit_low`         | float   | Negative compliance limit (asymmetric)          |
| `voltage_limit`             | float   | Voltage compliance limit (current source mode)  |
| `voltage_limit_range`       | float   | Range for voltage limit                         |
| `voltage_level_autorange`   | bool    | Enable auto-ranging for voltage                 |
| `current_limit_autorange`   | bool    | Enable auto-ranging for current limit           |
| `source_delay`              | timedelta | Delay after source change before measuring (use `hightime.timedelta`) |
| `transient_response`        | Enum    | NORMAL, FAST, SLOW, CUSTOM                      |
| `output_enabled`            | bool    | Enable/disable channel output                   |

### Measurement Configuration

| Property                         | Type   | Description                                       |
|----------------------------------|--------|---------------------------------------------------|
| `measure_when`                   | Enum   | AUTOMATICALLY_AFTER_SOURCE_COMPLETE, ON_DEMAND, ON_MEASURE_TRIGGER |
| `aperture_time`                  | float  | Integration time for measurement                  |
| `aperture_time_units`            | Enum   | SECONDS or POWER_LINE_CYCLES                      |
| `measure_record_length`          | int    | Number of measurements to acquire                 |
| `measure_record_length_is_finite`| bool   | True = stop after N, False = continuous            |
| `autorange`                      | bool   | Enable measurement autoranging                    |
| `sense`                          | Enum   | LOCAL or REMOTE (Kelvin)                           |
| `auto_zero`                      | Enum   | OFF, ONCE, ON                                     |

### Read-Only / Status Properties

| Property                    | Type    | Description                                  |
|-----------------------------|---------|----------------------------------------------|
| `fetch_backlog`             | int     | Number of measurements available to fetch    |
| `channel_count`             | int     | Total channels in session                    |
| `measure_record_delta_time` | float   | Time between measurements (after commit)     |
| `in_compliance`             | bool    | Whether channel is currently in compliance   |

---

## Core Methods

### Measurement Methods

```python
# fetch_multiple — Get N measurements from buffer (use with AUTOMATICALLY_AFTER_SOURCE_COMPLETE)
measurements = session.fetch_multiple(count=10, timeout=5.0)
# Returns list of named tuples: (voltage, current, in_compliance)

# measure_multiple — On-demand measurement (use with MeasureWhen.ON_DEMAND)
measurements = session.measure_multiple()
# Returns list of named tuples: (voltage, current, in_compliance)
# Note: in_compliance may be None for measure_multiple

# measure — Single on-demand measurement of one type
voltage = session.measure(nidcpower.MeasurementTypes.VOLTAGE)
current = session.measure(nidcpower.MeasurementTypes.CURRENT)

# Channel-specific fetch
measurements = session.channels["0"].fetch_multiple(count=10, timeout=5.0)
```

### Session Control Methods

```python
# commit — Apply settings, transition to Committed state
session.commit()

# initiate — Start sourcing/measuring, transition to Running state (use as context manager)
with session.initiate():
    measurements = session.fetch_multiple(count=10)
# Automatically aborts when exiting context

# abort — Stop sourcing/measuring (called automatically by initiate context manager)
session.abort()

# reset — Reset device to defaults, disable output
session.reset()

# reset_device — Hard reset (like Measurement & Automation Explorer reset)
session.reset_device()
```

### Utility Methods

```python
# Get channel names
channel_indices = f"0-{session.channel_count - 1}"
channel_names = session.get_channel_names(channel_indices)

# Wait for event
session.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=5.0)

# Query output state
is_sourcing_v = session.channels["0"].query_output_state(nidcpower.OutputStates.VOLTAGE)

# Export/import configuration
session.export_attribute_configuration_file("config.nidcpowerconfig")
session.import_attribute_configuration_file("config.nidcpowerconfig")

# Self-calibration
session.self_cal()

# Self-test (implicitly resets)
session.self_test()  # Raises SelfTestError on failure
```

---

## Measurement Data Structures

`fetch_multiple()` and `measure_multiple()` return lists of named tuples:

```python
# Standard measurement
measurement.voltage      # float — measured voltage
measurement.current      # float — measured current
measurement.in_compliance  # bool — True if within compliance limits (may be None for measure_multiple)

# LCR measurement (from fetch_multiple_lcr / measure_multiple_lcr)
measurement.vdc                  # float — DC bias voltage
measurement.idc                  # float — DC bias current
measurement.stimulus_frequency   # float — stimulus frequency
measurement.ac_voltage           # complex — AC voltage (real + imaginary)
measurement.ac_current           # complex — AC current
measurement.z                    # complex — impedance
measurement.z_magnitude_and_phase  # tuple — (magnitude, phase)
measurement.y                    # complex — admittance
measurement.series_lcr           # named tuple — (inductance, capacitance, resistance)
measurement.parallel_lcr         # named tuple — (inductance, capacitance, resistance)
measurement.d                    # float — dissipation factor
measurement.q                    # float — quality factor
measurement.measurement_mode     # InstrumentMode enum
measurement.dc_in_compliance     # bool
measurement.ac_in_compliance     # bool
measurement.unbalanced           # bool
```

---

## Canonical Examples

### Example 1: Source DC Voltage, Measure Current

The most fundamental pattern for PMIC rail validation.

```python
import nidcpower

def source_voltage_measure_current(resource_name, voltage, current_limit=0.1, count=10):
    """Source a DC voltage and measure the resulting current draw."""
    with nidcpower.Session(resource_name=resource_name) as session:
        # Configure source
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.voltage_level = voltage
        session.voltage_level_range = voltage  # or use autorange
        session.current_limit = current_limit
        session.current_limit_range = current_limit

        # Configure measurement
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE

        # Source and measure
        with session.initiate():
            measurements = session.fetch_multiple(count=count)

        return measurements
```

### Example 2: Source-Delay-Measure with On-the-Fly Updates

Change source voltage between measurements without re-initiating.

```python
import nidcpower
import hightime

def source_delay_measure(resource_name, voltages, delay=0.01, current_limit=0.06):
    """Source multiple voltages sequentially, measuring after each."""
    with nidcpower.Session(resource_name=resource_name) as session:
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = current_limit
        session.voltage_level_range = max(voltages)
        session.current_limit_range = current_limit
        session.source_delay = hightime.timedelta(seconds=delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE

        session.voltage_level = voltages[0]
        results = []

        with session.initiate():
            channel_indices = f"0-{session.channel_count - 1}"
            channels = session.get_channel_names(channel_indices)
            for channel_name in channels:
                for v in voltages:
                    session.voltage_level = v  # on-the-fly update
                    m = session.channels[channel_name].fetch_multiple(count=1, timeout=5.0)
                    results.append({"voltage_set": v, "channel": channel_name, "measurement": m[0]})

        return results
```

### Example 3: Measure Record (Continuous Acquisition)

Acquire a fixed number of measurements at the hardware's maximum rate.

```python
import nidcpower

def measure_record(resource_name, voltage, record_length=100):
    """Acquire a record of measurements at maximum rate."""
    with nidcpower.Session(resource_name=resource_name) as session:
        session.measure_record_length = record_length
        session.measure_record_length_is_finite = True
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.voltage_level = voltage

        session.commit()
        effective_rate = session.measure_record_delta_time
        print(f"Effective measurement rate: {1.0 / effective_rate:.1f} S/s")

        all_measurements = []
        with session.initiate():
            channel_indices = f"0-{session.channel_count - 1}"
            channels = session.get_channel_names(channel_indices)
            for channel_name in channels:
                samples_acquired = 0
                channel_data = []
                while samples_acquired < record_length:
                    batch = session.channels[channel_name].fetch_multiple(
                        count=session.fetch_backlog
                    )
                    channel_data.extend(batch)
                    samples_acquired += len(batch)
                all_measurements.append({
                    "channel": channel_name,
                    "measurements": channel_data
                })

        return all_measurements
```

### Example 4: Multi-Rail PMIC Validation

Configure multiple channels as independent supply rails for PMIC testing.

```python
import nidcpower

def pmic_rail_validation(resource_name, rails):
    """
    Validate PMIC output rails.
    
    Args:
        resource_name: e.g. "PXI1Slot2/0,PXI1Slot2/1,PXI1Slot2/2"
        rails: list of dicts with keys: channel, voltage, current_limit, name
               e.g. [{"channel": "0", "voltage": 3.3, "current_limit": 0.5, "name": "VDDIO"},
                      {"channel": "1", "voltage": 1.8, "current_limit": 0.3, "name": "VDDC"}]
    """
    with nidcpower.Session(resource_name=resource_name) as session:
        # Configure each rail independently
        for rail in rails:
            ch = session.channels[rail["channel"]]
            ch.source_mode = nidcpower.SourceMode.SINGLE_POINT
            ch.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            ch.voltage_level = rail["voltage"]
            ch.current_limit = rail["current_limit"]
            ch.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE

        # Initiate all channels, measure each
        results = {}
        with session.initiate():
            for rail in rails:
                ch = session.channels[rail["channel"]]
                measurements = ch.fetch_multiple(count=10, timeout=5.0)
                avg_current = sum(m.current for m in measurements) / len(measurements)
                all_compliant = all(m.in_compliance for m in measurements)
                results[rail["name"]] = {
                    "voltage_set": rail["voltage"],
                    "avg_current_mA": avg_current * 1000,
                    "in_compliance": all_compliant,
                    "measurements": measurements,
                }

        return results
```

---

## Advanced Sequences

Hardware-timed voltage/current sweeps using the sequence engine.

```python
import nidcpower
import hightime

def voltage_sweep_sequence(resource_name, v_start, v_stop, steps, source_delay=0.01):
    """Hardware-timed voltage sweep using advanced sequences."""
    with nidcpower.Session(resource_name=resource_name) as session:
        session.source_mode = nidcpower.SourceMode.SEQUENCE
        session.voltage_level_autorange = True
        session.current_limit_autorange = True
        session.source_delay = hightime.timedelta(seconds=source_delay)

        # Define sequence properties
        properties_used = ["output_function", "voltage_level"]
        session.create_advanced_sequence(
            sequence_name="v_sweep",
            property_names=properties_used,
            set_as_active_sequence=True,
        )

        # Create steps
        v_step = (v_stop - v_start) / (steps - 1)
        for i in range(steps):
            session.create_advanced_sequence_step(set_as_active_step=False)
            session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            session.voltage_level = v_start + v_step * i

        # Calculate timeout
        aperture_time = session.aperture_time
        timeout = hightime.timedelta(seconds=((source_delay + aperture_time) * steps + 1.0))

        # Run and fetch
        with session.initiate():
            channel_indices = f"0-{session.channel_count - 1}"
            channels = session.get_channel_names(channel_indices)
            results = {
                name: session.channels[name].fetch_multiple(steps, timeout=timeout)
                for name in channels
            }

        session.delete_advanced_sequence(sequence_name="v_sweep")
        return results
```

---

## LCR Measurements

For LCR-capable devices (e.g., PXIe-4190).

```python
import nidcpower

def lcr_impedance_measurement(resource_name, frequency=10_000.0, voltage_rms=0.5):
    """Measure impedance using LCR mode."""
    with nidcpower.Session(resource_name=resource_name) as session:
        session.instrument_mode = nidcpower.InstrumentMode.LCR
        session.lcr_stimulus_function = nidcpower.LCRStimulusFunction.VOLTAGE
        session.lcr_frequency = frequency
        session.lcr_voltage_amplitude = voltage_rms
        session.lcr_dc_bias_source = nidcpower.LCRDCBiasSource.VOLTAGE
        session.lcr_dc_bias_voltage_level = 0.0
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE

        with session.initiate():
            session.wait_for_event(
                event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=5.0
            )
            measurements = session.measure_multiple_lcr()

        return measurements
```

---

## Electronic Load / Sinking

For dedicated electronic load devices (PXIe-4051) and SMUs with e-load capability (v1.5+).

### Critical Differences from SMU Sourcing

Dedicated electronic loads behave differently from SMUs acting as loads:

| Property | SMU (sourcing) | Dedicated E-Load (sinking) |
|---|---|---|
| `current_level` sign | Negative = sinking | **Positive** = sinking (device sinks by design) |
| Voltage compliance | `voltage_limit` + `voltage_limit_range` | **Not configurable** — `voltage_limit` is fixed at Infinity on PXIe-4051 |
| Voltage autorange | `voltage_level_autorange` (for source level) | **Not supported** — no voltage limit ranging on PXIe-4051 |
| Current autorange | `current_limit_autorange` (for limit) | `current_level_autorange` (for source level) |
| `autorange` (measurement) | Supported on most SMUs | **Not supported** on dedicated e-loads — use `current_level_autorange` only |
| `conduction_voltage_mode` | Set for sinking modes | Not needed on dedicated e-loads |

### Example: Dedicated Electronic Load (PXIe-4051)

```python
import nidcpower
import hightime

def sink_dc_current(resource_name, current_level, source_delay=0.001):
    """Configure a dedicated e-load to sink DC current."""
    with nidcpower.Session(resource_name=resource_name) as session:
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_CURRENT
        session.current_level = abs(current_level)   # POSITIVE — e-load sinks by design
        # PXIe-4051: voltage_limit is fixed at Infinity — do NOT set it
        # PXIe-4051: voltage_limit_range and voltage_limit_autorange are NOT supported
        session.current_level_autorange = True
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        # Do NOT set session.autorange — not supported on dedicated e-loads
        # Do NOT set session.conduction_voltage_mode — not needed on dedicated e-loads

        with session.initiate():
            measurements = session.fetch_multiple(count=10, timeout=5.0)

        return measurements
```

### Example: SMU as Electronic Load (PXIe-4162/4163)

When using an SMU in sinking mode (not a dedicated e-load), the sign convention differs:

```python
import nidcpower
import hightime

def smu_sink_dc_current(resource_name, current_level, voltage_limit, source_delay=0.001):
    """Configure an SMU to sink DC current (electronic load mode)."""
    with nidcpower.Session(resource_name=resource_name) as session:
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_CURRENT
        session.current_level = -abs(current_level)  # NEGATIVE — SMU needs sign to indicate sinking
        session.voltage_limit = voltage_limit
        session.voltage_limit_range = voltage_limit
        session.current_level_autorange = True
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.conduction_voltage_mode = nidcpower.ConductionVoltageMode.AUTOMATIC
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE

        with session.initiate():
            measurements = session.fetch_multiple(count=10, timeout=5.0)

        return measurements
```

---

## Driver-Specific Gotchas

1. **`hightime.timedelta` for source_delay**: The `source_delay` property expects a `hightime.timedelta` object, not a plain float. Import `hightime` and use `hightime.timedelta(seconds=0.01)`.

2. **Channel addressing changed in v1.4+**: Older code uses `Session(resource_name="PXI1Slot2", channels="0")`. Newer code puts the channel in the resource name: `Session(resource_name="PXI1Slot2/0")`. Both work, but the newer style is preferred.

3. **`fetch_multiple` vs `measure_multiple`**: Use `fetch_multiple` when `measure_when = AUTOMATICALLY_AFTER_SOURCE_COMPLETE` (it reads from the measurement buffer). Use `measure_multiple` when `measure_when = ON_DEMAND` (it triggers an immediate measurement). Using the wrong one returns stale data or errors.

4. **`commit()` before reading computed properties**: Properties like `measure_record_delta_time` are only valid after calling `commit()`. Reading them in the Uncommitted state returns incorrect values.

5. **Output stays on after `close()`**: If power output is enabled when the session closes, the channels remain in their existing state and continue providing power. Call `session.reset()` before closing if you want to ensure outputs are off, or set `output_enabled = False` per channel.

6. **Thread safety with independent channels**: You can make concurrent calls to a session from multiple threads, but the session serializes them. Per-channel operations may run in parallel but this is not guaranteed.

7. **Self-test resets the device**: Calling `self_test()` implicitly calls `reset()`. Don't call it in the middle of a test sequence.

8. **PXIe-4162/4163 self-test requires all channels**: You must initialize with all channels to run self-test on these models. Subset self-test is not supported.

9. **Constant resistance/power modes (v1.5+)**: `CONSTANT_RESISTANCE` and `CONSTANT_POWER` are new `OutputFunction` values. When using `DC_CURRENT` or `CONSTANT_POWER`, enable conduction voltage via `conduction_voltage_mode`. When using `DC_VOLTAGE` or `CONSTANT_RESISTANCE`, disable it.

10. **Configuration export format**: `export_attribute_configuration_file()` uses `.nidcpowerconfig` extension by default.

11. **Dedicated e-load current sign**: Dedicated electronic loads (e.g., PXIe-4051) sink current by design. Set `current_level` to a **positive** value (the magnitude to draw). Setting it negative will cause an error or unexpected behavior. Only SMUs acting as loads (e.g., PXIe-4162/4163) use negative `current_level` to indicate sinking direction.

12. **Dedicated e-loads (PXIe-4051) have very limited property support**: `autorange`, `voltage_limit_autorange`, `voltage_limit_range`, and finite `voltage_limit` values are all **not supported**. The `voltage_limit` is fixed at `Infinity`. Only `current_level_autorange` is supported for autoranging. Do not set `voltage_limit` or any voltage-range properties on a PXIe-4051.

13. **`voltage_level_autorange` vs `voltage_limit_range`**: When an instrument is in `DC_CURRENT` mode (e-load), the voltage side is a **limit** (compliance), not a **level** (source). On SMUs, use `voltage_limit_range` (explicit value). On dedicated e-loads (PXIe-4051), do not set any voltage range property — it is not supported. Using `voltage_level_autorange` in current-source mode will error because there is no voltage level to range.
