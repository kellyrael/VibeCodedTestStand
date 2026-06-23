# nidmm Reference — NI-DMM Python API

**Package**: `nidmm` (via `pip install nidmm`)
**Runtime**: NI-DMM driver (ni.com/downloads)
**Instruments**: PXI/PXIe Digital Multimeters (PXI-4065, PXI-4070, PXI-4071, PXI-4072, PXIe-4080/4081/4082)
**Current Version**: 1.4.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Session Creation](#session-creation)
2. [Key Enums](#key-enums)
3. [Essential Properties](#essential-properties)
4. [Core Methods](#core-methods)
5. [Canonical Examples](#canonical-examples)
6. [Temperature Measurements](#temperature-measurements)
7. [Waveform Acquisition](#waveform-acquisition)
8. [Cable Compensation (NI 4072/4082)](#cable-compensation)
9. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Session Creation

```python
import nidmm

# Basic session
with nidmm.Session("Dev1") as session:
    pass

# With simulation
options = "Simulate=1, DriverSetup=Model:4081; BoardType:PXIe"
with nidmm.Session("Dev1", options=options) as session:
    pass

# Reset on open
with nidmm.Session("Dev1", reset_device=True) as session:
    pass

# With ID query verification
with nidmm.Session("Dev1", id_query=True) as session:
    pass
```

### Session Constructor Parameters

| Parameter       | Type   | Default | Description                                         |
|-----------------|--------|---------|-----------------------------------------------------|
| `resource_name` | str    | Required| NI-DAQmx device name, DAQ::name, or IVI logical name |
| `id_query`      | bool   | False   | Verify device compatibility on open                 |
| `reset_device`  | bool   | False   | Reset device to known state on open                 |
| `options`       | dict/str | {}    | Session options (simulate, driver_setup, etc.)      |

---

## Key Enums

These are the enum classes you'll use most often. **Always use the enum, never raw strings or ints.**

### nidmm.Function

Controls the measurement function.

| Value                  | Description                              |
|------------------------|------------------------------------------|
| `DC_VOLTS`             | DC voltage measurement                   |
| `AC_VOLTS`             | AC voltage measurement (RMS)             |
| `DC_CURRENT`           | DC current measurement                   |
| `AC_CURRENT`           | AC current measurement (RMS)             |
| `TWO_WIRE_RES`         | 2-wire resistance measurement            |
| `FOUR_WIRE_RES`        | 4-wire resistance measurement            |
| `FREQ`                 | Frequency measurement                    |
| `PERIOD`               | Period measurement                       |
| `TEMPERATURE`          | Temperature measurement                  |
| `AC_VOLTS_DC_COUPLED`  | AC voltage with DC coupling              |
| `DIODE`                | Diode test                               |
| `WAVEFORM_VOLTAGE`     | Waveform acquisition (voltage)           |
| `WAVEFORM_CURRENT`     | Waveform acquisition (current)           |
| `CAPACITANCE`          | Capacitance measurement (NI 4072/4082)   |
| `INDUCTANCE`           | Inductance measurement (NI 4072/4082)    |

### nidmm.ApertureTimeUnits

| Value                | Description                                        |
|----------------------|----------------------------------------------------|
| `SECONDS`            | Aperture time in seconds                           |
| `POWER_LINE_CYCLES`  | Aperture time in PLCs (e.g., 1 PLC = 1/60s at 60Hz) |

### nidmm.AutoZero

| Value  | Description                                       |
|--------|---------------------------------------------------|
| `AUTO` | Driver chooses based on function and resolution   |
| `OFF`  | Disables AutoZero                                 |
| `ON`   | AutoZero before every measurement (most accurate) |
| `ONCE` | AutoZero once, reuse offset for subsequent        |

### nidmm.TriggerSource

| Value           | Description                                    |
|-----------------|------------------------------------------------|
| `IMMEDIATE`     | No trigger, measurement starts immediately     |
| `EXTERNAL`      | External trigger on AUX I/O connector          |
| `SOFTWARE_TRIG` | Software trigger via `send_software_trigger()`  |
| `INTERVAL`      | Internal interval timer                         |
| `PXI_TRIG0` through `PXI_TRIG7` | PXI trigger lines            |
| `PXI_STAR`      | PXI star trigger line                           |
| `LBR_TRIG1`     | Internal trigger line                           |

### nidmm.SampleTrigger

Same values as TriggerSource — controls the trigger between samples in multi-point acquisition.

### nidmm.AcquisitionStatus

| Value                         | Description                        |
|-------------------------------|------------------------------------|
| `RUNNING`                     | Acquisition in progress            |
| `FINISHED_WITH_BACKLOG`       | Done, data waiting to be read      |
| `FINISHED_WITH_NO_BACKLOG`    | Done, all data read                |
| `PAUSED`                      | Acquisition paused                 |
| `NO_ACQUISITION_IN_PROGRESS`  | No active acquisition              |

### nidmm.OperationMode

| Value      | Description                              |
|------------|------------------------------------------|
| `IVIDMM`   | Standard DMM measurements                |
| `WAVEFORM` | Waveform acquisition mode                |

### nidmm.DCNoiseRejection

| Value         | Description                            |
|---------------|----------------------------------------|
| `AUTO`        | Driver chooses based on function       |
| `NORMAL`      | All samples weighted equally           |
| `SECOND_ORDER`| Triangular weighting method            |
| `HIGH_ORDER`  | Bell-curve weighting method            |

### nidmm.ThermocoupleType

| Value | Description    |
|-------|----------------|
| `B`   | Type B         |
| `E`   | Type E         |
| `J`   | Type J         |
| `K`   | Type K         |
| `N`   | Type N         |
| `R`   | Type R         |
| `S`   | Type S         |
| `T`   | Type T         |

### nidmm.TransducerType

| Value            | Description       |
|------------------|-------------------|
| `THERMOCOUPLE`   | Thermocouple      |
| `THERMISTOR`     | Thermistor        |
| `TWO_WIRE_RTD`   | 2-wire RTD        |
| `FOUR_WIRE_RTD`  | 4-wire RTD        |

### nidmm.RTDType

| Value    | Description                          |
|----------|--------------------------------------|
| `CUSTOM` | Custom RTD with user coefficients    |
| `PT3750` | Pt 3750                              |
| `PT3851` | Pt 3851 (most common)                |
| `PT3911` | Pt 3911                              |
| `PT3916` | Pt 3916                              |
| `PT3920` | Pt 3920                              |
| `PT3928` | Pt 3928 (ITS-90)                     |

### nidmm.LCCalculationModel

| Value      | Description                                    |
|------------|------------------------------------------------|
| `AUTO`     | NI-DMM chooses algorithm based on function     |
| `SERIES`   | Series impedance model                         |
| `PARALLEL` | Parallel admittance model                      |

### nidmm.CableCompensationType

| Value            | Description                    |
|------------------|--------------------------------|
| `NONE`           | No cable compensation          |
| `OPEN`           | Open cable compensation        |
| `SHORT`          | Short cable compensation       |
| `OPEN_AND_SHORT` | Open and short compensation    |

---

## Essential Properties

### Measurement Configuration

| Property                | Type    | Description                                      |
|-------------------------|---------|--------------------------------------------------|
| `function`              | Enum    | DC_VOLTS, AC_VOLTS, TWO_WIRE_RES, etc.          |
| `range`                 | float   | Measurement range (volts, amps, ohms)            |
| `resolution_absolute`   | float   | Absolute resolution in measurement units         |
| `resolution_digits`     | float   | Resolution in digits (e.g., 5.5, 6.5)           |
| `aperture_time`         | float   | Integration time for measurement                 |
| `aperture_time_units`   | Enum    | SECONDS or POWER_LINE_CYCLES                     |
| `auto_zero`             | Enum    | AUTO, OFF, ON, ONCE                              |
| `auto_range_value`      | float   | Actual range value when auto-ranging (read-only) |
| `dc_noise_rejection`    | Enum    | DC noise rejection mode                          |
| `powerline_freq`        | float   | Powerline frequency (50 or 60 Hz)                |
| `input_resistance`      | float   | Input resistance of instrument                   |
| `number_of_averages`    | int     | Number of averages per measurement               |
| `offset_comp_ohms`      | int     | Offset compensated ohms (NI 4070+ only)          |

### AC Measurement Properties

| Property              | Type  | Description                             |
|-----------------------|-------|-----------------------------------------|
| `ac_min_freq`         | float | Minimum expected AC frequency (Hz)      |
| `ac_max_freq`         | float | Maximum expected AC frequency (Hz)      |
| `freq_voltage_range`  | float | Voltage range for frequency measurements|

### Triggering Properties

| Property         | Type      | Description                                  |
|------------------|-----------|----------------------------------------------|
| `trigger_source` | Enum      | IMMEDIATE, EXTERNAL, SOFTWARE_TRIG           |
| `trigger_delay`  | timedelta | Delay after trigger before measurement       |
| `trigger_count`  | int       | Number of triggers before returning to idle  |
| `sample_trigger` | Enum      | Trigger source for multi-point measurements  |
| `sample_count`   | int       | Number of measurements per trigger           |
| `sample_interval`| timedelta | Time between measurement cycles              |

### Temperature Measurement Properties

| Property                | Type  | Description                                    |
|-------------------------|-------|------------------------------------------------|
| `temp_transducer_type`  | Enum  | THERMOCOUPLE, THERMISTOR, TWO_WIRE_RTD, etc.  |
| `temp_tc_type`          | Enum  | Thermocouple type (J, K, T, E, etc.)           |
| `temp_tc_ref_junc_type` | Enum  | FIXED reference junction                       |
| `temp_tc_fixed_ref_junc`| float | Fixed reference junction temperature (°C)      |
| `temp_rtd_type`         | Enum  | RTD type (PT3750, PT3851, PT3911, etc.)        |
| `temp_rtd_res`          | float | RTD resistance at 0°C (ohms)                   |
| `temp_rtd_a`            | float | Callendar-Van Dusen A coefficient              |
| `temp_rtd_b`            | float | Callendar-Van Dusen B coefficient              |
| `temp_rtd_c`            | float | Callendar-Van Dusen C coefficient              |
| `temp_thermistor_type`  | Enum  | Thermistor type (44004, 44006, 44007)          |
| `temp_thermistor_a`     | float | Steinhart-Hart A coefficient                   |
| `temp_thermistor_b`     | float | Steinhart-Hart B coefficient                   |
| `temp_thermistor_c`     | float | Steinhart-Hart C coefficient                   |

### Waveform Properties

| Property            | Type   | Description                               |
|---------------------|--------|-------------------------------------------|
| `waveform_rate`     | float  | Waveform acquisition rate (S/s)           |
| `waveform_points`   | int    | Number of points in waveform acquisition  |
| `waveform_coupling` | Enum   | AC or DC coupling (NI 4070+ only)         |
| `operation_mode`    | Enum   | IVIDMM or WAVEFORM                        |

### LC Measurement Properties (NI 4072/4082)

| Property                      | Type  | Description                                 |
|-------------------------------|-------|---------------------------------------------|
| `cable_comp_type`             | Enum  | Cable compensation type                     |
| `lc_calculation_model`        | Enum  | Series or parallel impedance model          |
| `lc_number_meas_to_average`   | int   | LC measurements to average                  |
| `open_cable_comp_conductance` | float | Open cable compensation conductance         |
| `open_cable_comp_susceptance` | float | Open cable compensation susceptance         |
| `short_cable_comp_resistance` | float | Short cable compensation resistance         |
| `short_cable_comp_reactance`  | float | Short cable compensation reactance          |

### Read-Only / Status Properties

| Property                  | Type  | Description                              |
|---------------------------|-------|------------------------------------------|
| `instrument_model`        | str   | DMM model number                         |
| `serial_number`           | str   | Instrument serial number                 |
| `channel_count`           | int   | Number of channels supported             |
| `simulate`                | bool  | Whether simulation mode is enabled       |

---

## Core Methods

### Configuration Methods

```python
# Configure measurement with absolute resolution
session.configure_measurement_absolute(
    measurement_function=nidmm.Function.DC_VOLTS,
    range=10.0,
    resolution_absolute=0.0001
)

# Configure measurement with digits of resolution (most common)
session.configure_measurement_digits(
    measurement_function=nidmm.Function.DC_VOLTS,
    range=10.0,
    resolution_digits=6.5
)

# Configure multi-point acquisition
session.configure_multi_point(
    trigger_count=10,
    sample_count=100,
    sample_trigger=nidmm.SampleTrigger.IMMEDIATE,
    sample_interval=hightime.timedelta(seconds=0.001)
)

# Configure waveform acquisition (NI 4070+ and NI 4080+)
session.configure_waveform_acquisition(
    measurement_function=nidmm.Function.WAVEFORM_VOLTAGE,
    range=10.0,
    rate=50000.0,         # samples/sec
    waveform_points=1000
)

# Configure trigger
session.configure_trigger(
    trigger_source=nidmm.TriggerSource.IMMEDIATE,
    trigger_delay=hightime.timedelta(seconds=-1)  # auto
)
```

### Measurement Methods

```python
# Single measurement (configure + initiate + fetch in one call)
reading = session.read(maximum_time=hightime.timedelta(seconds=1.0))
# Returns: float — single measurement value

# Multi-point measurement (configure + initiate + fetch)
readings = session.read_multi_point(
    array_size=100,
    maximum_time=hightime.timedelta(seconds=10.0)
)
# Returns: array.array("d") — array of float64 measurements

# Fetch-only (use after initiate() for async operation)
reading = session.fetch(maximum_time=hightime.timedelta(seconds=1.0))
# Returns: float

# Fetch multi-point (after initiate)
readings = session.fetch_multi_point(
    array_size=100,
    maximum_time=hightime.timedelta(seconds=10.0)
)
# Returns: array.array("d")

# Waveform fetch (NI 4070+ and NI 4080+)
waveform = session.fetch_waveform(
    array_size=1000,
    maximum_time=hightime.timedelta(seconds=1.0)
)
# Returns: array.array("d")

# Waveform fetch into pre-allocated numpy array (for performance)
import numpy as np
waveform_array = np.zeros(1000, dtype=np.float64)
session.fetch_waveform_into(
    waveform_array=waveform_array,
    maximum_time=hightime.timedelta(seconds=1.0)
)
```

### Session Control Methods

```python
# Initiate measurement (use as context manager)
with session.initiate():
    readings = session.fetch_multi_point(array_size=100, maximum_time=hightime.timedelta(seconds=5.0))
# Automatically aborts when exiting context

# Abort ongoing measurement
session.abort()

# Read measurement status
(backlog, acquisition_state) = session.read_status()
# backlog: int — number of measurements in buffer
# acquisition_state: AcquisitionStatus enum

# Send software trigger
session.send_software_trigger()

# Reset to default state
session.reset()

# Reset with user defaults
session.reset_with_defaults()

# Disable — place in quiescent state
session.disable()
```

### Calibration Methods

```python
# Self-calibration (NI 4070+ and NI 4080+)
session.self_cal()

# Check if self-cal is supported
supported = session.get_self_cal_supported()

# Get calibration info
cal_date = session.get_cal_date_and_time(cal_type=0)  # 0=external, 1=self
last_temp = session.get_last_cal_temp(cal_type=0)
device_temp = session.get_dev_temp()
ext_cal_interval = session.get_ext_cal_recommended_interval()
```

### Cable Compensation Methods (NI 4072/4082)

```python
# Perform open cable compensation
conductance, susceptance = session.perform_open_cable_comp()

# Perform short cable compensation
resistance, reactance = session.perform_short_cable_comp()
```

### Configuration Import/Export

```python
# Export session configuration
session.export_attribute_configuration_file("config.nidmmconfig")
config_bytes = session.export_attribute_configuration_buffer()

# Import session configuration
session.import_attribute_configuration_file("config.nidmmconfig")
session.import_attribute_configuration_buffer(config_bytes)
```

---

## Canonical Examples

### Example 1: DC Voltage Measurement

The most fundamental DMM operation.

```python
import nidmm

def measure_dc_voltage(resource_name, range_v=10.0, digits=6.5):
    """Measure DC voltage with specified range and resolution."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.DC_VOLTS,
            range=range_v,
            resolution_digits=digits
        )
        reading = session.read()
        return reading

# Usage
voltage = measure_dc_voltage("PXI1Slot3")
print(f"Voltage: {voltage:.6f} V")
```

### Example 2: Multi-Point Acquisition

Acquire multiple measurements for statistical analysis.

```python
import nidmm

def multi_point_measurement(resource_name, count=100, range_v=10.0):
    """Acquire multiple DC voltage measurements."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.DC_VOLTS,
            range=range_v,
            resolution_digits=6.5
        )
        session.configure_multi_point(
            trigger_count=1,
            sample_count=count,
            sample_trigger=nidmm.SampleTrigger.IMMEDIATE
        )
        measurements = session.read_multi_point(array_size=count)
        return measurements

# Usage
readings = multi_point_measurement("PXI1Slot3", count=1000)
avg = sum(readings) / len(readings)
print(f"Average: {avg:.6f} V over {len(readings)} samples")
```

### Example 3: Resistance Measurement (4-Wire)

High-accuracy resistance measurement using Kelvin sensing.

```python
import nidmm

def measure_resistance_4wire(resource_name, range_ohms=10000.0):
    """Measure resistance using 4-wire (Kelvin) method."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.FOUR_WIRE_RES,
            range=range_ohms,
            resolution_digits=6.5
        )
        reading = session.read()
        return reading

# Usage
resistance = measure_resistance_4wire("PXI1Slot3", range_ohms=1000.0)
print(f"Resistance: {resistance:.4f} Ω")
```

### Example 4: AC Voltage with Frequency Range

```python
import nidmm

def measure_ac_voltage(resource_name, range_v=10.0, min_freq=20.0, max_freq=25000.0):
    """Measure AC voltage (RMS) within a specified frequency band."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.AC_VOLTS,
            range=range_v,
            resolution_digits=5.5
        )
        session.ac_min_freq = min_freq
        session.ac_max_freq = max_freq
        reading = session.read()
        return reading

# Usage
ac_rms = measure_ac_voltage("PXI1Slot3", range_v=1.0, min_freq=50.0, max_freq=10000.0)
print(f"AC Voltage: {ac_rms:.6f} Vrms")
```

### Example 5: Continuous Fetch with Status Monitoring

```python
import nidmm

def continuous_measurement(resource_name, total_samples=1000):
    """Acquire measurements using initiate/fetch pattern with status monitoring."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.DC_VOLTS,
            range=10.0,
            resolution_digits=5.5
        )
        session.configure_multi_point(
            trigger_count=1,
            sample_count=total_samples,
            sample_trigger=nidmm.SampleTrigger.IMMEDIATE
        )

        all_readings = []
        with session.initiate():
            while True:
                backlog, status = session.read_status()
                if backlog > 0:
                    batch = session.fetch_multi_point(
                        array_size=backlog
                    )
                    all_readings.extend(batch)
                if status == nidmm.AcquisitionStatus.FINISHED_WITH_NO_BACKLOG:
                    break

        return all_readings
```

---

## Temperature Measurements

### Thermocouple Measurement

```python
import nidmm

def measure_temperature_thermocouple(resource_name, tc_type=nidmm.ThermocoupleType.K):
    """Measure temperature using a thermocouple."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.TEMPERATURE,
            range=1.0,  # ignored for temperature
            resolution_digits=5.5
        )
        session.temp_transducer_type = nidmm.TransducerType.THERMOCOUPLE
        session.configure_thermocouple(
            thermocouple_type=tc_type,
            reference_junction_type=nidmm.ThermocoupleReferenceJunctionType.FIXED
        )
        session.temp_tc_fixed_ref_junc = 25.0  # Reference junction temp in °C

        reading = session.read()
        return reading

# Usage
temp = measure_temperature_thermocouple("PXI1Slot3")
print(f"Temperature: {temp:.2f} °C")
```

### RTD Measurement

```python
import nidmm

def measure_temperature_rtd(resource_name, rtd_type=nidmm.RTDType.PT3851, resistance=100.0):
    """Measure temperature using an RTD (4-wire)."""
    with nidmm.Session(resource_name) as session:
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.TEMPERATURE,
            range=1.0,
            resolution_digits=6.5
        )
        session.temp_transducer_type = nidmm.TransducerType.FOUR_WIRE_RTD
        session.configure_rtd_type(
            rtd_type=rtd_type,
            rtd_resistance=resistance  # Ohms at 0°C
        )

        reading = session.read()
        return reading

# Usage
temp = measure_temperature_rtd("PXI1Slot3")
print(f"Temperature: {temp:.3f} °C")
```

---

## Waveform Acquisition

For high-speed digitization of voltage or current signals (NI 4070+ and NI 4080+).

```python
import nidmm
import time

def acquire_waveform(resource_name, rate=50000.0, points=10000, range_v=10.0):
    """Acquire a voltage waveform at the specified sample rate."""
    with nidmm.Session(resource_name) as session:
        session.configure_waveform_acquisition(
            measurement_function=nidmm.Function.WAVEFORM_VOLTAGE,
            range=range_v,
            rate=rate,
            waveform_points=points
        )

        with session.initiate():
            while True:
                time.sleep(0.1)
                backlog, status = session.read_status()
                if status == nidmm.AcquisitionStatus.FINISHED_WITH_NO_BACKLOG:
                    break
                if backlog > 0:
                    waveform = session.fetch_waveform(array_size=backlog)
                    # Process waveform data...

        return waveform

# Usage with numpy for performance
import numpy as np

def acquire_waveform_numpy(resource_name, rate=50000.0, points=10000):
    """Acquire waveform directly into a numpy array."""
    with nidmm.Session(resource_name) as session:
        session.configure_waveform_acquisition(
            measurement_function=nidmm.Function.WAVEFORM_VOLTAGE,
            range=10.0,
            rate=rate,
            waveform_points=points
        )
        waveform_array = np.zeros(points, dtype=np.float64)
        with session.initiate():
            session.fetch_waveform_into(waveform_array)
        return waveform_array
```

---

## Cable Compensation

For capacitance and inductance measurements on NI 4072/4082, cable compensation
corrects for parasitic effects of test leads.

```python
import nidmm

def measure_capacitance_compensated(resource_name, range_f=0.000001):
    """Measure capacitance with open/short cable compensation."""
    with nidmm.Session(resource_name) as session:
        # Perform open cable compensation (probes open, no DUT)
        conductance, susceptance = session.perform_open_cable_comp()
        session.open_cable_comp_conductance = conductance
        session.open_cable_comp_susceptance = susceptance

        # Perform short cable compensation (probes shorted together)
        resistance, reactance = session.perform_short_cable_comp()
        session.short_cable_comp_resistance = resistance
        session.short_cable_comp_reactance = reactance

        # Enable compensation
        session.cable_comp_type = nidmm.CableCompensationType.OPEN_AND_SHORT

        # Now measure
        session.configure_measurement_digits(
            measurement_function=nidmm.Function.CAPACITANCE,
            range=range_f,
            resolution_digits=5.5
        )
        reading = session.read()
        return reading
```

---

## Driver-Specific Gotchas

1. **`read()` vs `fetch()`**: `read()` is a convenience method that combines `initiate()` + `fetch()`. Use `fetch()` when you need to call `initiate()` separately (e.g., for multi-point with status monitoring).

2. **Resolution as digits**: Use `configure_measurement_digits()` with values like `3.5`, `4.5`, `5.5`, `6.5`, `7.5`. These correspond to the number of significant digits. Higher digits = slower but more accurate.

3. **Aperture time vs resolution**: You can set resolution via `resolution_digits` (simpler) or `aperture_time` (more control). Setting one overrides the other. Don't mix them.

4. **`read_multi_point()` returns `array.array("d")`**: Not a list. Use `list()` to convert if needed, or index directly. For numpy, use `np.frombuffer()`.

5. **Auto-zero overhead**: `AutoZero.ON` doubles measurement time since the DMM takes an internal reference measurement before each reading. Use `ONCE` for multi-point to zero only on the first measurement.

6. **Temperature requires transducer configuration**: Setting `function = TEMPERATURE` is not enough. You must also set `temp_transducer_type` and configure the specific transducer (thermocouple type, RTD type, etc.).

7. **Waveform mode is a separate mode**: Waveform functions (`WAVEFORM_VOLTAGE`, `WAVEFORM_CURRENT`) use a different acquisition engine than standard DMM measurements. Use `configure_waveform_acquisition()` instead of `configure_measurement_digits()`.

8. **NI 4065 limitations**: No self-calibration, no waveform acquisition, no cable compensation. Check `get_self_cal_supported()` before calling `self_cal()`.

9. **powerline_freq affects PLC-based aperture**: If you use `POWER_LINE_CYCLES` for aperture time units, ensure `powerline_freq` matches your AC power frequency (50 or 60 Hz). Incorrect values degrade noise rejection.

10. **Multi-point timeout**: The `maximum_time` in `read_multi_point()` is the total timeout for all samples, not per-sample. Calculate appropriately: `timeout = sample_count * (aperture_time + overhead)`.

11. **Self-test resets the device**: Calling `self_test()` resets the instrument. Don't call it in the middle of a test sequence.
