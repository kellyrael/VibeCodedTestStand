---
name: ni-measurement-data-services
description: >
  Generate correct Python code for logging measurement data to NI Measurement Data Services (MDS)
  using the ni.datastore package. Covers the DataStoreClient and MetadataStoreClient APIs for
  creating test results, steps, publishing measurements and conditions, querying data, and
  registering metadata (UUTs, operators, test stations, hardware items, software items).
  Use this skill whenever the user mentions MDS, Measurement Data Services, ni.datastore,
  DataStoreClient, data logging, test results, publishing measurements, or asks to store
  measurement data in a centralized data service. Also trigger when the user asks about
  querying historical test results, conditions, or measurement data from MDS.
---

# NI Measurement Data Services (MDS) Skill

This skill helps generate correct Python code for publishing and retrieving measurement data
using the `ni.datastore` package — the Python SDK for NI Measurement Data Services.

## Why this skill exists

The MDS API has a specific data model (TestResult → Step → Measurement/Condition) with
required relationships between entities. LLMs frequently get the hierarchy wrong, skip
required steps (e.g., creating a TestResult before a Step), or invent non-existent methods.
This skill encodes the verified API patterns from the actual `ni.datastore` v1.0.0 source.

## Package Info

| Field | Value |
|-------|-------|
| **Package** | `ni.datastore` (installed as `ni.datastore`) |
| **Version** | 1.0.0 |
| **Dependencies** | `hightime`, `ni-datamonikers-v1-client`, `ni-measurements-data-v1-client`, `ni-measurements-metadata-v1-client`, `ni-protobuf-types`, `protobuf` |
| **Requires** | MDS gRPC service running locally (part of NI SystemLink / MDS installation) |

### Installation

```
pip install ni.datastore
```

The MDS gRPC service must be running on the system. The client uses the NI Discovery Service
to locate the MDS endpoint automatically.

---

## Data Model

MDS organizes data in a strict hierarchy:

```
MetadataStoreClient (metadata about the test environment)
├── Uut                    — Unit Under Test definition (e.g. "Argus PMIC")
├── UutInstance             — Specific serial / instance of a UUT
├── Operator                — Person running the test
├── TestStation             — Machine / system running the test
├── TestDescription         — Describes what a test does
├── Test                    — A test definition
├── HardwareItem            — Instrument metadata (e.g. "PXIe-4162")
├── SoftwareItem            — Software metadata (e.g. "nidcpower 1.5.0")
├── TestAdapter             — Test framework adapter
└── ExtensionSchema         — Schema for custom extension fields

DataStoreClient (actual measurement data)
├── TestResult              — Top-level container for one test execution
│   ├── Step                — Logical grouping within a test result
│   │   ├── PublishedMeasurement  — A named measurement value
│   │   └── PublishedCondition    — A named condition/parameter value
│   └── Step (nested)       — Steps can form hierarchies via parent_step_id
```

### Key Rule: You must create entities top-down

1. Create a `TestResult` first → get `test_result_id`
2. Create a `Step` referencing that `test_result_id` → get `step_id`
3. Publish measurements and conditions referencing that `step_id`

Skipping any level will fail.

---

## Two Clients

### DataStoreClient — Publishing & Reading Measurement Data

```python
from ni.datastore.data import DataStoreClient

# Default: auto-discovers MDS via NI Discovery Service
with DataStoreClient() as client:
    # create test results, steps, publish measurements...
    pass
```

### MetadataStoreClient — Registering Test Environment Metadata

```python
from ni.datastore.metadata import MetadataStoreClient

with MetadataStoreClient() as meta_client:
    # create UUTs, operators, test stations, hardware items...
    pass
```

Both support context managers and should always be used with `with`.

---

## Core Types — Data Module

### Outcome (Enum)

```python
from ni.datastore.data import Outcome

Outcome.UNSPECIFIED      # Default — not specified
Outcome.PASSED           # Test/measurement passed
Outcome.FAILED           # Test/measurement failed
Outcome.INDETERMINATE    # Inconclusive
```

### TestResult

Top-level container for a single test execution.

```python
from ni.datastore.data import TestResult, Outcome
import hightime as ht

test_result = TestResult(
    name="Load Regulation Test",
    start_date_time=ht.datetime.now(),
    outcome=Outcome.PASSED,
    # Optional metadata links:
    uut_instance_id="...",         # ID from MetadataStoreClient.create_uut_instance()
    operator_id="...",             # ID from MetadataStoreClient.create_operator()
    test_station_id="...",         # ID from MetadataStoreClient.create_test_station()
    test_description_id="...",     # ID from MetadataStoreClient.create_test_description()
    hardware_item_ids=["..."],     # IDs from MetadataStoreClient.create_hardware_item()
    software_item_ids=["..."],     # IDs from MetadataStoreClient.create_software_item()
    extension={"custom_key": "custom_value"},  # Custom key-value metadata
)
```

### Step

A logical grouping within a TestResult. Steps can be nested.

```python
from ni.datastore.data import Step, Outcome
import hightime as ht

step = Step(
    name="Voltage Sweep",
    test_result_id=test_result_id,    # REQUIRED — must reference a created TestResult
    step_type="Measurement",           # Freeform category string
    notes="Sweeping load current 0-2A",
    start_date_time=ht.datetime.now(),
    outcome=Outcome.PASSED,
    # For nested steps:
    parent_step_id="...",              # ID of parent step (optional)
)
```

### ErrorInformation

```python
from ni.datastore.data import ErrorInformation

error = ErrorInformation(
    error_code=-1,
    error_message="Compliance limit reached",
)
```

---

## DataStoreClient Methods

### create_test_result(test_result) → str

Creates a test result. Returns the `test_result_id`.

```python
test_result_id = client.create_test_result(test_result)
```

### create_step(step) → str

Creates a step under a test result. Returns the `step_id`.

```python
step_id = client.create_step(step)
```

### publish_measurement(name, value, step_id, ...) → str

Publish a single measurement value to a step.

```python
measurement_id = client.publish_measurement(
    name="Vout",                          # Measurement name (used for grouping)
    value=3.2856,                         # Scalar: float, int, str, bool
    step_id=step_id,                      # REQUIRED
    timestamp=ht.datetime.now(),          # Optional (defaults to current time)
    outcome=Outcome.PASSED,               # Optional
    error_information=None,               # Optional
    hardware_item_ids=["..."],            # Optional
    notes="Measured at no-load",          # Optional
)
```

**Supported value types for `publish_measurement`:**
- **Scalar**: `float`, `int`, `str`, `bool`
- **Vector**: list/array of float, int, str, or bool
- **DoubleAnalogWaveform**: Analog waveform with double precision
- **DoubleXYData**: XY coordinate data
- **I16AnalogWaveform**: Analog waveform with 16-bit integer precision
- **DoubleComplexWaveform**: Complex waveform
- **I16ComplexWaveform**: Complex waveform (16-bit)
- **DoubleSpectrum**: Frequency spectrum data
- **DigitalWaveform**: Digital waveform data

### publish_measurement_batch(name, values, step_id, ...) → Sequence[str]

Publish N scalar values at once (ideal for parametric sweeps).

```python
vout_values = [3.300, 3.298, 3.295, 3.291, 3.288]  # One per sweep point

measurement_ids = client.publish_measurement_batch(
    name="Vout",
    values=vout_values,                    # Vector of N scalars
    step_id=step_id,
    timestamps=[...],                      # Optional: empty, 1, or N timestamps
    outcomes=[Outcome.PASSED] * len(vout_values),  # Optional: empty, 1, or N
    notes="Load regulation sweep data",
)
```

### publish_condition(name, condition_type, value, step_id) → str

Publish a condition (test parameter/setting) to a step.

```python
condition_id = client.publish_condition(
    name="Vin",                    # Condition name
    condition_type="Setup",        # Category: "Setup", "Environment", "Limit", etc.
    value=3.3,                     # Scalar value
    step_id=step_id,
)
```

### publish_condition_batch(name, condition_type, values, step_id) → str

Publish N condition values at once.

```python
condition_id = client.publish_condition_batch(
    name="Temperature",
    condition_type="Environment",
    values=[25.0, 25.1, 25.0, 24.9],
    step_id=step_id,
)
```

### read_data(moniker_source, expected_type=None) → object

Read back published data using a moniker.

```python
# From a PublishedMeasurement or PublishedCondition
published = client.get_measurement(measurement_id)
data = client.read_data(published)  # Returns the value

# With type checking
data = client.read_data(published, expected_type=list)
```

### Query Methods

All query methods accept OData query strings:

```python
# Query test results
results = client.query_test_results("$filter=name eq 'Load Regulation Test'")
results = client.query_test_results()  # All results

# Query steps
steps = client.query_steps("$filter=test_result_id eq 'some-guid'")

# Query measurements
measurements = client.query_measurements("$filter=name eq 'Vout'")

# Query conditions
conditions = client.query_conditions("$filter=condition_type eq 'Setup'")
```

### Getter Methods

```python
test_result = client.get_test_result(test_result_id)
step = client.get_step(step_id)
measurement = client.get_measurement(measurement_id)
condition = client.get_condition(condition_id)
```

---

## MetadataStoreClient Methods

All metadata types follow the same pattern: `create_*()`, `get_*()`, `query_*()`.

### Register a UUT and Instance

```python
from ni.datastore.metadata import MetadataStoreClient, Uut, UutInstance

with MetadataStoreClient() as meta:
    uut_id = meta.create_uut(Uut(name="Argus PMIC", part_number="ARGUS-001"))
    uut_instance_id = meta.create_uut_instance(
        UutInstance(uut_id=uut_id, serial_number="SN-12345")
    )
```

### Register an Operator

```python
from ni.datastore.metadata import Operator

operator_id = meta.create_operator(Operator(name="Demo User"))
```

### Register a Test Station

```python
from ni.datastore.metadata import TestStation

station_id = meta.create_test_station(TestStation(name="PXIe-1092 Demo Rig"))
```

### Register Hardware / Software Items

```python
from ni.datastore.metadata import HardwareItem, SoftwareItem

hw_id = meta.create_hardware_item(HardwareItem(
    name="PXIe-4162",
    model="PXIe-4162",
    serial_number="01A2B3C4",
))

sw_id = meta.create_software_item(SoftwareItem(
    name="nidcpower",
    version="1.5.0",
))
```

### Register a Test Description

```python
from ni.datastore.metadata import TestDescription

td_id = meta.create_test_description(TestDescription(
    name="PMIC Load Regulation",
    description="Sweeps load current and measures Vout regulation %",
))
```

---

## Complete Example: Log a Measurement Sweep to MDS

```python
import hightime as ht
from ni.datastore.data import DataStoreClient, TestResult, Step, Outcome

def log_load_regulation_to_mds(
    test_name: str,
    vin: float,
    iload_values: list[float],
    vout_values: list[float],
    regulation_pct: float,
    passed: bool,
) -> str:
    """Publish load regulation results to MDS.
    
    Returns the test_result_id for reference.
    """
    outcome = Outcome.PASSED if passed else Outcome.FAILED

    with DataStoreClient() as client:
        # 1. Create test result
        test_result = TestResult(
            name=test_name,
            start_date_time=ht.datetime.now(),
            outcome=outcome,
        )
        test_result_id = client.create_test_result(test_result)

        # 2. Create step for the sweep
        step = Step(
            name="Load Current Sweep",
            test_result_id=test_result_id,
            step_type="Measurement",
            start_date_time=ht.datetime.now(),
            outcome=outcome,
        )
        step_id = client.create_step(step)

        # 3. Publish conditions (test setup parameters)
        client.publish_condition("Vin", "Setup", vin, step_id)
        client.publish_condition("Iload Start", "Setup", iload_values[0], step_id)
        client.publish_condition("Iload Stop", "Setup", iload_values[-1], step_id)

        # 4. Publish sweep data as batches
        client.publish_measurement_batch("Vout", vout_values, step_id)
        client.publish_measurement_batch("Iload", iload_values, step_id)

        # 5. Publish summary scalar
        client.publish_measurement(
            "Load Regulation %",
            regulation_pct,
            step_id,
            outcome=outcome,
        )

        return test_result_id
```

## Complete Example: Query and Read Back Data

```python
from ni.datastore.data import DataStoreClient

def read_latest_results(test_name: str):
    """Query MDS for the latest results of a named test."""
    with DataStoreClient() as client:
        # Find test results by name
        results = client.query_test_results(
            f"$filter=name eq '{test_name}'&$orderby=start_date_time desc"
        )
        
        if not results:
            print(f"No results found for '{test_name}'")
            return

        latest = results[0]
        print(f"Test: {latest.name}")
        print(f"Outcome: {latest.outcome.name}")
        print(f"Time: {latest.start_date_time}")

        # Get steps for this result
        steps = client.query_steps(
            f"$filter=test_result_id eq '{latest.id}'"
        )
        
        for step in steps:
            print(f"\n  Step: {step.name} ({step.outcome.name})")
            
            # Get measurements for this step
            measurements = client.query_measurements(
                f"$filter=step_id eq '{step.id}'"
            )
            for m in measurements:
                data = client.read_data(m)
                print(f"    {m.name}: {data}")
```

## Complete Example: Full Metadata + Data Pipeline

```python
import hightime as ht
from ni.datastore.data import DataStoreClient, TestResult, Step, Outcome
from ni.datastore.metadata import (
    MetadataStoreClient, Uut, UutInstance, Operator,
    TestStation, HardwareItem, TestDescription,
)

def full_mds_pipeline():
    """Register metadata and publish measurement data."""
    
    # --- Register metadata (typically done once per setup) ---
    with MetadataStoreClient() as meta:
        uut_id = meta.create_uut(Uut(name="Argus PMIC"))
        uut_instance_id = meta.create_uut_instance(
            UutInstance(uut_id=uut_id, serial_number="ARGUS-001")
        )
        operator_id = meta.create_operator(Operator(name="Demo User"))
        station_id = meta.create_test_station(TestStation(name="PXIe Demo Rig"))
        hw_id = meta.create_hardware_item(HardwareItem(
            name="PXIe-4162", model="PXIe-4162"
        ))
        td_id = meta.create_test_description(TestDescription(
            name="PMIC Load Regulation",
            description="Measures Vout vs load current",
        ))

    # --- Publish results ---
    with DataStoreClient() as client:
        test_result_id = client.create_test_result(TestResult(
            name="Load Regulation – Argus PMIC",
            start_date_time=ht.datetime.now(),
            outcome=Outcome.PASSED,
            uut_instance_id=uut_instance_id,
            operator_id=operator_id,
            test_station_id=station_id,
            test_description_id=td_id,
            hardware_item_ids=[hw_id],
        ))

        step_id = client.create_step(Step(
            name="Load Sweep 0-2A",
            test_result_id=test_result_id,
            outcome=Outcome.PASSED,
        ))

        # Conditions
        client.publish_condition("Vin", "Setup", 3.3, step_id)

        # Measurements
        client.publish_measurement_batch(
            "Vout", [3.300, 3.298, 3.295, 3.291], step_id
        )
        client.publish_measurement(
            "Regulation %", 0.27, step_id, outcome=Outcome.PASSED
        )
```

---

## Common Mistakes to Avoid

1. **Skipping TestResult creation**: You cannot create a Step without a valid `test_result_id`. Always create TestResult first.
2. **Skipping Step creation**: You cannot publish measurements or conditions without a valid `step_id`. Always create a Step first.
3. **Not using context managers**: Both `DataStoreClient` and `MetadataStoreClient` manage gRPC connections. Always use `with`.
4. **Using `datetime` instead of `hightime.datetime`**: MDS uses `hightime.datetime` for high-precision timestamps. Import `hightime as ht` and use `ht.datetime.now(timezone.utc)`. **Always pass `timezone.utc` explicitly** — `ht.datetime.now()` without a timezone produces a naive datetime that the MDS stack rejects with `ValueError: The tzinfo must be datetime.timezone.utc.` Always import `from datetime import timezone` alongside hightime.
5. **Forgetting that MDS must be running**: The clients use gRPC to connect to a local MDS service. If MDS isn't running, you'll get a connection error.
6. **Mixing up Data vs Metadata clients**: `DataStoreClient` is for test results, steps, measurements, conditions. `MetadataStoreClient` is for UUTs, operators, stations, hardware items, etc.
7. **Using wrong ID types in queries**: All IDs are strings (GUIDs). OData queries filter on string fields.
8. **OData field names are PascalCase, Python SDK attributes are snake_case**: When querying MDS via OData HTTP endpoints, field names must be PascalCase (e.g., `StartDateTime`, `UutInstanceId`, `Outcome`). The Python SDK returns typed objects whose attributes use snake_case (e.g., `result.start_date_time`, `result.uut_instance_id`). Do not use snake_case in OData `$filter` expressions.
9. **Forgetting `publish_measurement_batch` returns a sequence**: Even though it currently returns a single measurement ID in the sequence, treat it as a sequence for forward compatibility.
9. **Starting or instantiating a local MDS service in code**: NEVER spawn, start, or construct an MDS service process or gRPC server in generated code. The MDS service is a system-installed Windows service managed by NI. Always connect to it by calling `DataStoreClient()` and `MetadataStoreClient()` with no arguments — they auto-discover the running system service via the NI Discovery Service. Do not hard-code gRPC channel addresses, ports, or host names.
