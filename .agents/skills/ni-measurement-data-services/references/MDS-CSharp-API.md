# NI Measurement Data Services (MDS) — C# API Skills

## Overview

The **NI Measurement Data Services (MDS)** .NET API allows users to **publish, query, and manage measurement data and metadata** using gRPC-based client libraries. The MDS client libraries target **.NET Standard 2.0**, so they can be used with any compatible .NET implementation (e.g., .NET Framework 4.6.1+, .NET 6+, .NET 8+).

### Prerequisites

- **NI Measurement Data Services Software 2026 Q3 or later** installed on the system.
- Any .NET runtime or SDK compatible with .NET Standard 2.0.
- NuGet packages are sourced from the NI Artifactory feed.

---

## NuGet Packages

The core NuGet packages required for MDS applications are:

| Package | Purpose |
|---|---|
| `NI.Measurements.Data.V1.Api` | Data operations: create test results, steps, publish measurements/conditions, query data |
| `NI.Measurements.Metadata.V1.Api` | Metadata operations: create/query operators, test stations, hardware items, software items, UUTs, UUT instances, aliases, register schemas |
| `NI.Discovery.V1.Client` | Service discovery: provides `GrpcClientStubFactory` to create gRPC client stubs |

### .csproj Setup

A typical MDS `.csproj` file looks like:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework> <!-- or any framework compatible with .NET Standard 2.0 -->
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="NI.Discovery.V1.Client" />
    <PackageReference Include="NI.Measurements.Data.V1.Api" />
    <PackageReference Include="NI.Measurements.Metadata.V1.Api" />
  </ItemGroup>
</Project>
```

If the application uses schema files (`.json` or `.toml`), add a copy rule:

```xml
<ItemGroup>
  <None Update="*.json">
    <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
  </None>
</ItemGroup>
```

---

## Key Namespaces and Using Directives

Every MDS C# file should include the following `using` directives as needed:

```csharp
using NationalInstruments;                                        // Core types (e.g., PrecisionDateTime)
using NationalInstruments.MeasurementLink.Discovery.V1;           // GrpcClientStubFactory
using NationalInstruments.Measurements.Data.V1;                   // Data types: TestResult, Step, Scalar, DoubleAnalogWaveform, Outcome, etc.
using NationalInstruments.Measurements.Metadata.V1;               // Metadata types: Operator, TestStation, HardwareItem, SoftwareItem, Uut, UutInstance, Alias, ExtensionValue
using NationalInstruments.Protobuf.Types;                         // PrecisionTimestamp / PrecisionDateTime conversion
using static NationalInstruments.Measurements.Data.V1.DataStoreService;         // DataStoreServiceClient
using static NationalInstruments.Measurements.Metadata.V1.MetadataStoreService; // MetadataStoreServiceClient
```

**IMPORTANT**: The `using static` directives are required to access the nested gRPC client classes (`DataStoreServiceClient`, `MetadataStoreServiceClient`). Without them, you must use the fully qualified name `DataStoreService.DataStoreServiceClient`.

**IMPORTANT**: `PrecisionDateTime.UtcNow` is only available in the high-level wrapper packages (`NI.Measurements.Data.V1.DataStoreClient`). When using the raw gRPC API packages (`NI.Measurements.Data.V1.Api`), use `PrecisionTimestamp` directly:
```csharp
var ts = new PrecisionTimestamp { Seconds = DateTimeOffset.UtcNow.ToUnixTimeSeconds() };
```

---

## Client Initialization (Required Boilerplate)

Every MDS application must create gRPC client stubs using `GrpcClientStubFactory`:

```csharp
// Create the gRPC client stub factory and service clients.
using var clientStubFactory = new GrpcClientStubFactory();
var dataStoreServiceClient = clientStubFactory.CreateClient<DataStoreServiceClient>();
var metadataStoreServiceClient = clientStubFactory.CreateClient<MetadataStoreServiceClient>();
```

**IMPORTANT**: When using the raw gRPC stubs, all async methods take a `Request` object as the first argument and optionally `Grpc.Core.Metadata` as the second. Do **NOT** pass `CancellationToken.None` as the second argument — it will not compile. Either omit the second argument or pass `null` for default metadata.

```csharp
// WRONG — CancellationToken is not accepted by gRPC stubs
await data.PublishMeasurementAsync(request, CancellationToken.None);

// CORRECT — omit the second argument
await data.PublishMeasurementAsync(request);
```

---

## Data Model

The MDS data model is hierarchical:

```
TestResult
├── Step (one or more steps per test result)
│   ├── PublishedMeasurement (measurement data with name, value, timestamp, outcome)
│   └── PublishedCondition (environmental/test conditions)
├── OperatorId → Operator
├── TestStationId → TestStation
├── UutInstanceId → UutInstance → Uut
├── HardwareItemIds → [HardwareItem, ...]
└── SoftwareItemIds → [SoftwareItem, ...]
```

### Core Data Types

| Type | Service | Description |
|---|---|---|
| `TestResult` | DataStoreServiceClient | Top-level test result with references to metadata |
| `Step` | DataStoreServiceClient | A step within a test result |
| `PublishedMeasurement` | DataStoreServiceClient | A measurement with name, value, timestamp, and outcome |
| `PublishedCondition` | DataStoreServiceClient | A test condition (e.g., ambient temperature) |
| `Scalar` | DataStoreServiceClient | A scalar measurement value with `DoubleValue` and `Units` |
| `DoubleAnalogWaveform` | DataStoreServiceClient | Waveform data with `Dt`, `T0`, and `YData` |
| `Outcome` | DataStoreServiceClient | Enum: `Passed`, `Failed`, etc. |

### Core Metadata Types

| Type | Service | Description |
|---|---|---|
| `Operator` | MetadataStoreServiceClient | Test operator with `Name` and `Role` |
| `TestStation` | MetadataStoreServiceClient | Test station with `Name` |
| `HardwareItem` | MetadataStoreServiceClient | Hardware with `Manufacturer`, `Model`, `SerialNumber` |
| `SoftwareItem` | MetadataStoreServiceClient | Software with `Product`, `Version` |
| `Uut` | MetadataStoreServiceClient | Unit Under Test with `ModelName`, `Family` |
| `UutInstance` | MetadataStoreServiceClient | A specific UUT instance with `UutId`, `SerialNumber` |
| `Alias` | MetadataStoreServiceClient | Named alias to reference metadata entities by friendly name |
| `ExtensionValue` | MetadataStoreServiceClient | Key-value extension attribute (e.g., `StringValue`) |

---

## Common Operations

### 1. Creating Metadata

```csharp
// Create an operator
var @operator = new Operator { Name = "Jane Doe", Role = "Test Engineer" };
var operatorId = await metadataStoreServiceClient.CreateOperatorAsync(@operator);

// Create a test station
var testStation = new TestStation { Name = "TestStation_A1" };
var testStationId = await metadataStoreServiceClient.CreateTestStationAsync(testStation);

// Create a hardware item
var hardwareItem = new HardwareItem
{
    Manufacturer = "NI",
    Model = "PXIe-4081",
    SerialNumber = "DMM001"
};
var hardwareItemId = await metadataStoreServiceClient.CreateHardwareItemAsync(hardwareItem);

// Create a software item
var softwareItem = new SoftwareItem { Product = "Python", Version = "3.11.5" };
var softwareItemId = await metadataStoreServiceClient.CreateSoftwareItemAsync(softwareItem);

// Create a UUT (unit under test)
var uut = new Uut { ModelName = "PowerSupply v2.1", Family = "Power" };
await metadataStoreServiceClient.CreateUutAsync(uut);

// Create a UUT instance (a specific serial-numbered unit)
var uutInstance = new UutInstance { UutId = uutId, SerialNumber = "PS-2024-001" };
await metadataStoreServiceClient.CreateUutInstanceAsync(uutInstance);
```

### 2. Creating Aliases

Aliases provide friendly names that can be used in place of server-generated IDs:

```csharp
// Create an alias for an operator
await metadataStoreServiceClient.CreateAliasAsync("primary_operator", @operator);

// Use the alias as an ID when creating a test result
var testResult = new TestResult
{
    Name = "My Test",
    OperatorId = "primary_operator",  // Uses the alias instead of a server-generated ID
};

// Query, get, and delete aliases
var alias = await metadataStoreServiceClient.GetAliasAsync("primary_operator");
var aliases = await metadataStoreServiceClient.QueryAliasesAsync("$filter=name eq 'primary_operator'");
var deleted = await metadataStoreServiceClient.DeleteAliasAsync("primary_operator");
```

### 3. Creating Test Results with Metadata References

```csharp
var testResult = new TestResult
{
    Name = "Power Supply Test v2.1",
    OperatorId = operatorId,          // or an alias string
    TestStationId = testStationId,    // or an alias string
    UutInstanceId = uutInstanceId,    // or an alias string
};
testResult.SoftwareItemIds.Add(softwareItemId);   // or alias strings
testResult.HardwareItemIds.Add(hardwareItemId);   // or alias strings
var testResultId = await dataStoreServiceClient.CreateTestResultAsync(testResult);
```

### 4. Creating Steps

```csharp
var step = new Step
{
    Name = "Output Voltage Test",
    TestResultId = testResultId,
};
var stepId = await dataStoreServiceClient.CreateStepAsync(step);
```

### 5. Publishing Scalar Measurements

```csharp
await dataStoreServiceClient.PublishMeasurementAsync(
    "Measure 5V Rail",                                    // measurement name
    new Scalar { DoubleValue = 5.02, Units = "V" },      // scalar value
    PrecisionDateTime.UtcNow,                             // timestamp
    stepId,                                               // parent step ID
    outcome: Outcome.Passed                               // pass/fail outcome (optional)
);
```

### 6. Publishing Waveform Measurements

```csharp
var waveform = new DoubleAnalogWaveform
{
    Dt = 0.001,                                           // time between samples (seconds)
    T0 = PrecisionDateTime.UtcNow.ToPrecisionTimestamp(), // start time
    ChannelName = "CH1",                                  // channel identifier
    UnitDescription = "Volts",                            // Y-axis units
};
waveform.YData.AddRange(new double[] { 1.0, 2.0, 3.0 }); // sample data

await dataStoreServiceClient.PublishMeasurementAsync(
    "scope reading",
    waveform,
    PrecisionDateTime.UtcNow,
    stepId
);
```

#### DoubleAnalogWaveform Properties

| Property | Type | Description |
|----------|------|-------------|
| `ChannelName` | `string` | Channel identifier (e.g., "CH1") |
| `UnitDescription` | `string` | Units for the Y data (e.g., "Volts", "Amps") |
| `T0` | `PrecisionTimestamp` | Start timestamp |
| `Dt` | `double` | Delta time between samples in seconds |
| `YData` | `RepeatedField<double>` | Sample values (use `.AddRange()`) |
| `Attributes` | `MapField` | Optional key-value metadata |

#### All Supported Measurement Value Types

`PublishMeasurementAsync` supports multiple value types (use only one per call):

| Type | Description |
|------|-------------|
| `Scalar` | Single value (double, int, string, bool) |
| `Vector` | Array of values |
| `DoubleAnalogWaveform` | Analog waveform (Y data + timing) |
| `I16AnalogWaveform` | 16-bit integer analog waveform |
| `DoubleComplexWaveform` | Complex waveform (real + imaginary) |
| `I16ComplexWaveform` | 16-bit complex waveform |
| `DoubleSpectrum` | Frequency spectrum data |
| `DigitalWaveform` | Digital waveform |
| `DoubleXYData` | XY coordinate data |

### 7. Publishing Conditions

Conditions capture environmental or test setup parameters:

```csharp
await dataStoreServiceClient.PublishConditionAsync(
    "Ambient Temperature",                                // condition name
    "Environment",                                        // category
    new Scalar { DoubleValue = 23.5, Units = "deg C" },   // value
    stepId                                                // parent step ID
);
```

### 8. Retrieving Data

```csharp
// Get a test result by ID
var testResult = await dataStoreServiceClient.GetTestResultAsync(testResultId);

// Get a measurement by ID
var measurement = await dataStoreServiceClient.GetMeasurementAsync(measurementId);

// Read the typed value of a measurement
var waveform = await dataStoreServiceClient.ReadMeasurementValueAsync<DoubleAnalogWaveform>(measurementId);

// Get metadata by ID
var @operator = await metadataStoreServiceClient.GetOperatorAsync(operatorId);
```

---

## Querying with OData Filters

All query methods accept an OData filter string. Pass an empty string `""` to return all items.

### Query Methods Available

**DataStoreServiceClient:**
- `QueryMeasurementsAsync(odataQuery)`
- `QueryStepsAsync(odataQuery)`
- `QueryConditionsAsync(odataQuery)`

**MetadataStoreServiceClient:**
- `QueryOperatorsAsync(odataQuery)`
- `QueryTestStationsAsync(odataQuery)`
- `QueryHardwareItemsAsync(odataQuery)`
- `QuerySoftwareItemsAsync(odataQuery)`
- `QueryUutsAsync(odataQuery)`
- `QueryUutInstancesAsync(odataQuery)`
- `QueryAliasesAsync(odataQuery)`

### OData Filter Examples

```csharp
// Exact match
"$filter=Name eq 'TestStation_B2'"

// Contains (substring search)
"$filter=contains(Name,'Voltage')"

// Starts with
"$filter=startswith(Name,'Test')"

// Ends with
"$filter=endswith(ModelName,'v1.3')"

// AND combination
"$filter=contains(SerialNumber,'AMP') and contains(SerialNumber,'2024')"

// OR combination
"$filter=contains(Name,'Temperature') or contains(Name,'Pressure')"

// Filter by manufacturer
"$filter=Manufacturer eq 'NI'"

// Filter by product
"$filter=Product eq 'Python'"

// Filter by role
"$filter=contains(Role,'Test Engineer')"

// Filter by version prefix
"$filter=startswith(Version,'3.')"

// Filter aliases by target type
"$filter=TargetType eq DataStore.AliasTargetType'TestStation'"

// Filter measurements by extension attribute on related hardware
"$filter=testresult/hardwareitems/any (h: h/extension/cable_length eq '1.5') and Name eq 'scope reading'"

// Get all items (empty query)
""
```

---

## Extension Attributes and Schemas

Extension attributes allow adding custom key-value properties to metadata objects. Schemas validate these attributes.

### Schema Formats

**JSON Schema** (for multi-type schemas):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/sample.schema.json",
  "title": "default test schema",
  "type": "object",
  "properties": {
    "operator": {
      "type": "object",
      "properties": {
        "badge_number": { "type": "string" }
      },
      "required": ["badge_number"]
    },
    "test_station": {
      "type": "object",
      "properties": {
        "location": { "type": "string", "enum": ["USA", "Canada", "Mexico"] }
      }
    }
  }
}
```

**TOML Schema** (for single-type schemas):
```toml
id = "https://example.com/cable.schema.toml"

[hardware_item]
cable_length = "*"
manufacture_date = "*"
```

### Registering Schemas and Using Extension Attributes

```csharp
// Register a schema from a file
var schemaId = await metadataStoreServiceClient.RegisterSchemaFromFileAsync(
    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "my_schema.json"));

// Create a metadata object with a schema and extension attributes
var @operator = new Operator
{
    Name = "John Doe",
    SchemaId = schemaId,
};
@operator.Extension["badge_number"] = new ExtensionValue { StringValue = "emp-128256" };
var operatorId = await metadataStoreServiceClient.CreateOperatorAsync(@operator);

// Hardware item with extension attributes
var cable = new HardwareItem
{
    Manufacturer = "NI",
    Model = "cable",
    SerialNumber = "7u2349",
    SchemaId = cableSchemaId,
};
cable.Extension["cable_length"] = new ExtensionValue { StringValue = "1.5" };
cable.Extension["manufacture_date"] = new ExtensionValue { StringValue = "2023-01-01" };
```

---

## AliasTargetType Enum Values

When querying or inspecting aliases, the `AliasTargetType` enum can take these values:

| Value | Description |
|---|---|
| `Unspecified` | Unspecified target type |
| `Operator` | Operator |
| `TestStation` | Test Station |
| `HardwareItem` | Hardware Item |
| `SoftwareItem` | Software Item |
| `Uut` | Unit Under Test |
| `UutInstance` | UUT Instance |
| `TestDescription` | Test Description |
| `Test` | Test |
| `TestAdapter` | Test Adapter |

---

## Complete Minimal Example

Here is a complete, minimal MDS example that creates metadata, publishes a measurement, and reads it back:

```csharp
using NationalInstruments;
using NationalInstruments.MeasurementLink.Discovery.V1;
using NationalInstruments.Measurements.Data.V1;
using NationalInstruments.Measurements.Metadata.V1;
using NationalInstruments.Protobuf.Types;
using static NationalInstruments.Measurements.Data.V1.DataStoreService;
using static NationalInstruments.Measurements.Metadata.V1.MetadataStoreService;

// Create gRPC clients
using var clientStubFactory = new GrpcClientStubFactory();
var dataStoreServiceClient = clientStubFactory.CreateClient<DataStoreServiceClient>();
var metadataStoreServiceClient = clientStubFactory.CreateClient<MetadataStoreServiceClient>();

// Create metadata
var @operator = new Operator { Name = "Jane Doe", Role = "Test Engineer" };
var operatorId = await metadataStoreServiceClient.CreateOperatorAsync(@operator);

var testStation = new TestStation { Name = "TestStation_01" };
var testStationId = await metadataStoreServiceClient.CreateTestStationAsync(testStation);

// Create a test result
var testResult = new TestResult
{
    Name = "My First Test",
    OperatorId = operatorId,
    TestStationId = testStationId,
};
var testResultId = await dataStoreServiceClient.CreateTestResultAsync(testResult);

// Create a step and publish a measurement
var step = new Step { Name = "Voltage Check", TestResultId = testResultId };
var stepId = await dataStoreServiceClient.CreateStepAsync(step);

await dataStoreServiceClient.PublishMeasurementAsync(
    "Output Voltage",
    new Scalar { DoubleValue = 5.02, Units = "V" },
    PrecisionDateTime.UtcNow,
    stepId,
    outcome: Outcome.Passed);

// Query the measurement back
var measurements = await dataStoreServiceClient.QueryMeasurementsAsync(
    "$filter=contains(Name,'Voltage')");
foreach (var m in measurements)
{
    Console.WriteLine($"Measurement: {m.Name} - {m.Outcome}");
}
```

---

## Building and Running

```bash
# Build the project
dotnet build

# Run the application
dotnet run
```

---

## Common Patterns and Best Practices

1. **Always use `using` statements** for `GrpcClientStubFactory` and any `IDisposable` objects.
2. **Use aliases** instead of server-generated IDs for more readable and maintainable code.
3. **All async methods use the `Async` suffix** — always `await` them.
4. **Use `PrecisionDateTime.UtcNow`** for timestamps, and `.ToPrecisionTimestamp()` when a `PrecisionTimestamp` is needed (e.g., for waveform `T0`).
5. **OData filter strings** start with `$filter=`. Pass an empty string `""` to return all items.
6. **Extension attributes** are set via the `.Extension` dictionary on metadata objects, using `ExtensionValue` with `StringValue`.
7. **Schema files** can be `.json` (JSON Schema) or `.toml` format. Register them with `RegisterSchemaFromFileAsync()` and assign the returned `schemaId` to the metadata object's `SchemaId` property.
8. **Test results reference metadata by ID** — set `OperatorId`, `TestStationId`, `UutInstanceId`, and add to `SoftwareItemIds` / `HardwareItemIds` collections.
9. **Waveform data** uses `DoubleAnalogWaveform` with `Dt` (sample interval), `T0` (start time), and `YData` (sample values added via `.AddRange()`).

---

## Common Mistakes

1. **Wrong namespace for Scalar/PrecisionTimestamp**: Use `NationalInstruments.Protobuf.Types`, not `NationalInstruments.Measurements.Data.V1`.

2. **Missing `TestResultId` on Step**: A `Step` requires `TestResultId` to link to its parent `TestResult`.

3. **Missing `StepId` on Measurement/Condition**: Measurements and conditions require a `StepId` to link to their parent step.

4. **Wrong timestamp type**: `PrecisionTimestamp.Seconds` is `long`, not `ulong`. Use `PrecisionDateTime.UtcNow` and `.ToPrecisionTimestamp()` for conversions.

5. **Confusing `Scalar.Units` with `UnitDescription`**: `Scalar` has a `Units` string property for scalar values. `DoubleAnalogWaveform` uses `UnitDescription` for Y-axis units. Don't mix them up.

6. **Forgetting to create entities top-down**: You must create `TestResult` → `Step` → Measurement/Condition in order. Each child requires its parent's ID.

7. **Not disposing `GrpcClientStubFactory`**: Always use a `using` statement to ensure proper cleanup of gRPC channels.
