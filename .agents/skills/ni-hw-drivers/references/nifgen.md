# nifgen Reference — NI-FGEN Python API

**Package**: `nifgen` (via `pip install nifgen`)
**Runtime**: NI-FGEN driver (ni.com/downloads)
**Instruments**: PXI/PXIe Function Generators and Arbitrary Waveform Generators (PXIe-5413, PXIe-5423, PXIe-5433, PXIe-5450, PXIe-5451)
**Current Version**: 1.4.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Session Creation](#session-creation)
2. [Key Enums](#key-enums)
3. [Essential Properties](#essential-properties)
4. [Core Methods](#core-methods)
5. [Canonical Examples](#canonical-examples)
6. [Arbitrary Waveforms](#arbitrary-waveforms)
7. [Sequences and Scripts](#sequences-and-scripts)
8. [Triggering and Synchronization](#triggering-and-synchronization)
9. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Session Creation

```python
import nifgen

# Basic session
with nifgen.Session("Dev1") as session:
    pass

# Specific channel
with nifgen.Session("Dev1", channel_name="0") as session:
    pass

# Multi-channel
with nifgen.Session("Dev1", channel_name="0,1") as session:
    pass

# Simulation
options = "Simulate=1, DriverSetup=Model:5433; BoardType:PXIe"
with nifgen.Session("Dev1", options=options) as session:
    pass
```

### Session Constructor Parameters

| Parameter       | Type   | Default  | Description                                         |
|-----------------|--------|----------|-----------------------------------------------------|
| `resource_name` | str    | Required | Device name (e.g., `"PXI1Slot4"`, `"Dev1"`)        |
| `channel_name`  | str    | None     | Channel(s) to use (default: `"0"`)                  |
| `reset_device`  | bool   | False    | Reset device to known state on open                 |
| `options`       | dict/str | {}     | Session options (simulate, driver_setup, etc.)      |

---

## Key Enums

### nifgen.OutputMode

Controls the generation mode.

| Value    | Description                                          |
|----------|------------------------------------------------------|
| `FUNC`   | Standard waveform generation (sine, square, etc.)    |
| `ARB`    | Arbitrary waveform generation                        |
| `SEQ`    | Arbitrary waveform sequence                          |
| `SCRIPT` | Waveform scripting engine                            |
| `FREQ_LIST` | Frequency list mode                               |

### nifgen.Waveform

Standard waveform shapes for `OutputMode.FUNC`.

| Value        | Description                       |
|--------------|-----------------------------------|
| `SINE`       | Sine wave                         |
| `SQUARE`     | Square wave                       |
| `TRIANGLE`   | Triangle wave                     |
| `RAMP_UP`    | Ramp up (sawtooth)                |
| `RAMP_DOWN`  | Ramp down (reverse sawtooth)      |
| `DC`         | DC level                          |
| `NOISE`      | White noise                       |
| `USER`       | User-defined standard waveform    |

### nifgen.TriggerMode

Controls how many waveform cycles are generated per trigger.

| Value        | Description                                    |
|--------------|------------------------------------------------|
| `SINGLE`     | Generate one waveform cycle per trigger        |
| `CONTINUOUS` | Generate continuously after trigger            |
| `STEPPED`    | Step through sequence on each trigger          |
| `BURST`      | Generate fixed number of cycles per trigger    |

### nifgen.StartTriggerType

| Value          | Description                    |
|----------------|--------------------------------|
| `TRIG_NONE`    | No start trigger               |
| `DIGITAL_EDGE` | Trigger on digital edge        |
| `SOFTWARE_EDGE`| Trigger via software command   |

### nifgen.ScriptTriggerType

| Value          | Description                    |
|----------------|--------------------------------|
| `TRIG_NONE`    | No script trigger              |
| `DIGITAL_EDGE` | Digital edge trigger           |
| `DIGITAL_LEVEL`| Digital level trigger          |
| `SOFTWARE_EDGE`| Software trigger               |

### nifgen.ClockMode

| Value             | Description                              |
|-------------------|------------------------------------------|
| `HIGH_RESOLUTION` | High-resolution clock                    |
| `DIVIDE_DOWN`     | Divide down from reference clock         |
| `AUTOMATIC`       | Driver selects best mode automatically   |

### nifgen.HardwareState

| Value            | Description                     |
|------------------|---------------------------------|
| `IDLE`           | Not generating                  |
| `WAITING_FOR_START_TRIGGER` | Waiting for trigger  |
| `RUNNING`        | Actively generating             |
| `DONE`           | Generation complete             |
| `HARDWARE_ERROR` | Hardware error occurred         |

### nifgen.Trigger

| Value    | Description              |
|----------|--------------------------|
| `START`  | Start trigger            |
| `SCRIPT` | Script trigger           |

### nifgen.TerminalConfiguration

| Value            | Description           |
|------------------|-----------------------|
| `SINGLE_ENDED`   | Single-ended output   |
| `DIFFERENTIAL`   | Differential output   |

---

## Essential Properties

### Output Configuration

| Property                   | Type   | Description                                     |
|----------------------------|--------|-------------------------------------------------|
| `output_mode`              | Enum   | FUNC, ARB, SEQ, SCRIPT, FREQ_LIST              |
| `output_enabled`           | bool   | Enable/disable channel output                   |
| `output_impedance`         | float  | Output impedance (50 Ω or high-Z)              |
| `load_impedance`           | float  | Expected load impedance (for amplitude calc)    |
| `terminal_configuration`   | Enum   | SINGLE_ENDED or DIFFERENTIAL                    |
| `analog_path`              | Enum   | MAIN, DIRECT, FIXED_LOW_GAIN, FIXED_HIGH_GAIN  |
| `channel_delay`            | float  | Inter-channel delay (seconds)                   |

### Standard Waveform Properties (OutputMode.FUNC)

| Property             | Type  | Description                              |
|----------------------|-------|------------------------------------------|
| `func_waveform`      | Enum  | SINE, SQUARE, TRIANGLE, etc.             |
| `func_amplitude`     | float | Peak-to-peak amplitude (volts)           |
| `func_dc_offset`     | float | DC offset (volts)                        |
| `func_frequency`     | float | Frequency (Hz)                           |
| `func_start_phase`   | float | Starting phase (degrees)                 |
| `func_duty_cycle_high`| float| Duty cycle for square wave (0-100%)      |

### Arbitrary Waveform Properties (OutputMode.ARB)

| Property              | Type  | Description                              |
|-----------------------|-------|------------------------------------------|
| `arb_gain`            | float | Gain multiplier for arb data (V)        |
| `arb_offset`          | float | DC offset for arb waveform (V)          |
| `arb_sample_rate`     | float | Playback sample rate (S/s)              |
| `arb_waveform_handle` | int   | Handle of current waveform              |
| `arb_sequence_handle` | int   | Handle of current sequence              |

### Trigger Properties

| Property                               | Type | Description                              |
|----------------------------------------|------|------------------------------------------|
| `trigger_mode`                         | Enum | SINGLE, CONTINUOUS, STEPPED, BURST       |
| `start_trigger_type`                   | Enum | TRIG_NONE, DIGITAL_EDGE, SOFTWARE_EDGE   |
| `digital_edge_start_trigger_source`    | str  | Source terminal (e.g., `"PXI_Trig0"`)    |
| `digital_edge_start_trigger_edge`      | Enum | RISING or FALLING                        |

### Memory / Capabilities (read-only)

| Property               | Type | Description                          |
|------------------------|------|--------------------------------------|
| `max_waveform_size`    | int  | Maximum waveform samples             |
| `min_waveform_size`    | int  | Minimum waveform samples             |
| `max_num_waveforms`    | int  | Maximum number of waveforms in memory|
| `max_sequence_length`  | int  | Maximum sequence steps               |
| `memory_size`          | int  | Total onboard memory (bytes)         |
| `waveform_quantum`     | int  | Waveform size must be multiple of this|

### Clock Properties

| Property                  | Type | Description                         |
|---------------------------|------|-------------------------------------|
| `reference_clock_source`  | Enum | PXI_CLOCK, ONBOARD_REFERENCE_CLOCK  |
| `sample_clock_source`     | Enum | ONBOARD_CLOCK, CLOCK_IN, etc.       |
| `clock_mode`              | Enum | HIGH_RESOLUTION, DIVIDE_DOWN, AUTO  |

### Device Properties (read-only)

| Property             | Type | Description               |
|----------------------|------|---------------------------|
| `instrument_model`   | str  | Model number              |
| `serial_number`      | str  | Serial number             |
| `channel_count`      | int  | Number of output channels |
| `bus_type`           | Enum | PXI, PXIe, etc.           |

---

## Core Methods

### Standard Waveform Configuration

```python
# Configure a standard waveform
session.configure_standard_waveform(
    waveform=nifgen.Waveform.SINE,
    amplitude=1.0,          # Vpp
    frequency=1_000_000,    # 1 MHz
    dc_offset=0.0,
    start_phase=0.0
)
```

### Arbitrary Waveform Methods

```python
# Create waveform from data (normalized ±1.0)
wfm_handle = session.create_waveform(waveform_data_array=data)
# data: list or numpy array of float64, values in [-1.0, 1.0]

# Create waveform from file
wfm_handle = session.create_waveform_from_file_f64(
    file_name="waveform.bin",
    byte_order=nifgen.ByteOrder.LITTLE
)

# Allocate waveform memory and write later
wfm_handle = session.allocate_waveform(waveform_size=1024)
session.write_waveform(waveform_name_or_handle=wfm_handle, data=data)

# Allocate named waveform
session.allocate_named_waveform(
    waveform_name="myWaveform",
    waveform_size=1024
)

# Configure arbitrary waveform playback
session.configure_arb_waveform(
    waveform_handle=wfm_handle,
    gain=1.0,        # Scales [-1,1] data to ±gain volts
    offset=0.0       # DC offset
)

# Set write position for partial updates
session.set_next_write_position(
    waveform_name_or_handle=wfm_handle,
    relative_to=nifgen.RelativeTo.START,
    offset=0
)

# Delete waveform
session.delete_waveform(waveform_name_or_handle=wfm_handle)

# Clear all arb memory
session.clear_arb_memory()

# Define user standard waveform (replaces USER in FUNC mode)
session.define_user_standard_waveform(waveform_data_array=data)
session.clear_user_standard_waveform()
```

### Sequence Methods

```python
# Create a simple sequence
seq_handle = session.create_arb_sequence(
    waveform_handles_array=[wfm1, wfm2, wfm3],
    loop_counts_array=[10, 20, 10]
)

# Create advanced sequence with markers
waveform_table, seq_handle = session.create_advanced_arb_sequence(
    waveform_handles_array=[wfm1, wfm2],
    loop_counts_array=[5, 10],
    sample_counts_array=None,    # optional: partial waveform
    marker_location_array=None   # optional: marker positions
)

# Configure sequence playback
session.configure_arb_sequence(
    sequence_handle=seq_handle,
    gain=1.0,
    offset=0.0
)

# Create frequency list
freq_handle = session.create_freq_list(
    waveform=nifgen.Waveform.SINE,
    frequency_array=[1e6, 2e6, 5e6],
    duration_array=[0.001, 0.002, 0.001]
)

# Configure frequency list playback
session.configure_freq_list(
    frequency_list_handle=freq_handle,
    amplitude=1.0,
    dc_offset=0.0,
    start_phase=0.0
)

# Delete sequence/freq list
session.clear_arb_sequence(sequence_handle=seq_handle)
session.clear_freq_list(frequency_list_handle=freq_handle)
```

### Script Methods

```python
# Write a waveform generation script
session.write_script(script="""
script myScript
  repeat 10
    generate sine
  end repeat
  generate myCustomWaveform
end script
""")

# Set active script
session.script_to_generate = "myScript"

# Delete script
session.delete_script(script_name="myScript")
```

### Generation Control

```python
# Initiate generation (use as context manager)
with session.initiate():
    # Generation is active
    pass
# Generation stops automatically on exit

# Wait for generation to complete
session.wait_until_done(max_time=hightime.timedelta(seconds=10.0))

# Check if done
done = session.is_done()

# Abort generation
session.abort()

# Commit settings (apply without starting)
session.commit()

# Disable output
session.disable()

# Check hardware state
state = session.get_hardware_state()
# Returns: HardwareState.IDLE, RUNNING, DONE, etc.

# Query capabilities
arb_caps = session.query_arb_wfm_capabilities()
seq_caps = session.query_arb_seq_capabilities()
```

### Calibration

```python
session.self_cal()
temp = session.read_current_temperature()
```

---

## Canonical Examples

### Example 1: Standard Sine Wave

The most fundamental function generator operation.

```python
import nifgen
import time

def generate_sine_wave(resource_name, frequency=1e6, amplitude=1.0, duration=5.0):
    """Generate a continuous sine wave."""
    with nifgen.Session(resource_name) as session:
        session.output_mode = nifgen.OutputMode.FUNC
        session.configure_standard_waveform(
            waveform=nifgen.Waveform.SINE,
            amplitude=amplitude,
            frequency=frequency,
            dc_offset=0.0,
            start_phase=0.0
        )

        with session.initiate():
            time.sleep(duration)

# Usage
generate_sine_wave("PXI1Slot4", frequency=10e6, amplitude=2.0, duration=10.0)
```

### Example 2: Arbitrary Waveform (Chirp Signal)

```python
import nifgen
import numpy as np
import time

def generate_chirp(resource_name, start_freq=1e6, stop_freq=10e6, duration=0.001):
    """Generate a linear frequency chirp."""
    with nifgen.Session(resource_name) as session:
        # Create chirp waveform
        sample_rate = 100e6
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples)

        # Linear chirp (normalized to ±1.0)
        instantaneous_freq = start_freq + (stop_freq - start_freq) * t / duration
        phase = 2 * np.pi * np.cumsum(instantaneous_freq) / sample_rate
        waveform_data = np.sin(phase)

        # Load waveform
        wfm_handle = session.create_waveform(waveform_data_array=waveform_data)

        # Configure
        session.output_mode = nifgen.OutputMode.ARB
        session.configure_arb_waveform(
            waveform_handle=wfm_handle,
            gain=1.0,
            offset=0.0
        )
        session.arb_sample_rate = sample_rate

        # Generate
        with session.initiate():
            time.sleep(5)

# Usage
generate_chirp("Dev1", start_freq=1e6, stop_freq=50e6, duration=0.001)
```

### Example 3: Triggered Burst Generation

```python
import nifgen
import time

def generate_triggered_burst(resource_name):
    """Generate bursts of a sine wave on external trigger."""
    with nifgen.Session(resource_name) as session:
        session.output_mode = nifgen.OutputMode.FUNC
        session.configure_standard_waveform(
            waveform=nifgen.Waveform.SINE,
            amplitude=1.0,
            frequency=1_000_000
        )

        # Configure trigger
        session.trigger_mode = nifgen.TriggerMode.BURST
        session.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
        session.digital_edge_start_trigger_source = "PXI_Trig0"
        session.digital_edge_start_trigger_edge = nifgen.StartTriggerDigitalEdgeEdge.RISING

        with session.initiate():
            print("Waiting for triggers...")
            time.sleep(30)
```

### Example 4: Multi-Device Synchronization

```python
import nifgen
import time

def synchronized_generation(resource1, resource2):
    """Synchronize two function generators using PXI triggers."""
    with nifgen.Session(resource1) as leader, nifgen.Session(resource2) as follower:
        # Configure both generators
        for session in [leader, follower]:
            session.output_mode = nifgen.OutputMode.FUNC
            session.configure_standard_waveform(
                waveform=nifgen.Waveform.SINE,
                amplitude=1.0,
                frequency=1_000_000
            )

        # Leader uses software trigger, exports start trigger
        leader.start_trigger_type = nifgen.StartTriggerType.SOFTWARE_EDGE
        leader.exported_start_trigger_output_terminal = "PXI_Trig0"

        # Follower triggers from leader's exported trigger
        follower.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
        follower.digital_edge_start_trigger_source = "PXI_Trig0"

        # Start follower first (waits for trigger), then leader
        with follower.initiate():
            with leader.initiate():
                leader.send_software_edge_trigger(
                    trigger=nifgen.Trigger.START,
                    trigger_id="None"
                )
                time.sleep(5.0)
```

### Example 5: Script-Based Waveform Generation

```python
import nifgen
import time

def scripted_generation(resource_name):
    """Use waveform scripting for complex generation patterns."""
    with nifgen.Session(resource_name) as session:
        session.output_mode = nifgen.OutputMode.SCRIPT

        # Configure script triggers
        session.script_triggers[0].script_trigger_type = nifgen.ScriptTriggerType.SOFTWARE_EDGE

        # Write script
        session.write_script("""
script mySequence
  repeat until scriptTrigger0
    generate sine
    generate square
  end repeat
end script
""")

        session.script_to_generate = "mySequence"

        with session.initiate():
            time.sleep(5.0)
            # Stop the loop
            session.send_software_edge_trigger(
                trigger=nifgen.Trigger.SCRIPT,
                trigger_id="ScriptTrigger0"
            )
```

---

## Arbitrary Waveforms

### Waveform Data Requirements

- Data must be normalized to **[-1.0, 1.0]**. The driver scales by `arb_gain`.
- Waveform size must be a multiple of `waveform_quantum` (query with property).
- Minimum and maximum sizes are instrument-dependent (query `min_waveform_size`, `max_waveform_size`).

### Performance Tips

```python
# Use numpy arrays for best performance
import numpy as np

waveform = np.sin(np.linspace(0, 2*np.pi, 4096))  # Already in [-1, 1]
handle = session.create_waveform(waveform_data_array=waveform)

# Pre-allocate and stream for dynamic waveforms
handle = session.allocate_waveform(waveform_size=4096)
for i in range(iterations):
    new_data = compute_new_waveform(i)
    session.set_next_write_position(handle, nifgen.RelativeTo.START, 0)
    session.write_waveform(handle, new_data)
```

---

## Triggering and Synchronization

### Trigger Sources

Common trigger source terminal strings:
- `"PXI_Trig0"` through `"PXI_Trig7"` — PXI backplane trigger lines
- `"PXI_Star"` — PXI star trigger
- `"RTSI_7"` — RTSI trigger line
- `"ClkIn"` — External clock input

### Export Trigger Signals

```python
# Export start trigger to PXI backplane
session.exported_start_trigger_output_terminal = "PXI_Trig0"

# Export sample clock
session.exported_sample_clock_output_terminal = "PXI_Trig1"

# Export marker event
session.marker_event_output_terminal = "PXI_Trig2"
```

---

## Driver-Specific Gotchas

1. **`output_enabled` defaults to False on some instruments**: Always verify the output is enabled, or rely on the `initiate()` context manager which handles this.

2. **OutputMode switching requires abort**: When switching between `FUNC`, `ARB`, `SEQ`, or `SCRIPT` modes, you must abort first, reconfigure, then initiate again. You cannot change output mode while generating.

3. **Waveform handle lifetime**: Handles are valid for the session lifetime. Deleting a waveform while actively generating it will cause errors.

4. **`arb_sample_rate` constraints**: The achievable sample rate depends on the instrument and waveform size. Query actual rate after setting — it may be quantized.

5. **`func_amplitude` vs `arb_gain`**: For standard waveforms (`FUNC` mode), use `func_amplitude` (Vpp). For arbitrary waveforms (`ARB` mode), use `arb_gain` (scaling factor applied to normalized [-1, 1] data).

6. **`create_waveform()` data normalization**: Input data should be in **[-1.0, 1.0]**. The driver scales the output by `arb_gain`. Values outside this range are clipped.

7. **Marker events for synchronization**: Use marker events to trigger other instruments (e.g., a scope) at specific points in your waveform. Set marker positions when creating advanced sequences.

8. **Script mode complexity**: Waveform scripts are powerful (looping, branching, triggering) but complex. Use `SEQ` mode for simple looping and `FUNC` mode for standard waveforms. Only use `SCRIPT` when you need conditional behavior.

9. **`waveform_quantum` alignment**: Waveform sizes must be multiples of the quantum (typically 2-16 samples depending on instrument). The driver will error if the size is not aligned.

10. **Output impedance matching**: Set `output_impedance` and `load_impedance` to match your physical setup. Mismatched impedance causes amplitude errors and reflections at high frequencies.
