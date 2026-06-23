# niswitch Reference — NI-SWITCH Python API

**Package**: `niswitch` (via `pip install niswitch`)
**Runtime**: NI-SWITCH driver (ni.com/downloads)
**Instruments**: PXI/PXIe Switch Modules (PXI-2501, 2503, 2510–2599, 2720–2799 series, and many more)
**Current Version**: 1.4.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Session Creation](#session-creation)
2. [Key Enums](#key-enums)
3. [Essential Properties](#essential-properties)
4. [Core Methods](#core-methods)
5. [Canonical Examples](#canonical-examples)
6. [Scanning](#scanning)
7. [Relay Control](#relay-control)
8. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Session Creation

**Important**: Unlike most nimi-python drivers, `niswitch` requires a `topology` parameter that must match your physical switch module's configuration.

```python
import niswitch

# Basic session (topology must match hardware)
with niswitch.Session("Dev1", topology="2529/2-Wire 4x32 Matrix") as session:
    pass

# Use MAX-configured topology (default)
with niswitch.Session("Dev1", topology="Configured Topology") as session:
    pass

# Simulation
with niswitch.Session("Dev1", topology="2737/2-Wire 4x64 Matrix", simulate=True) as session:
    pass

# Reset on open
with niswitch.Session("Dev1", topology="2529/2-Wire 4x32 Matrix", reset_device=True) as session:
    pass
```

### Session Constructor Parameters

| Parameter       | Type   | Default                 | Description                                    |
|-----------------|--------|-------------------------|------------------------------------------------|
| `resource_name` | str    | Required                | Device name (e.g., `"PXI1Slot6"`, `"Dev1"`)   |
| `topology`      | str    | `"Configured Topology"` | Switch topology string (must match hardware)   |
| `simulate`      | bool   | False                   | Enable simulation mode                         |
| `reset_device`  | bool   | False                   | Reset device to known state on open            |

### Common Topology Strings

| Topology                       | Description                    |
|--------------------------------|--------------------------------|
| `"2501/1-Wire 48x1 Mux"`      | 48-channel 1-wire multiplexer  |
| `"2503/2-Wire 24x1 Mux"`      | 24-channel 2-wire multiplexer  |
| `"2510/Independent"`           | Independent relay control      |
| `"2520/80-SPST"`               | 80 SPST relays                 |
| `"2529/2-Wire 4x32 Matrix"`   | 4×32 two-wire matrix           |
| `"2530/1-Wire 128x1 Mux"`     | 128-channel 1-wire mux         |
| `"2532/1-Wire 4x128 Matrix"`  | 4×128 one-wire matrix          |
| `"2737/2-Wire 4x64 Matrix"`   | 4×64 two-wire matrix           |
| `"2790/Independent"`           | Independent relay control      |
| `"Configured Topology"`        | Use MAX configuration          |

---

## Key Enums

### niswitch.ScanMode

| Value              | Description                                           |
|--------------------|-------------------------------------------------------|
| `NONE`             | No scanning, manual connections only                  |
| `BREAK_BEFORE_MAKE`| Open existing connections before making new ones (safe)|
| `BREAK_AFTER_MAKE` | Make new connections before opening old ones           |

### niswitch.RelayAction

| Value   | Description              |
|---------|--------------------------|
| `OPEN`  | Open (disconnect) relay  |
| `CLOSE` | Close (connect) relay    |

### niswitch.RelayPosition

| Value    | Description         |
|----------|---------------------|
| `OPEN`   | Relay is open       |
| `CLOSED` | Relay is closed     |

### niswitch.PathCapability

| Value                   | Description                                          |
|-------------------------|------------------------------------------------------|
| `PATH_AVAILABLE`        | Can create path now                                  |
| `PATH_EXISTS`           | Path already exists                                  |
| `PATH_UNSUPPORTED`      | Not capable of this path                             |
| `RESOURCE_IN_USE`       | Valid path but resource currently in use              |
| `SOURCE_CONFLICT`       | Channels connected to different sources              |
| `CHANNEL_NOT_AVAILABLE` | Configuration channel unavailable                    |

### niswitch.TriggerInput

| Value           | Description                        |
|-----------------|------------------------------------|
| `IMMEDIATE`     | No external trigger                |
| `EXTERNAL`      | External trigger input             |
| `SOFTWARE_TRIG` | Software trigger                   |
| `TTL0` through `TTL7` | PXI trigger lines            |
| `PXI_STAR`      | PXI star trigger line              |

### niswitch.HandshakingInitiation

| Value                | Description                              |
|----------------------|------------------------------------------|
| `MEASUREMENT_DEVICE` | Measurement device controls handshaking  |
| `SWITCH`             | Switch initiates with advance signal     |

---

## Essential Properties

### Switch Configuration

| Property                                    | Type      | Description                                   |
|---------------------------------------------|-----------|-----------------------------------------------|
| `scan_mode`                                 | Enum      | NONE, BREAK_BEFORE_MAKE, BREAK_AFTER_MAKE     |
| `scan_list`                                 | str       | List of connections (e.g., `"r0->c0; r1->c1"`)|
| `scan_delay`                                | timedelta | Delay between scan steps (seconds)            |
| `continuous_scan`                           | bool      | Enable continuous scanning                    |
| `trigger_input`                             | Enum      | Trigger source for scan steps                 |
| `trigger_input_polarity`                    | Enum      | RISING or FALLING edge                        |
| `scan_advanced_output`                      | Enum      | Output signal destination after each step     |
| `scan_advanced_polarity`                    | Enum      | RISING or FALLING output polarity             |
| `handshaking_initiation`                    | Enum      | Who controls the handshaking                  |
| `power_down_latching_relays_after_debounce` | bool      | Power down latching relays after settling     |

### Relay Properties (read-only)

| Property             | Type  | Description                                    |
|----------------------|-------|------------------------------------------------|
| `number_of_relays`   | int   | Total relays in the switch                     |
| `num_of_columns`     | int   | Number of matrix columns                       |
| `num_of_rows`        | int   | Number of matrix rows                          |
| `settling_time`      | timedelta | Max time for signal to settle after switch  |
| `temperature`        | float | Internal temperature (°C)                      |

### Channel Properties (per-channel via `session.channels[...]`)

| Property                    | Type  | Description                          |
|-----------------------------|-------|--------------------------------------|
| `bandwidth`                 | float | Signal bandwidth (Hz)                |
| `characteristic_impedance`  | float | Impedance (Ω)                       |
| `settling_time`             | timedelta | Settling time for this channel    |
| `wire_mode`                 | int   | Number of wires (1, 2, or 4)        |
| `is_configuration_channel`  | bool  | Whether this is a config channel     |
| `max_switching_dc_power`    | float | Maximum switching DC power (W)       |

### Device Properties (read-only)

| Property            | Type | Description               |
|---------------------|------|---------------------------|
| `instrument_model`  | str  | Model number              |
| `serial_number`     | str  | Serial number             |
| `channel_count`     | int  | Number of channels        |

---

## Core Methods

### Connection Methods

```python
# Connect two channels
session.connect(channel1="r0", channel2="c0")

# Connect multiple paths (semicolon-separated)
session.connect_multiple(connection_list="r0->c0; r1->c1; r2->c2")

# Check if connection is possible
capability = session.can_connect(channel1="r0", channel2="c5")
# Returns: PathCapability enum (PATH_AVAILABLE, PATH_EXISTS, etc.)

# Disconnect two channels
session.disconnect(channel1="r0", channel2="c0")

# Disconnect multiple paths
session.disconnect_multiple(disconnection_list="r0->c0; r1->c1")

# Disconnect all connections
session.disconnect_all()

# Get the relay path between two channels
path = session.get_path(channel1="r0", channel2="c0")
# Returns: string of relay names forming the path

# Set a specific path
session.set_path(path_list="[r0->c0]")
```

### Scanning Methods

```python
# Configure and execute a scan
session.scan_list = "r0->c0; r1->c1; r2->c2; r3->c3"
session.scan_delay = hightime.timedelta(seconds=0.01)  # 10 ms per step
session.scan_mode = niswitch.ScanMode.BREAK_BEFORE_MAKE

# Initiate scan (use as context manager)
with session.initiate():
    session.wait_for_scan_complete(maximum_time_ms=10000)

# Abort scan
session.abort()

# Commit settings without starting
session.commit()

# Send software trigger
session.send_software_trigger()

# Wait for settling
session.wait_for_debounce(maximum_time_ms=5000)
```

### Relay Control Methods

```python
# Direct relay control
session.relay_control(
    relay_name="k0",
    relay_action=niswitch.RelayAction.CLOSE
)

# Get relay position
position = session.get_relay_position(relay_name="k0")
# Returns: RelayPosition.OPEN or RelayPosition.CLOSED

# Get relay actuation count (for lifecycle monitoring)
count = session.get_relay_count(relay_name="k0")

# Get relay name by index
name = session.get_relay_name(index=0)
```

### Channel / Info Methods

```python
# Get channel name by index
name = session.get_channel_name(index=0)

# Get multiple channel names
names = session.get_channel_names(indices=range(8))

# Route trigger signals
session.route_trigger_input(
    trigger_input_connector=niswitch.TriggerInput.PXI_TRIG0,
    trigger_input_bus_line=niswitch.TriggerInput.TTL0,
    invert=False
)
```

---

## Canonical Examples

### Example 1: Simple Matrix Routing

Connect and disconnect channels in a matrix switch.

```python
import niswitch

def connect_matrix_path(resource_name, row, column):
    """Connect a row to a column in a matrix switch."""
    with niswitch.Session(resource_name, topology="2529/2-Wire 4x32 Matrix") as session:
        # Connect
        session.connect(channel1=f"r{row}", channel2=f"c{column}")

        # Wait for relay settling
        session.wait_for_debounce(maximum_time_ms=1000)

        # Verify connection
        path = session.get_path(channel1=f"r{row}", channel2=f"c{column}")
        print(f"Path relays: {path}")

        # ... perform measurement here ...

        # Disconnect
        session.disconnect(channel1=f"r{row}", channel2=f"c{column}")

# Usage
connect_matrix_path("PXI1Slot6", row=0, column=5)
```

### Example 2: Sequential Scanning

Hardware-timed scan through multiple connections.

```python
import niswitch

def scan_matrix_rows(resource_name, num_rows=4, num_columns=8):
    """Scan through connections in a matrix."""
    with niswitch.Session(resource_name, topology="2529/2-Wire 4x32 Matrix") as session:
        # Build scan list
        scan_paths = []
        for row in range(num_rows):
            for col in range(num_columns):
                scan_paths.append(f"r{row}->c{col}")

        session.scan_list = "; ".join(scan_paths)
        session.scan_delay = hightime.timedelta(seconds=0.05)  # 50 ms per step
        session.scan_mode = niswitch.ScanMode.BREAK_BEFORE_MAKE

        # Execute scan
        with session.initiate():
            session.wait_for_scan_complete(maximum_time_ms=60000)

        print("Scan complete")

# Usage
scan_matrix_rows("Dev1", num_rows=4, num_columns=8)
```

### Example 3: Relay Life Monitoring

Monitor relay actuations for preventive maintenance.

```python
import niswitch

def check_relay_life(resource_name, topology, warn_threshold=500000):
    """Check actuation counts for all relays and warn on high usage."""
    with niswitch.Session(resource_name, topology=topology) as session:
        num_relays = session.number_of_relays

        relay_info = []
        for i in range(num_relays):
            relay_name = session.get_relay_name(index=i)
            count = session.get_relay_count(relay_name=relay_name)
            position = session.get_relay_position(relay_name=relay_name)

            status = "OK"
            if count > warn_threshold:
                status = "WARNING — nearing end of life"

            relay_info.append({
                "name": relay_name,
                "count": count,
                "position": "CLOSED" if position == niswitch.RelayPosition.CLOSED else "OPEN",
                "status": status,
            })

        return relay_info

# Usage
relays = check_relay_life("PXI1Slot6", "2737/2-Wire 4x64 Matrix")
for r in relays:
    print(f"{r['name']}: {r['count']} actuations [{r['status']}]")
```

### Example 4: Multi-Path Routing for Test System

```python
import niswitch

def route_dut_to_instruments(resource_name, topology, connections):
    """
    Route DUT pins to measurement instruments through a switch matrix.
    
    Args:
        connections: list of (row, column) tuples
    """
    with niswitch.Session(resource_name, topology=topology) as session:
        # Disconnect any existing paths
        session.disconnect_all()

        # Make all connections at once
        conn_list = "; ".join(f"r{r}->c{c}" for r, c in connections)
        session.connect_multiple(connection_list=conn_list)

        # Wait for all relays to settle
        session.wait_for_debounce(maximum_time_ms=2000)

        # ... perform measurements ...

        # Clean up
        session.disconnect_all()

# Usage
route_dut_to_instruments(
    "PXI1Slot6",
    "2529/2-Wire 4x32 Matrix",
    connections=[(0, 0), (1, 5), (2, 10), (3, 15)]
)
```

---

## Scanning

### Scan List Syntax

The scan list is a semicolon-separated list of connection pairs:

```
"r0->c0; r1->c1; r2->c2"
```

Arrow (`->`) indicates the connection direction (though switches are bidirectional). Semicolons separate steps.

### Scanning with External Trigger

```python
session.scan_list = "r0->c0; r1->c1; r2->c2"
session.trigger_input = niswitch.TriggerInput.PXI_TRIG0
session.scan_mode = niswitch.ScanMode.BREAK_BEFORE_MAKE

with session.initiate():
    # Switch advances to next connection on each trigger
    session.wait_for_scan_complete(maximum_time_ms=30000)
```

### Continuous Scanning

```python
session.scan_list = "r0->c0; r1->c1; r2->c2"
session.continuous_scan = True  # Loop back to beginning after last step
session.trigger_input = niswitch.TriggerInput.IMMEDIATE

with session.initiate():
    time.sleep(10)  # Run for 10 seconds
```

---

## Relay Control

### Direct Relay Control

For low-level relay manipulation (independent topologies):

```python
# Close a specific relay
session.relay_control(relay_name="k0", relay_action=niswitch.RelayAction.CLOSE)

# Open it
session.relay_control(relay_name="k0", relay_action=niswitch.RelayAction.OPEN)

# Wait for debounce
session.wait_for_debounce(maximum_time_ms=1000)
```

### Relay Naming

- Matrix relays: `"kr0c0"` (relay at row 0, column 0)
- Independent relays: `"k0"`, `"k1"`, etc.
- Multiplexer relays: depends on topology

---

## Driver-Specific Gotchas

1. **Topology is required**: Unlike most NI drivers, you must specify the `topology` parameter (or use `"Configured Topology"` to use the MAX setting). The topology must match the physical switch module.

2. **Channel naming depends on topology**: Matrix switches use `"r0"`, `"c0"` notation. Independent switches use `"ch0"`, `"ch1"`. Multiplexers may use `"com0"`, `"ch0"`. Consult your instrument's documentation.

3. **Break-before-make vs break-after-make**: Always use `BREAK_BEFORE_MAKE` for measurement applications to avoid short circuits. Use `BREAK_AFTER_MAKE` only when you must maintain power continuity (e.g., hot-switching loads).

4. **Relay lifetime is finite**: Electromechanical relays have lifetimes of 100,000 to 10,000,000 actuations depending on the model. Monitor with `get_relay_count()` and implement preventive replacement.

5. **Settling time matters**: After making/breaking connections, signals need time to settle. Always call `wait_for_debounce()` before making measurements. The settling time depends on signal type and switch model.

6. **Temperature monitoring**: High relay actuation rates generate heat. Monitor `temperature` during rapid scans. Excessive temperature can reduce relay life and affect contact resistance.

7. **Path notation**: The `"r0->c0"` notation indicates a connection (not signal direction). Switches are bidirectional. Semicolons separate independent connections in connection lists.

8. **`disconnect_all()` on session close**: Sessions do NOT automatically disconnect on close. Explicitly call `disconnect_all()` if you want relays to open, or use `reset()`.

9. **Scanning vs immediate**: For single connections use `connect()`/`disconnect()`. For sequences of connections that need hardware timing, use `scan_list` and `initiate()`.

10. **Matrix vs independent topologies**: `connect()` and `get_path()` work for matrix topologies. For independent relay topologies, use `relay_control()` directly.
