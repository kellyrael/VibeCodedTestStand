# MDS Python API Skill

## Overview

The `ni.datastore` Python package provides APIs for publishing and retrieving test data from
the **NI Measurement Data Store (MDS)**. It targets CPython 3.10+ on Windows and Linux and
requires **NI Measurement Data Services 2026 Q3** (or later) installed on the system.

**PyPI:** `pip install --pre "ni.datastore>=2.0.0.dev0,<3"` (latest 2.0 prerelease)

Two sub-packages cover the two backend services:

| Sub-package | Service | Purpose |
|---|---|---|
| `ni.datastore.data` | DataStoreService | Publish & query test execution data (TestResult, Step, measurements, conditions) |
| `ni.datastore.metadata` | MetadataStoreService | Publish & query test context metadata (operators, stations, UUTs, hardware, software …) |

---

## Required Imports

```python
# Data store
from ni.datastore.data import (
    DataStoreClient,
    Step,
    TestResult,
    PublishedMeasurement,
    PublishedCondition,
    Outcome,
    ErrorInformation,
)

# Metadata store
from ni.datastore.metadata import (
    MetadataStoreClient,
    Operator,
    TestStation,
    HardwareItem,
    SoftwareItem,
    Uut,
    UutInstance,
    TestDescription,
    Test,
    TestAdapter,
    ExtensionSchema,
    Alias,
)

# Common measurement types (from companion packages)
from nitypes.waveform import AnalogWaveform, Timing
from nitypes.vector import Vector
from nitypes.scalar import Scalar
from nitypes.spectrum import Spectrum
import hightime as ht
import numpy as np
from datetime import timezone
```

---

## Client Lifecycle

Both `DataStoreClient` and `MetadataStoreClient` are context managers. Always prefer the
`with` statement so gRPC channels are closed automatically.

```python
# Preferred — automatic cleanup
with MetadataStoreClient() as metadata_store_client, DataStoreClient() as data_store_client:
    ...

# Manual lifecycle (less common)
client = DataStoreClient()
try:
    ...
finally:
    client.close()
```

---

## Data Model Hierarchy

```
TestResult          ← top-level session (who/what/where/when)
├── Step            ← logical grouping of related measurements
│   ├── PublishedMeasurement  ← actual measured value (scalar, waveform, …)
│   └── PublishedCondition    ← environmental/setup context for the step
└── Step
    └── ...
```

The **MetadataStore** entities (Operator, TestStation, Uut, UutInstance, …) are referenced
by ID inside a `TestResult` but are managed separately and reused across many test results.

---

## Complete Workflow

### Phase 1 — Setup (register metadata once, reuse everywhere)

```python
with MetadataStoreClient() as metadata_store_client:
    # --- WHO ---
    operator_id = metadata_store_client.create_operator(Operator(name="Jane Smith", role="Test Engineer"))

    # --- WHERE ---
    station_id = metadata_store_client.create_test_station(TestStation(name="Station_A1", asset_identifier="STA-001"))

    # --- WHAT (product model) ---
    uut_id = metadata_store_client.create_uut(Uut(model_name="PowerSupply v2.1", family="Power"))
    # WHAT (specific physical unit)
    uut_instance_id = metadata_store_client.create_uut_instance(
        UutInstance(uut_id=uut_id, serial_number="PS-2024-001")
    )

    # --- HOW (equipment) ---
    dmm_id = metadata_store_client.create_hardware_item(HardwareItem(
        manufacturer="NI", model="PXIe-4081", serial_number="DMM-001",
        calibration_due_date="2025-06-15",
    ))
    scope_id = metadata_store_client.create_hardware_item(HardwareItem(
        manufacturer="NI", model="PXIe-5171", serial_number="SCOPE-001",
    ))

    # --- HOW (software) ---
    python_id = metadata_store_client.create_software_item(SoftwareItem(product="Python", version="3.12"))
    driver_id = metadata_store_client.create_software_item(SoftwareItem(product="NI-DAQmx", version="23.3.0"))

    # --- Aliases (optional — human-readable references) ---
    metadata_store_client.create_alias("Production_DMM", dmm)          # alias → HardwareItem object
    metadata_store_client.create_alias("Lead_Engineer", operator)       # alias → Operator object
```

### Phase 2 — Test Execution (publish data)

```python
with DataStoreClient() as data_store_client:
    # 1. Create a TestResult session
    test_result_id = data_store_client.create_test_result(TestResult(
        name="PowerSupply PS-2024-001 Validation",
        uut_instance_id=uut_instance_id,
        operator_id=operator_id,           # GUID or alias name
        test_station_id=station_id,        # GUID or alias name
        software_item_ids=[python_id, driver_id],
        hardware_item_ids=[dmm_id, scope_id],
    ))

    # 2. Create a Step within the TestResult
    step_id = data_store_client.create_step(Step(
        name="DC Voltage Accuracy Check",
        test_result_id=test_result_id,
        notes="Testing 5 V output under no load",
    ))

    # 3. Publish conditions (environmental / setup context)
    data_store_client.publish_condition(
        name="Ambient Temperature",
        condition_type="Environment",
        value=23.5,                        # scalar float
        step_id=step_id,
    )
    data_store_client.publish_condition(
        name="Supply Voltage",
        condition_type="Input Parameter",
        value=Scalar(value=120.0, units="V"),
        step_id=step_id,
    )

    # 4. Publish a single measurement
    measurement_id = data_store_client.publish_measurement(
        name="5V Output Voltage",
        value=5.023,                       # scalar; see Supported Value Types below
        step_id=step_id,
        outcome=Outcome.PASSED,
        hardware_item_ids=[dmm_id],
        notes="DMM reading at no load",
    )

    # 4b. Publish a waveform measurement
    waveform = AnalogWaveform(
        sample_count=1000,
        raw_data=np.zeros(1000),
        timing=Timing.create_with_regular_interval(
            ht.timedelta(seconds=1e-6),
            ht.datetime.now(timezone.utc),
        ),
    )
    waveform_id = data_store_client.publish_measurement(
        name="Output Ripple Waveform",
        value=waveform,
        step_id=step_id,
        outcome=Outcome.PASSED,
        hardware_item_ids=[scope_id],
    )

    # 4c. Publish a parametric batch (sweep)
    measurement_ids = data_store_client.publish_measurement_batch(
        name="Load Regulation Sweep",
        values=[5.025, 5.023, 5.021, 5.019, 5.018],  # scalar list or Vector
        step_id=step_id,
        outcomes=[Outcome.PASSED] * 5,
        hardware_item_ids=[dmm_id],
    )
    # Corresponding conditions for the sweep
    data_store_client.publish_condition_batch(
        name="Load Current",
        condition_type="Test Parameter",
        values=[0.0, 2.5, 5.0, 7.5, 10.0],
        step_id=step_id,
    )
```

### Phase 3 — Analysis (query & read data)

```python
with MetadataStoreClient() as metadata_store_client, DataStoreClient() as data_store_client:
    # Query measurements with OData
    measurements = data_store_client.query_measurements("$filter=name eq '5V Output Voltage'")
    failed = data_store_client.query_measurements("$filter=outcome eq 'Failed'")
    recent = data_store_client.query_measurements("$filter=startDateTime gt 2024-01-01T00:00:00Z")
    in_result = data_store_client.query_measurements(f"$filter=testResultId eq {test_result_id}")

    # Read the actual data from a PublishedMeasurement
    for measurement in measurements:
        waveform = data_store_client.read_measurement_value(measurement, expected_type=AnalogWaveform)
        vector   = data_store_client.read_measurement_value(measurement, expected_type=Vector)

    # Navigate the hierarchy
    measurement = data_store_client.get_measurement(measurement_id)
    step        = data_store_client.get_step(measurement.step_id)
    test_result = data_store_client.get_test_result(measurement.test_result_id)

    # Cross-reference metadata
    uut_instance = metadata_store_client.get_uut_instance(test_result.uut_instance_id)
    uut          = metadata_store_client.get_uut(uut_instance.uut_id)
    operator     = metadata_store_client.get_operator(test_result.operator_id)

    # Query other entity types
    steps        = data_store_client.query_steps(f"$filter=testResultId eq {test_result_id}")
    conditions   = data_store_client.query_conditions(f"$filter=stepId eq {step_id}")
    test_results = data_store_client.query_test_results("$filter=outcome eq 'Failed'")

    # Query metadata entities
    operators   = metadata_store_client.query_operators("$filter=name eq 'Jane Smith'")
    hw_items    = metadata_store_client.query_hardware_items()
    uut_insts   = metadata_store_client.query_uut_instances(f"$filter=uutId eq '{uut_id}'")
```

---

## Supported Value Types for `publish_measurement`

| Python / nitypes type | MDS wire type |
|---|---|
| `bool` | Scalar |
| `int`, `float` | Scalar → stored as Vector |
| `str` | Scalar |
| `list[bool/int/float/str]` | Vector |
| `nitypes.vector.Vector` | Vector |
| `nitypes.scalar.Scalar` | Scalar |
| `nitypes.waveform.AnalogWaveform` | DoubleAnalogWaveform or I16AnalogWaveform |
| `nitypes.waveform.ComplexWaveform` | DoubleComplexWaveform or I16ComplexWaveform |
| `nitypes.waveform.DigitalWaveform` | DigitalWaveform |
| `nitypes.spectrum.Spectrum` | DoubleSpectrum |
| `nitypes.xydata.XYData` | DoubleXYData |

Pass the same type to `read_measurement_value(measurement, expected_type=<Type>)` to decode. The `expected_type` argument is optional; omit it to get an `object` back, or supply it to get a typed result and automatic `TypeError` on mismatch. Use `read_condition_value(condition, expected_type=<Type>)` for conditions.

---

## MetadataStoreClient — Full Method Reference

```text
# UUT Instance
create_uut_instance(uut_instance: UutInstance) -> str
get_uut_instance(uut_instance_id: str) -> UutInstance
query_uut_instances(odata_query: str = "") -> Sequence[UutInstance]

# UUT
create_uut(uut: Uut) -> str
get_uut(uut_id: str) -> Uut
query_uuts(odata_query: str = "") -> Sequence[Uut]

# Operator
create_operator(operator: Operator) -> str
get_operator(operator_id: str) -> Operator
query_operators(odata_query: str = "") -> Sequence[Operator]

# TestStation
create_test_station(test_station: TestStation) -> str
get_test_station(test_station_id: str) -> TestStation
query_test_stations(odata_query: str = "") -> Sequence[TestStation]

# HardwareItem
create_hardware_item(hardware_item: HardwareItem) -> str
get_hardware_item(hardware_item_id: str) -> HardwareItem
query_hardware_items(odata_query: str = "") -> Sequence[HardwareItem]

# SoftwareItem
create_software_item(software_item: SoftwareItem) -> str
get_software_item(software_item_id: str) -> SoftwareItem
query_software_items(odata_query: str = "") -> Sequence[SoftwareItem]

# TestDescription
create_test_description(test_description: TestDescription) -> str
get_test_description(test_description_id: str) -> TestDescription
query_test_descriptions(odata_query: str = "") -> Sequence[TestDescription]

# Test
create_test(test: Test) -> str
get_test(test_id: str) -> Test
query_tests(odata_query: str = "") -> Sequence[Test]

# TestAdapter
create_test_adapter(test_adapter: TestAdapter) -> str
get_test_adapter(test_adapter_id: str) -> TestAdapter
query_test_adapters(odata_query: str = "") -> Sequence[TestAdapter]

# ExtensionSchema
register_schema(schema_contents: str) -> str          # returns schema_id
register_schema_from_file(path: Path | str) -> str
list_schemas() -> Sequence[ExtensionSchema]

# Alias
create_alias(alias_name: str, alias_target: <metadata entity>) -> Alias
get_alias(alias_name: str) -> Alias
query_aliases(odata_query: str = "") -> Sequence[Alias]
delete_alias(alias_name: str) -> bool

# Bulk load from JSON
create_from_json_file(metadata_file_path: Path | str) -> MetadataItems
create_from_json(metadata_file_contents: str) -> MetadataItems
```

---

## DataStoreClient — Full Method Reference

```text
# TestResult
create_test_result(test_result: TestResult) -> str
get_test_result(test_result_id: str) -> TestResult
query_test_results(odata_query: str = "") -> Sequence[TestResult]

# Step
create_step(step: Step) -> str
get_step(step_id: str) -> Step
query_steps(odata_query: str = "") -> Sequence[Step]

# Publish measurements
publish_measurement(
    name: str,
    value: object,
    step_id: str,
    timestamp: ht.datetime | None = None,
    outcome: Outcome = Outcome.UNSPECIFIED,
    error_information: ErrorInformation | None = None,
    hardware_item_ids: Iterable[str] = (),
    test_adapter_ids: Iterable[str] = (),
    software_item_ids: Iterable[str] = (),
    notes: str = "",
) -> str

publish_measurement_batch(
    name: str,
    values: object,                        # scalar list or Vector
    step_id: str,
    timestamps: Iterable[ht.datetime] = (),
    outcomes: Iterable[Outcome] = (),
    error_information: Iterable[ErrorInformation] = (),
    hardware_item_ids: Iterable[str] = (),
    test_adapter_ids: Iterable[str] = (),
    software_item_ids: Iterable[str] = (),
    notes: str = "",
) -> Sequence[str]

# Read measurement data
get_measurement(measurement_id: str) -> PublishedMeasurement
query_measurements(odata_query: str = "") -> Sequence[PublishedMeasurement]
read_measurement_value(
    read_source: PublishedMeasurement,
    expected_type: type[T] | None = None,  # optional; raises TypeError on mismatch
) -> T | object

# Publish conditions
publish_condition(
    name: str,
    condition_type: str,
    value: object,
    step_id: str,
) -> str

publish_condition_batch(
    name: str,
    condition_type: str,
    values: object,
    step_id: str,
) -> str

# Read conditions
get_condition(condition_id: str) -> PublishedCondition
query_conditions(odata_query: str = "") -> Sequence[PublishedCondition]
read_condition_value(
    read_source: PublishedCondition,
    expected_type: type[T] | None = None,  # optional; raises TypeError on mismatch
) -> T | object
```

---

## Entity Field Reference

### TestResult fields
| Field | Type | Notes |
|---|---|---|
| `id` | str | GUID, auto-generated |
| `name` | str | Human-readable label |
| `uut_instance_id` | str | GUID or alias |
| `operator_id` | str | GUID or alias |
| `test_station_id` | str | GUID or alias |
| `test_description_id` | str | GUID or alias |
| `software_item_ids` | list[str] | GUIDs or aliases |
| `hardware_item_ids` | list[str] | GUIDs or aliases |
| `test_adapter_ids` | list[str] | GUIDs or aliases |
| `outcome` | Outcome | PASSED / FAILED / INDETERMINATE / UNSPECIFIED |
| `start_date_time` | timestamp | |
| `end_date_time` | timestamp | |
| `extension` | dict | Custom key-value pairs |
| `schema_id` | str | For extension validation |
| `error_information` | ErrorInformation | `error_code`, `message`, `source` |

### Step fields
| Field | Type | Notes |
|---|---|---|
| `id` | str | GUID |
| `name` | str | |
| `test_result_id` | str | Required |
| `parent_step_id` | str | For hierarchical steps |
| `test_id` | str | Links to Test entity |
| `step_type` | str | Category label |
| `outcome` | Outcome | |
| `notes` | str | |
| `extension` | dict | |
| `schema_id` | str | |

### Outcome enum values
`Outcome.UNSPECIFIED` · `Outcome.PASSED` · `Outcome.FAILED` · `Outcome.INDETERMINATE`

---

## OData Query Syntax

All `query_*` methods accept an OData query string. Unsupported options: `$expand`, `$count`, `$select`.

```python
# Filter examples
"$filter=name eq 'My Measurement'"
"$filter=outcome eq 'Failed'"
"$filter=testResultId eq <guid>"
"$filter=contains(name, 'Voltage')"
"$filter=startDateTime gt 2024-01-01T00:00:00Z"

# Ordering
"$filter=outcome eq 'Failed'&$orderby=startDateTime desc"

# Metadata queries
"$filter=serialNumber eq 'PS-2024-001'"
"$filter=name eq 'Sarah Johnson'"
```

Reference: https://learn.microsoft.com/en-us/odata/concepts/queryoptions-overview

---

## Extension Schemas

Register JSON Schema documents to validate `extension` dictionaries on any entity.

```python
schema_json = """
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "hardware_item": {
      "type": "object",
      "properties": {
        "bandwidth": {"type": "string"},
        "asset_tag":  {"type": "string"}
      },
      "required": ["bandwidth"]
    }
  }
}
"""

with MetadataStoreClient() as metadata_store_client:
    schema_id = metadata_store_client.register_schema(schema_json)
    # or from file:
    schema_id = metadata_store_client.register_schema_from_file("scope_schema.toml")

    hw = HardwareItem(
        manufacturer="NI", model="PXIe-5171", serial_number="S001",
        schema_id=schema_id,
        extension={"bandwidth": "1 GHz", "asset_tag": "SCOPE-789"},
    )
    hw_id = metadata_store_client.create_hardware_item(hw)
```

If a `TestResult` has a `schema_id`, child entities inherit it automatically.

---

## Aliases

Aliases map a stable human-readable name to any metadata entity. Use an alias name
anywhere a GUID is expected (e.g., `operator_id`, `hardware_item_ids`).

```python
with MetadataStoreClient() as metadata_store_client:
    # Create
    alias = metadata_store_client.create_alias("Primary_DMM", dmm_hardware_item_object)

    # Retrieve
    alias = metadata_store_client.get_alias("Primary_DMM")
    # alias.name        → "Primary_DMM"
    # alias.target_type → AliasTargetType.HARDWARE_ITEM
    # alias.target_id   → "<guid>"

    # List all
    aliases = metadata_store_client.query_aliases()

    # Delete
    metadata_store_client.delete_alias("Primary_DMM")
```

Supported alias target types: `UUT_INSTANCE`, `UUT`, `HARDWARE_ITEM`, `SOFTWARE_ITEM`,
`OPERATOR`, `TEST_DESCRIPTION`, `TEST`, `TEST_STATION`, `TEST_ADAPTER`.

---

## Minimal End-to-End Example

```python
"""Minimal example: publish a waveform and read it back."""
from datetime import timezone

import hightime as ht
import numpy as np
from ni.datastore.data import DataStoreClient, Step, TestResult
from ni.datastore.metadata import MetadataStoreClient, Operator, TestStation, Uut, UutInstance
from nitypes.waveform import AnalogWaveform, Timing


def main() -> None:
    with MetadataStoreClient() as metadata_store_client, DataStoreClient() as data_store_client:
        # --- Metadata ---
        operator_id = metadata_store_client.create_operator(Operator(name="Alice", role="Test Engineer"))
        station_id  = metadata_store_client.create_test_station(TestStation(name="Bench-1"))
        uut_id      = metadata_store_client.create_uut(Uut(model_name="Widget v1", family="Electronics"))
        uut_inst_id = metadata_store_client.create_uut_instance(UutInstance(uut_id=uut_id, serial_number="W-0001"))

        # --- Test result + step ---
        test_result_id = data_store_client.create_test_result(TestResult(
            name="Widget Validation",
            uut_instance_id=uut_inst_id,
            operator_id=operator_id,
            test_station_id=station_id,
        ))
        step_id = data_store_client.create_step(Step(name="Voltage Check", test_result_id=test_result_id))

        # --- Publish waveform ---
        waveform = AnalogWaveform(
            sample_count=3,
            raw_data=np.array([1.0, 2.0, 3.0]),
            timing=Timing.create_with_regular_interval(
                ht.timedelta(seconds=1e-3), ht.datetime.now(timezone.utc)
            ),
        )
        measurement_id = data_store_client.publish_measurement(name="Output Waveform", value=waveform, step_id=step_id)

        # --- Read back ---
        measurement = data_store_client.get_measurement(measurement_id)
        readback    = data_store_client.read_measurement_value(measurement, expected_type=AnalogWaveform)
        print(readback.raw_data)   # [1. 2. 3.]


if __name__ == "__main__":
    main()
```

---

## Best Practices

- Always use `with` statements for both clients to ensure gRPC channel cleanup.
- Create metadata entities (operators, stations, UUTs, hardware, software) **once** in a
  setup phase and store the returned IDs for reuse across many test results.
- Create **aliases** for frequently referenced entities so test code is not coupled to GUIDs.
- Always create a `TestResult` before creating `Step` objects or publishing data.
- Group related measurements into logical `Step` objects.
- Publish `PublishedCondition` data (temperature, supply voltage, etc.) alongside measurements
  so analysis can account for environmental variation.
- Use `publish_measurement_batch` / `publish_condition_batch` for parametric sweeps.
- Set `outcome` (PASSED / FAILED / INDETERMINATE) on every measurement so queries like
  `"$filter=outcome eq 'Failed'"` work correctly.
- Use specific OData `$filter` clauses to reduce query result sizes.
- Register extension schemas to enforce required custom fields across your organization.
- Reference: https://datastorepython.readthedocs.io/en/latest
