# nise Reference — NI Switch Executive Python API

**Package**: `nise` (via `pip install nise`)
**Runtime**: NI Switch Executive runtime (ni.com/downloads)
**Purpose**: High-level switch routing abstraction layer (uses `niswitch` under the hood)
**Current Version**: 1.4.x (nimi-python)
**Source**: [github.com/ni/nimi-python](https://github.com/ni/nimi-python)

## Table of Contents

1. [Overview](#overview)
2. [Session Creation](#session-creation)
3. [Key Enums](#key-enums)
4. [Core Methods](#core-methods)
5. [Canonical Examples](#canonical-examples)
6. [Key Concepts](#key-concepts)
7. [Driver-Specific Gotchas](#driver-specific-gotchas)

---

## Overview

NI Switch Executive (`nise`) provides a **high-level routing abstraction** on top of `niswitch`. Instead of working with physical relay names and channel addresses, you define named routes and route groups in the NI Switch Executive configuration tool, then connect/disconnect them by name in your code.

**When to use `nise` vs `niswitch`**:
- Use `nise` when you have predefined routes configured in NI Switch Executive and want simple connect/disconnect by name.
- Use `niswitch` when you need low-level relay control, direct matrix routing, or don't have NI Switch Executive configured.

**Key differences from other nimi-python drivers**:
- Session connects to a **virtual device** (configured in NI Switch Executive), not a physical instrument.
- **No session properties** — configuration is done at creation time and via the configuration tool.
- Very small API surface — only ~11 methods.

---

## Session Creation

```python
import nise

# Basic session — virtual device must be pre-configured in NI Switch Executive
with nise.Session(virtual_device_name="SwitchExecutiveExample") as session:
    pass

# With simulation
with nise.Session("SwitchExecutiveExample", options={"simulate": True}) as session:
    pass
```

**Important**: Virtual devices must be pre-configured using the NI Switch Executive configuration tool (part of the NI Switch Executive runtime). They cannot be created programmatically.

### Session Constructor Parameters

| Parameter             | Type   | Default  | Description                                          |
|-----------------------|--------|----------|------------------------------------------------------|
| `virtual_device_name` | str    | Required | Name of the NI Switch Executive virtual device       |
| `options`             | dict   | {}       | Session options: `simulate`, `cache`, `driver_setup`  |

### Options Dictionary Keys

| Key                       | Type | Default | Description                          |
|---------------------------|------|---------|--------------------------------------|
| `range_check`             | bool | True    | Enable range checking                |
| `query_instrument_status` | bool | False   | Query status after each API call     |
| `cache`                   | bool | True    | Enable attribute caching             |
| `simulate`                | bool | False   | Enable simulation mode               |
| `driver_setup`            | dict | {}      | Driver-specific setup                |

---

## Key Enums

### nise.ExpandAction

| Value    | Description                                              |
|----------|----------------------------------------------------------|
| `ROUTES` | Expand route groups to individual route names            |
| `PATHS`  | Expand to fully specified paths (square bracket format)  |

### nise.MulticonnectMode

| Value              | Description                                              |
|--------------------|----------------------------------------------------------|
| `DEFAULT`          | Use the default setting configured for the route         |
| `NO_MULTICONNECT`  | Route must be disconnected before reconnection           |
| `MULTICONNECT`     | Allow multiple connections; uses reference counting      |

### nise.OperationOrder

| Value    | Description                                                  |
|----------|--------------------------------------------------------------|
| `BEFORE` | Break Before Make — disconnect first, then connect (typical) |
| `AFTER`  | Break After Make — connect first, then disconnect            |

### nise.PathCapability

| Value                    | Description                                          |
|--------------------------|------------------------------------------------------|
| `PATH_NEEDS_HARDWIRE`    | Path requires physical hardwire                      |
| `PATH_NEEDS_CONFIG_CHANNEL` | Path needs configuration channel                  |
| `PATH_AVAILABLE`         | Path is available and can be connected               |
| `PATH_EXISTS`            | Path already exists (already connected)              |
| `PATH_UNSUPPORTED`       | Path not supported by hardware                       |
| `RESOURCE_IN_USE`        | Required resource currently in use                   |
| `EXCLUSION_CONFLICT`     | Channels cannot connect due to exclusion rules       |
| `CHANNEL_NOT_AVAILABLE`  | Channel not available as endpoint                    |
| `CHANNELS_HARDWIRED`     | Channels on same hardwire, implicit path exists      |

---

## Core Methods

### Connection Methods

```python
# Connect a route or route group
session.connect(
    connect_spec="DIOToUUT",
    multiconnect_mode=nise.MulticonnectMode.DEFAULT,
    wait_for_debounce=True
)

# Connect and disconnect atomically (prevents floating states)
session.connect_and_disconnect(
    connect_spec="NewRoute",
    disconnect_spec="OldRoute",
    multiconnect_mode=nise.MulticonnectMode.DEFAULT,
    operation_order=nise.OperationOrder.AFTER,
    wait_for_debounce=True
)

# Disconnect a route
session.disconnect(disconnect_spec="DIOToUUT")

# Disconnect all routes (resets all switch states)
session.disconnect_all()
```

### Query Methods

```python
# Check if a route is connected
is_connected = session.is_connected(route_spec="DIOToUUT")
# Returns: bool

# Check if all switches have settled
is_debounced = session.is_debounced()
# Returns: bool

# Wait for all switches to debounce
session.wait_for_debounce(maximum_time_ms=5000)
# Use -1 for infinite wait, 0 for immediate check

# Find a route between two channels
route_spec, capability = session.find_route(
    channel1="DMM1",
    channel2="Pin1"
)
# Returns: (str, PathCapability)

# Get all currently connected routes
all_connections = session.get_all_connections()
# Returns: str — route specification of all connected routes

# Expand a route spec to see individual connections
expanded = session.expand_route_spec(
    route_spec="MyRouteGroup",
    expand_action=nise.ExpandAction.ROUTES
)
# Returns: str — expanded route specification
```

---

## Canonical Examples

### Example 1: Connect a Route Group

```python
import nise

def connect_route(virtual_device, route_name):
    """Connect a predefined route group and verify."""
    with nise.Session(virtual_device) as session:
        # Connect
        session.connect(route_spec=route_name)

        # Wait for settling
        session.wait_for_debounce(maximum_time_ms=5000)

        # Verify
        if session.is_connected(route_spec=route_name):
            print(f"Route '{route_name}' is connected")

        # See what's actually connected
        expanded = session.expand_route_spec(
            route_spec=route_name,
            expand_action=nise.ExpandAction.PATHS
        )
        print(f"Expanded paths: {expanded}")

        # Disconnect when done
        session.disconnect(disconnect_spec=route_name)

# Usage
connect_route("MyTestSystem", "DIOToUUT")
```

### Example 2: Sequential Route Measurement

Step through multiple routes, performing measurements at each.

```python
import nise
import time

def measure_through_routes(virtual_device, route_sequence, measure_func):
    """
    Connect routes sequentially and call a measurement function at each.
    
    Args:
        virtual_device: NI Switch Executive virtual device name
        route_sequence: list of route specification strings
        measure_func: callable that performs a measurement and returns result
    """
    results = {}
    with nise.Session(virtual_device) as session:
        for route in route_sequence:
            session.connect(route_spec=route)
            session.wait_for_debounce(maximum_time_ms=2000)

            # Perform measurement
            results[route] = measure_func()

            session.disconnect(disconnect_spec=route)
            session.wait_for_debounce(maximum_time_ms=2000)

    return results

# Usage
routes = ["DMM_To_Pin1", "DMM_To_Pin2", "DMM_To_Pin3", "DMM_To_Pin4"]
results = measure_through_routes("MyTestSystem", routes, my_dmm_measure)
```

### Example 3: Atomic Route Switching

Switch between routes without any gap where neither is connected.

```python
import nise

def switch_routes(virtual_device, old_route, new_route):
    """Atomically switch from one route to another (no gap)."""
    with nise.Session(virtual_device) as session:
        # Initial connection
        session.connect(route_spec=old_route)
        session.wait_for_debounce(maximum_time_ms=3000)

        # Atomic switch: connect new, then disconnect old
        session.connect_and_disconnect(
            connect_spec=new_route,
            disconnect_spec=old_route,
            operation_order=nise.OperationOrder.AFTER  # Connect first, then disconnect
        )
        session.wait_for_debounce(maximum_time_ms=3000)

        print(f"Old route connected: {session.is_connected(old_route)}")  # False
        print(f"New route connected: {session.is_connected(new_route)}")  # True

        session.disconnect_all()

# Usage
switch_routes("MyTestSystem", "DMM_To_Pin1", "DMM_To_Pin2")
```

### Example 4: Route Discovery

Find available routes between instruments and DUT pins.

```python
import nise

def find_available_routes(virtual_device, source, destinations):
    """Find which routes are available from a source to multiple destinations."""
    with nise.Session(virtual_device) as session:
        available = []
        for dest in destinations:
            route_spec, capability = session.find_route(
                channel1=source,
                channel2=dest
            )

            if capability == nise.PathCapability.PATH_AVAILABLE:
                available.append({"dest": dest, "route": route_spec})
                print(f"{source} -> {dest}: AVAILABLE ({route_spec})")
            elif capability == nise.PathCapability.PATH_EXISTS:
                print(f"{source} -> {dest}: ALREADY CONNECTED")
            elif capability == nise.PathCapability.RESOURCE_IN_USE:
                print(f"{source} -> {dest}: RESOURCE IN USE")
            else:
                print(f"{source} -> {dest}: NOT AVAILABLE ({capability})")

        return available

# Usage
destinations = ["Pin1", "Pin2", "Pin3", "Pin4"]
available = find_available_routes("MyTestSystem", "DMM1", destinations)
```

### Example 5: Multiconnect Reference Counting

```python
import nise

def multiconnect_example(virtual_device):
    """Demonstrate multiconnect reference counting."""
    with nise.Session(virtual_device) as session:
        # First connect — physically connects the route
        session.connect("SharedRoute", multiconnect_mode=nise.MulticonnectMode.MULTICONNECT)
        print(f"Connected: {session.is_connected('SharedRoute')}")  # True

        # Second connect — increments reference count (no hardware action)
        session.connect("SharedRoute", multiconnect_mode=nise.MulticonnectMode.MULTICONNECT)

        # First disconnect — decrements count to 1 (no hardware action)
        session.disconnect("SharedRoute")
        print(f"Still connected: {session.is_connected('SharedRoute')}")  # True

        # Second disconnect — decrements count to 0, physically disconnects
        session.disconnect("SharedRoute")
        print(f"Now disconnected: {session.is_connected('SharedRoute')}")  # False
```

---

## Key Concepts

### Route Specification Syntax

Route specs are flexible strings:
- **Route name**: `"DIOToUUT"` — a named route defined in configuration
- **Route group**: `"MyRouteGroup"` — a group of routes
- **Combined**: `"Route1 & Route2"` — multiple routes/groups with `&`
- **Fully specified path**: `"[A->Switch1/r0->B]"` — explicit channel-relay-channel path

### Multiconnect Reference Counting

When using `MulticonnectMode.MULTICONNECT`:
1. First `connect()` physically closes the relays
2. Subsequent `connect()` calls increment a reference count (no hardware action)
3. Each `disconnect()` decrements the counter
4. Physical disconnect occurs only when count reaches 0

This is useful when multiple subsystems share the same route and need independent lifetime management.

### Break Before Make vs Break After Make

- **`BEFORE` (default)**: Disconnect old route first, then connect new. Prevents short circuits. Use for most measurement applications.
- **`AFTER`**: Connect new route first, then disconnect old. Maintains continuous connection. Use when you must not lose power/signal (e.g., powering a DUT).

---

## Driver-Specific Gotchas

1. **Virtual devices must be pre-configured**: Unlike `niswitch`, you cannot create switch configurations programmatically. Use the NI Switch Executive configuration tool to define virtual devices, routes, and route groups before coding.

2. **Route names are arbitrary strings**: Route names are defined in your Switch Executive configuration. There are no standard names — they depend entirely on your test system design.

3. **No session properties**: The `nise` API has no readable/writable properties. All configuration is done at creation time or through the configuration tool.

4. **Sessions do NOT disconnect on close**: Routes remain connected when the session closes. You must explicitly call `disconnect_all()` if you want to open all relays on exit.

5. **Multiconnect conflicts**: With `NO_MULTICONNECT`, attempting to connect a route that shares a resource with an existing connection will fail. Use `find_route()` to check availability first.

6. **Always wait for debounce before measuring**: Relays need settling time after switching. Call `wait_for_debounce()` or set `wait_for_debounce=True` in `connect()` before making any measurements.

7. **`connect_and_disconnect()` atomicity**: This method optimizes hardware operations — it only actuates relays that differ between the connect and disconnect specs, improving throughput and reducing relay wear.

8. **Limited error detail**: `nise` errors are high-level abstractions. For detailed switch diagnostics (relay counts, positions, temperatures), use `niswitch` directly.

9. **Single process per virtual device**: Only one process can have a session open to a given virtual device at a time. Multiple threads within the same process can share the session (thread-safe).

10. **`expand_route_spec()` for debugging**: Use `PATHS` expand action to see exactly which physical relay paths are being used — invaluable for debugging routing issues.
