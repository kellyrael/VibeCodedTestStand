# nidigital Reference — NI-Digital Pattern Driver Python API

**Package**: `nidigital` (via `pip install nidigital`)
**Runtime**: NI-Digital Pattern Driver (ni.com/downloads)
**Instruments**: PXIe-6570, PXIe-6571 Digital Pattern Instruments
**Current Version**: 1.4.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Session Creation](#session-creation)
2. [Key Enums](#key-enums)
3. [Essential Properties](#essential-properties)
4. [Core Methods](#core-methods)
5. [Data Structures](#data-structures)
6. [Canonical Examples](#canonical-examples)
7. [PPMU (Per-Pin Parametric Measurement Unit)](#ppmu)
8. [Digital Patterns](#digital-patterns)
9. [History RAM](#history-ram)
10. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Session Creation

```python
import nidigital

# Basic session — single instrument
with nidigital.Session(resource_name="PXI1Slot2") as session:
    pass

# Multiple instruments (must be same model, same chassis)
with nidigital.Session(resource_name="PXI1Slot2,PXI1Slot3") as session:
    pass

# Reset on open
with nidigital.Session(resource_name="PXI1Slot2", reset_device=True) as session:
    pass
```

### Session Constructor Parameters

| Parameter       | Type   | Default  | Description                                          |
|-----------------|--------|----------|------------------------------------------------------|
| `resource_name` | str    | Required | Device name(s), comma-separated for multiple         |
| `id_query`      | bool   | False    | Verify device compatibility                          |
| `reset_device`  | bool   | False    | Reset to known state on open                         |
| `options`       | dict/str | {}     | Session options (simulate, driver_setup, etc.)       |

### Repeated Capability Containers

The Session object provides these containers for accessing subsets of resources:

```python
session.channels["PXI1Slot2/0,PXI1Slot2/1"]  # Access specific channels
session.pins["DUT_CLK,DUT_DATA"]              # Access by pin name (requires pin map)
session.sites[0, 1, 2]                        # Access specific test sites
session.instruments["PXI1Slot2"]              # Access specific instrument
session.pattern_opcode_events[0]              # Pattern opcode events
session.conditional_jump_triggers[0]          # Conditional jump triggers
```

---

## Key Enums

### nidigital.SelectedFunction

Controls what mode a pin is in.

| Value        | Description                                    |
|--------------|------------------------------------------------|
| `DIGITAL`    | Pattern sequencer controls pin (pattern mode)  |
| `PPMU`       | PPMU controls pin (DC parametric mode)         |
| `OFF`        | Pin driver off, active load disabled           |
| `DISCONNECT` | Pin electrically disconnected from DUT         |

### nidigital.PPMUOutputFunction

| Value     | Description                              |
|-----------|------------------------------------------|
| `VOLTAGE` | Force voltage, measure current           |
| `CURRENT` | Force current, measure voltage           |

### nidigital.PPMUMeasurementType

| Value     | Description         |
|-----------|---------------------|
| `CURRENT` | Measure current     |
| `VOLTAGE` | Measure voltage     |

### nidigital.PPMUApertureTimeUnits

| Value     | Description              |
|-----------|--------------------------|
| `SECONDS` | Aperture time in seconds |

### nidigital.PPMUCurrentLimitBehavior

| Value      | Description                              |
|------------|------------------------------------------|
| `REGULATE` | Regulate output current to specified limit|

### nidigital.PinState

| Value                    | Description                              |
|--------------------------|------------------------------------------|
| `ZERO`                   | Logic state 0 (low)                      |
| `ONE`                    | Logic state 1 (high)                     |
| `L`                      | Low (comparison result)                  |
| `H`                      | High (comparison result)                 |
| `X`                      | Don't care / non-drive state             |
| `M`                      | Midband                                  |
| `V`                      | Compare high or low (not midband)        |
| `D`                      | Drive data from source waveform          |
| `E`                      | Compare data from source waveform        |
| `NOT_A_PIN_STATE`        | Non-existent DUT cycle                   |
| `PIN_STATE_NOT_ACQUIRED` | State not acquired by History RAM        |

### nidigital.WriteStaticPinState

| Value  | Description       |
|--------|-------------------|
| `ZERO` | Drive pin low     |
| `ONE`  | Drive pin high    |
| `X`    | Non-drive state   |

### nidigital.TerminationMode

| Value         | Description                               |
|---------------|-------------------------------------------|
| `ACTIVE_LOAD` | Active load provides current              |
| `VTERM`       | Terminates to VTERM voltage               |
| `HIGH_Z`      | High impedance (non-drive cycles)         |

### nidigital.DriveFormat

| Value | Description                        |
|-------|------------------------------------|
| `NR`  | Non-return (logic level maintained)|
| `RL`  | Return to logic low                |
| `RH`  | Return to logic high               |
| `SBC` | Surround by complement             |

### nidigital.HistoryRAMTriggerType

| Value            | Description                          |
|------------------|--------------------------------------|
| `FIRST_FAILURE`  | Trigger on first pattern failure     |
| `CYCLE_NUMBER`   | Trigger at specified cycle number    |
| `PATTERN_LABEL`  | Trigger on pattern label             |

### nidigital.HistoryRAMCyclesToAcquire

| Value    | Description                  |
|----------|------------------------------|
| `FAILED` | Acquire only failed cycles   |
| `ALL`    | Acquire all cycles           |

### nidigital.TriggerType

| Value          | Description          |
|----------------|----------------------|
| `NONE`         | Trigger disabled     |
| `DIGITAL_EDGE` | Digital edge trigger |
| `SOFTWARE`     | Software trigger     |

### nidigital.DigitalEdge

| Value     | Description             |
|-----------|-------------------------|
| `RISING`  | Low-to-high transition  |
| `FALLING` | High-to-low transition  |

### nidigital.SourceDataMapping

| Value        | Description                              |
|--------------|------------------------------------------|
| `BROADCAST`  | Same waveform data for all sites         |
| `SITE_UNIQUE`| Unique waveform data per site            |

### nidigital.TDREndpointTermination

| Value              | Description                |
|--------------------|----------------------------|
| `OPEN`             | Open circuit termination   |
| `SHORT_TO_GROUND`  | Short to ground            |

### nidigital.FrequencyMeasurementMode

| Value      | Description                          |
|------------|--------------------------------------|
| `BANKED`   | Serial measurements, max 200 MHz    |
| `PARALLEL` | Parallel measurements, max 100 MHz  |

### nidigital.BitOrder

| Value | Description                    |
|-------|--------------------------------|
| `MSB` | Most significant bit first     |
| `LSB` | Least significant bit first    |

### nidigital.SoftwareTrigger

| Value              | Description                    |
|--------------------|--------------------------------|
| `START`            | Override start trigger         |
| `CONDITIONAL_JUMP` | Conditional jump trigger      |

---

## Essential Properties

### Pin Voltage / Current Levels

| Property          | Type  | Description                           |
|-------------------|-------|---------------------------------------|
| `vil`             | float | Input voltage for logic low (V)       |
| `vih`             | float | Input voltage for logic high (V)      |
| `vol`             | float | Output voltage threshold for low (V)  |
| `voh`             | float | Output voltage threshold for high (V) |
| `vterm`           | float | Termination voltage (V)               |
| `termination_mode`| Enum  | ACTIVE_LOAD, VTERM, or HIGH_Z         |

### Active Load Properties

| Property             | Type  | Description                           |
|----------------------|-------|---------------------------------------|
| `active_load_iol`    | float | Current DUT sinks below VCOM (A)     |
| `active_load_ioh`    | float | Current DUT sources above VCOM (A)   |
| `active_load_vcom`   | float | Commutating voltage (V)              |

### PPMU Properties (per-channel)

| Property                        | Type  | Description                              |
|---------------------------------|-------|------------------------------------------|
| `ppmu_output_function`          | Enum  | VOLTAGE or CURRENT                       |
| `ppmu_voltage_level`            | float | Voltage to force (V)                     |
| `ppmu_current_level`            | float | Current to force (A)                     |
| `ppmu_current_level_range`      | float | Current level range (A)                  |
| `ppmu_voltage_limit_high`       | float | High voltage clamp (V)                   |
| `ppmu_voltage_limit_low`        | float | Low voltage clamp (V)                    |
| `ppmu_current_limit`            | float | Current limit when forcing voltage (A)   |
| `ppmu_current_limit_range`      | float | Current limit range (A)                  |
| `ppmu_current_limit_behavior`   | Enum  | REGULATE                                 |
| `ppmu_aperture_time`            | float | Measurement aperture time                |
| `ppmu_aperture_time_units`      | Enum  | SECONDS                                  |
| `ppmu_allow_extended_voltage_range` | bool | Enable extended voltage range         |

### Pin Function Properties

| Property            | Type | Description                            |
|---------------------|------|----------------------------------------|
| `selected_function` | Enum | DIGITAL, PPMU, OFF, DISCONNECT         |
| `mask_compare`      | bool | Mask pattern comparison failures       |

### Trigger Properties

| Property                                   | Type | Description                      |
|--------------------------------------------|------|----------------------------------|
| `start_trigger_type`                       | Enum | NONE, DIGITAL_EDGE, SOFTWARE     |
| `digital_edge_start_trigger_source`        | str  | Source terminal for start trigger|
| `digital_edge_start_trigger_edge`          | Enum | RISING or FALLING                |
| `conditional_jump_trigger_type`            | Enum | NONE, DIGITAL_EDGE, SOFTWARE     |

### History RAM Properties

| Property                                        | Type | Description                        |
|-------------------------------------------------|------|------------------------------------|
| `history_ram_trigger_type`                      | Enum | FIRST_FAILURE, CYCLE_NUMBER, PATTERN_LABEL |
| `history_ram_cycles_to_acquire`                 | Enum | FAILED or ALL                      |
| `history_ram_pretrigger_samples`                | int  | Samples before trigger             |
| `history_ram_max_samples_to_acquire_per_site`   | int  | Max samples per site (-1 unlimited)|
| `history_ram_number_of_samples_is_finite`       | bool | Finite vs continuous acquisition   |
| `history_ram_buffer_size_per_site`              | int  | Host memory buffer size            |

### Clock Generator Properties

| Property                         | Type  | Description                   |
|----------------------------------|-------|-------------------------------|
| `clock_generator_frequency`      | float | Clock frequency (Hz)          |
| `clock_generator_is_running`     | bool  | Whether clock is active       |

### Frequency Counter Properties

| Property                                | Type  | Description                       |
|-----------------------------------------|-------|-----------------------------------|
| `frequency_counter_measurement_mode`    | Enum  | BANKED or PARALLEL                |
| `frequency_counter_measurement_time`    | float | Measurement duration (seconds)    |

### Device Properties (read-only)

| Property             | Type | Description               |
|----------------------|------|---------------------------|
| `instrument_model`   | str  | Model number              |
| `serial_number`      | str  | Serial number             |
| `channel_count`      | int  | Number of channels        |

---

## Core Methods

### File Loading and Configuration

```python
# Load pin map (required before pattern operations)
session.load_pin_map(pin_map_file_path="pinmap.pinmap")

# Load specifications, levels, and timing
session.load_specifications_levels_and_timing(
    specifications_file_paths="specs.specs",
    levels_file_paths="levels.digilevels",
    timing_file_paths="timing.digitiming"
)

# Apply levels and timing sheets
session.apply_levels_and_timing(
    levels_sheet="DefaultLevels",
    timing_sheet="DefaultTiming"
)

# Load a digital pattern
session.load_pattern(file_path="pattern.digipat")
```

### Pattern Burst

```python
# Run a digital pattern
session.burst_pattern(
    start_label="main",
    select_digital_function=True,  # Auto-set pins to DIGITAL mode
    wait_until_done=True,
    timeout=hightime.timedelta(seconds=30.0)
)

# Get pass/fail results per site
pass_fail = session.get_site_pass_fail(site_list="site0,site1,site2,site3")
# Returns: dict mapping site number to bool (True=pass)

# Abort a running pattern
session.abort()

# Wait for pattern completion
session.wait_until_done(timeout=hightime.timedelta(seconds=10.0))
```

### PPMU Methods

```python
# Configure and source voltage
session.channels["PXI1Slot2/0"].selected_function = nidigital.SelectedFunction.PPMU
session.channels["PXI1Slot2/0"].ppmu_output_function = nidigital.PPMUOutputFunction.VOLTAGE
session.channels["PXI1Slot2/0"].ppmu_voltage_level = 3.3
session.channels["PXI1Slot2/0"].ppmu_current_limit_range = 0.032

# Start sourcing
session.channels["PXI1Slot2/0"].ppmu_source()

# Measure current
current_measurements = session.channels["PXI1Slot2/0"].ppmu_measure(
    measurement_type=nidigital.PPMUMeasurementType.CURRENT
)
# Returns: list of float values (one per channel in the repeated capability)

# Measure voltage
voltage_measurements = session.channels["PXI1Slot2/0"].ppmu_measure(
    measurement_type=nidigital.PPMUMeasurementType.VOLTAGE
)

# Disconnect when done
session.channels["PXI1Slot2/0"].selected_function = nidigital.SelectedFunction.DISCONNECT
```

### Static Pin Control

```python
# Write static pin state
session.channels["PXI1Slot2/0"].write_static(
    state=nidigital.WriteStaticPinState.ONE
)

# Read static pin state
states = session.channels["PXI1Slot2/0"].read_static()
# Returns: list of PinState enums
```

### Waveform Operations

```python
# Create source waveform (parallel)
session.create_source_waveform_parallel(
    pin_list="DUT_DATA",
    waveform_name="src_data",
    data_mapping=nidigital.SourceDataMapping.BROADCAST
)

# Write to source waveform
session.write_source_waveform_broadcast_u32(
    waveform_name="src_data",
    waveform_data=[0x00, 0xFF, 0xAA, 0x55]
)

# Create capture waveform (parallel)
session.create_capture_waveform_parallel(
    pin_list="DUT_OUT",
    waveform_name="cap_data"
)

# Fetch captured data after pattern burst
capture_data = session.fetch_capture_waveform(
    site_list="site0",
    waveform_name="cap_data",
    samples_to_read=100,
    timeout=hightime.timedelta(seconds=5.0)
)

# Serial waveform operations
session.create_source_waveform_serial(
    pin_list="DUT_SPI_MOSI",
    waveform_name="spi_tx",
    data_mapping=nidigital.SourceDataMapping.BROADCAST,
    sample_width=8,
    bit_order=nidigital.BitOrder.MSB
)
```

### Time Set and Timing

```python
# Configure time set period
session.configure_time_set_period(
    time_set_name="tset_100mhz",
    period=hightime.timedelta(nanoseconds=10)
)

# Configure drive edges
session.channels["DUT_CLK"].configure_time_set_drive_edges(
    time_set_name="tset_100mhz",
    format=nidigital.DriveFormat.NR,
    drive_on_edge=hightime.timedelta(nanoseconds=0),
    drive_data_edge=hightime.timedelta(nanoseconds=0),
    drive_return_edge=hightime.timedelta(nanoseconds=5),
    drive_off_edge=hightime.timedelta(nanoseconds=10)
)

# Configure compare strobe
session.channels["DUT_OUT"].configure_time_set_compare_edges_strobe(
    time_set_name="tset_100mhz",
    strobe_edge=hightime.timedelta(nanoseconds=7)
)
```

### History RAM

```python
# Configure History RAM
session.history_ram_trigger_type = nidigital.HistoryRAMTriggerType.FIRST_FAILURE
session.history_ram_cycles_to_acquire = nidigital.HistoryRAMCyclesToAcquire.FAILED
session.history_ram_pretrigger_samples = 0

# After running a pattern, get sample count
sample_count = session.get_history_ram_sample_count(site="site0")

# Fetch cycle information
cycle_info = session.fetch_history_ram_cycle_information(
    site="site0",
    sample_index=0,
    position=0,
    samples_to_read=sample_count
)
# Returns: list of HistoryRAMCycleInformation objects
```

### Frequency Counter

```python
# Configure and measure frequency
session.channels["DUT_CLK"].frequency_counter_measurement_mode = nidigital.FrequencyMeasurementMode.BANKED
session.channels["DUT_CLK"].frequency_counter_measurement_time = hightime.timedelta(milliseconds=10)

frequencies = session.channels["DUT_CLK"].frequency_counter_measure_frequency()
# Returns: list of float values (Hz)
```

### Clock Generator

```python
# Generate a clock signal
session.channels["DUT_CLK"].clock_generator_frequency = 100_000_000  # 100 MHz
session.channels["DUT_CLK"].clock_generator_generate_clock(frequency=100e6)

# Check if running
is_running = session.channels["DUT_CLK"].clock_generator_is_running

# Abort clock generation
session.channels["DUT_CLK"].clock_generator_abort()
```

### TDR Calibration

```python
# Perform TDR measurement for cable delay compensation
offsets = session.tdr(
    apply_offsets=True  # Auto-apply measured offsets
)

# Or apply manually
session.apply_tdr_offsets(offsets)
```

### Calibration and Device Management

```python
# Self-calibrate
session.self_calibrate()

# Self-test
session.self_test()

# Reset
session.reset()

# Reset device
session.reset_device()
```

---

## Data Structures

### HistoryRAMCycleInformation

Returned by `fetch_history_ram_cycle_information()`:

```python
cycle.pattern_name        # str — pattern that generated this cycle
cycle.time_set_name       # str — time set used
cycle.vector_number       # int — vector number in pattern
cycle.cycle_number        # int — cycle number
cycle.num_dut_cycles      # int — number of DUT cycles
cycle.scan_offset         # int — scan offset
cycle.expected_pin_states # list — expected pin states (PinState enums)
cycle.actual_pin_states   # list — actual pin states (PinState enums)
cycle.per_pin_pass_fail   # list — per-pin pass/fail (bool)
```

### PinInfo

Named tuple for pin information:

```python
pin_info.pin_name      # str — logical pin name
pin_info.site_number   # int — site index
pin_info.channel_name  # str — physical channel name
```

---

## Canonical Examples

### Example 1: PPMU Source Voltage and Measure Current

The most common parametric operation — power a DUT pin and measure current draw.

```python
import nidigital
import time

def ppmu_source_measure(resource_name, channels, voltage_level=3.3, current_limit=0.032):
    """Source voltage and measure current using PPMU."""
    with nidigital.Session(resource_name=resource_name) as session:
        # Configure PPMU
        session.channels[channels].ppmu_aperture_time = 0.000004  # 4 µs
        session.channels[channels].ppmu_aperture_time_units = nidigital.PPMUApertureTimeUnits.SECONDS
        session.channels[channels].ppmu_output_function = nidigital.PPMUOutputFunction.VOLTAGE
        session.channels[channels].ppmu_voltage_level = voltage_level
        session.channels[channels].ppmu_voltage_limit_high = voltage_level + 0.5
        session.channels[channels].ppmu_voltage_limit_low = 0
        session.channels[channels].ppmu_current_limit_range = current_limit

        # Source
        session.channels[channels].ppmu_source()

        # Allow settling
        time.sleep(0.01)

        # Measure
        current = session.channels[channels].ppmu_measure(
            nidigital.PPMUMeasurementType.CURRENT
        )
        voltage = session.channels[channels].ppmu_measure(
            nidigital.PPMUMeasurementType.VOLTAGE
        )

        # Disconnect
        session.channels[channels].selected_function = nidigital.SelectedFunction.DISCONNECT

        return voltage, current

# Usage
voltages, currents = ppmu_source_measure(
    "PXI1Slot2", "PXI1Slot2/0,PXI1Slot2/1", voltage_level=3.3
)
```

### Example 2: Digital Pattern Burst

Load and execute a digital pattern, then check results.

```python
import nidigital

def run_digital_pattern(resource_name, pin_map, specs, levels, timing, pattern):
    """Load and execute a digital pattern."""
    with nidigital.Session(resource_name=resource_name) as session:
        # Load configuration files
        session.load_pin_map(pin_map_file_path=pin_map)
        session.load_specifications_levels_and_timing(
            specifications_file_paths=specs,
            levels_file_paths=levels,
            timing_file_paths=timing
        )
        session.apply_levels_and_timing(
            levels_sheet="DefaultLevels",
            timing_sheet="DefaultTiming"
        )

        # Load pattern
        session.load_pattern(file_path=pattern)

        # Burst pattern
        session.burst_pattern(
            start_label="main",
            select_digital_function=True,
            wait_until_done=True,
            timeout=hightime.timedelta(seconds=30.0)
        )

        # Get results
        pass_fail = session.get_site_pass_fail(site_list="site0,site1")
        return pass_fail

# Usage
results = run_digital_pattern(
    "PXI1Slot2",
    pin_map="project.pinmap",
    specs="project.specs",
    levels="project.digilevels",
    timing="project.digitiming",
    pattern="test_pattern.digipat"
)
for site, passed in results.items():
    print(f"Site {site}: {'PASS' if passed else 'FAIL'}")
```

### Example 3: Static Pin Control

Toggle digital pins for simple GPIO-style control.

```python
import nidigital
import time

def toggle_digital_pins(resource_name, channels, num_toggles=10, delay=0.1):
    """Toggle digital pins between high and low."""
    with nidigital.Session(resource_name=resource_name) as session:
        session.channels[channels].selected_function = nidigital.SelectedFunction.DIGITAL

        for i in range(num_toggles):
            session.channels[channels].write_static(nidigital.WriteStaticPinState.ONE)
            time.sleep(delay)
            session.channels[channels].write_static(nidigital.WriteStaticPinState.ZERO)
            time.sleep(delay)

        # Read final state
        final_states = session.channels[channels].read_static()
        return final_states
```

---

## PPMU

### PPMU Overview

Each pin on the PXIe-6570/6571 has a built-in Per-Pin Measurement Unit (PPMU) that can:
- **Force voltage** and measure current (most common)
- **Force current** and measure voltage

PPMU is independent from digital pattern mode — pins must be switched to `PPMU` mode.

### PPMU Voltage Ranges

| Range        | Resolution  | Notes                           |
|--------------|-------------|---------------------------------|
| ±4 V         | ~30 µV      | Standard range                  |
| ±7 V (ext)   | ~50 µV      | Requires `ppmu_allow_extended_voltage_range = True` |

### PPMU Current Ranges

Common current limit ranges: 2 µA, 20 µA, 200 µA, 2 mA, 32 mA. Always set `ppmu_current_limit_range` explicitly — auto-ranging is not available.

---

## Digital Patterns

### Pattern Workflow

1. **Load pin map** — Maps logical pin names to physical channels
2. **Load specs/levels/timing** — Defines voltage levels and timing for each time set
3. **Apply levels/timing** — Selects which sheets to use
4. **Load pattern** — Loads the `.digipat` file
5. **Burst pattern** — Executes the pattern
6. **Check results** — `get_site_pass_fail()` for overall, History RAM for details

### Pattern File Types

| File Extension   | Description                                    |
|------------------|------------------------------------------------|
| `.pinmap`        | Pin map — maps signals to physical channels    |
| `.specs`         | Specifications — parameterized values          |
| `.digilevels`    | Levels — voltage/current levels per time set   |
| `.digitiming`    | Timing — edge placement for each time set      |
| `.digipat`       | Pattern — the actual digital vectors           |

---

## History RAM

History RAM captures per-cycle pattern data for failure analysis.

```python
# Configure
session.history_ram_trigger_type = nidigital.HistoryRAMTriggerType.FIRST_FAILURE
session.history_ram_cycles_to_acquire = nidigital.HistoryRAMCyclesToAcquire.FAILED
session.history_ram_pretrigger_samples = 0
session.history_ram_max_samples_to_acquire_per_site = 1024

# Run pattern
session.burst_pattern(start_label="main", select_digital_function=True,
                      wait_until_done=True, timeout=hightime.timedelta(seconds=10.0))

# Analyze failures
sample_count = session.get_history_ram_sample_count(site="site0")
if sample_count > 0:
    cycles = session.fetch_history_ram_cycle_information(
        site="site0", sample_index=0, position=0, samples_to_read=sample_count
    )
    for c in cycles:
        print(f"Vector {c.vector_number}, Cycle {c.cycle_number}: "
              f"Expected={c.expected_pin_states}, Actual={c.actual_pin_states}")
```

---

## Driver-Specific Gotchas

1. **Pin maps are required**: You must load a `.pinmap` file before executing patterns. The pin map defines signal-to-channel routing and site configuration.

2. **Specifications files**: Levels and timing are defined in separate files (`.specs`, `.digilevels`, `.digitiming`). You must load all of these and call `apply_levels_and_timing()` before pattern execution.

3. **PPMU vs Digital mode exclusion**: Pins can be in PPMU mode (DC parametric) or Digital mode (pattern execution), but **not both simultaneously**. Switch using `selected_function`.

4. **Site vs Channel**: nidigital distinguishes "sites" (DUTs under test) from "channels" (physical pins). A single site maps to multiple channels through the pin map. Use `session.sites[...]` for site-level operations and `session.channels[...]` for pin-level operations.

5. **Pattern file format**: Patterns are `.digipat` files, typically created in NI Digital Pattern Editor. They cannot be easily created programmatically.

6. **PPMU aperture time**: Longer aperture = better accuracy but slower. Default is device-dependent. 4 µs is typical for most applications. Always set explicitly.

7. **No auto-ranging for PPMU**: You must set `ppmu_current_limit_range` explicitly to match your expected current levels. Incorrect ranges give poor accuracy.

8. **TDR calibration for high-speed patterns**: For patterns running at >100 MHz, use `tdr()` to measure and compensate for cable delays. Delays not compensated cause setup/hold timing violations.

9. **`burst_pattern` with `select_digital_function=True`**: This automatically switches all pattern pins to DIGITAL mode. If you need some pins in PPMU mode during a burst, set this to `False` and manually configure `selected_function`.

10. **`get_site_pass_fail()` returns a dict**: The return value is a dictionary mapping site numbers (int) to boolean pass/fail. Not a simple list.

11. **Multiple instruments must match**: When creating a session with multiple instruments (`"PXI1Slot2,PXI1Slot3"`), they must be the same model and in the same PXI chassis.
