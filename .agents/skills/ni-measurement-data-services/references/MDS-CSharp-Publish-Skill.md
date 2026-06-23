---
name: ni-mds-csharp-publish
description: >
  Generate correct C# code for publishing measurement data to NI Measurement Data Services (MDS)
  using the NI.Measurements.Data.V1 NuGet packages. Covers DataStoreClient and MetadataStoreClient
  APIs for creating test results, steps, publishing measurements, and querying data.
---

# NI MDS C# Publishing Skill

## Package Requirements

```xml
<PackageReference Include="NI.Measurements.Data.V1.Api" Version="9.19.14" />
<PackageReference Include="NI.Measurements.Data.V1.DataStoreClient" Version="9.19.14" />
<PackageReference Include="NI.Measurements.Metadata.V1.MetadataStoreClient" Version="9.19.14" />
<PackageReference Include="NI.Discovery.V1.Client" Version="9.21.0.1290" />
```

**NuGet Source**: Requires NI Artifactory feed:
```
https://pull.artifacts.ni.com/artifactory/api/nuget/v3/rnd-nuget-pre
```

## Required Namespaces

```csharp
using NationalInstruments.Measurements.Data.V1;      // DataStoreClient, TestResult, Step, etc.
using NationalInstruments.Measurements.Metadata.V1;  // MetadataStoreClient (for UUT, Operator queries)
using NationalInstruments.Protobuf.Types;            // PrecisionTimestamp, Scalar
```

## Data Model Hierarchy

MDS requires a strict hierarchy when publishing data:

```
TestResult (top-level container)
└── Step (logical grouping)
    ├── Measurement (data value)
    └── Condition (test parameter)
```

**Key Rule**: You must create entities top-down:
1. Create `TestResult` first → get `testResultId`
2. Create `Step` referencing that `testResultId` → get `stepId`
3. Publish measurements referencing that `stepId`

## Two Clients

| Client | Purpose | Namespace |
|--------|---------|-----------|
| `DataStoreClient` | Publish/query test results, steps, measurements, conditions | `NationalInstruments.Measurements.Data.V1` |
| `MetadataStoreClient` | Query/create UUTs, operators, test stations, hardware/software items | `NationalInstruments.Measurements.Metadata.V1` |

**IMPORTANT - Two Client Patterns Exist:**

The MDS C# API has **two different client patterns** depending on the NuGet packages available:

1. **High-level wrappers** (`DataStoreClient`, `MetadataStoreClient`) — available in `NI.Measurements.Data.V1.DataStoreClient` and `NI.Measurements.Metadata.V1.MetadataStoreClient` packages. These accept `CancellationToken` and have convenience overloads like `PublishMeasurementAsync(name, scalar, timestamp, stepId)`.

2. **Raw gRPC stubs** (`DataStoreService.DataStoreServiceClient`) — available in the `NI.Measurements.Data.V1.Api` package. These use `Request`/`Response` types and accept `Grpc.Core.Metadata` (not `CancellationToken`). Created via `GrpcClientStubFactory.CreateClient<DataStoreServiceClient>()`.

**Use this rule:** Check which packages are available. If the high-level wrappers are not resolvable, use the gRPC stub pattern:

```csharp
// gRPC stub pattern (works with NI.Measurements.Data.V1.Api only)
using NationalInstruments.MeasurementLink.Discovery.V1;
using NationalInstruments.Measurements.Data.V1;
using NationalInstruments.Protobuf.Types;
using static NationalInstruments.Measurements.Data.V1.DataStoreService;

using var factory = new GrpcClientStubFactory();
var data = factory.CreateClient<DataStoreServiceClient>();

// Create TestResult — must wrap in request object
var trResp = await data.CreateTestResultAsync(new CreateTestResultRequest { TestResult = testResult });
var trId = trResp.TestResultId;

// Create Step — must wrap in request object
var stResp = await data.CreateStepAsync(new CreateStepRequest { Step = step });
var stId = stResp.StepId;

// Publish — use request objects, do NOT pass CancellationToken
await data.PublishMeasurementAsync(new PublishMeasurementRequest {
    Name = "Voltage", StepId = stId, Outcome = Outcome.Passed,
    Scalar = new Scalar { DoubleValue = 5.02, Units = "V" }
});
```

## NuGet Resolution Gotchas

### NI Artifactory Feed Requires Authentication

The NI Artifactory feed (`https://pull.artifacts.ni.com/...`) returns HTTP 401 without proper credentials. If packages are already cached locally in `~/.nuget/packages`, add the local cache as a NuGet source to avoid needing the authenticated feed:

```xml
<!-- NuGet.Config -->
<packageSources>
  <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
  <add key="local-cache" value="C:\Users\<user>\.nuget\packages" />
</packageSources>
```

### Version Alignment

Transitive NI dependencies must all resolve to compatible versions. If `NI.Discovery.V1.Client` version `9.21.x` requires `NI.Discovery.V1.Api >= 9.21.x` but only `9.20.x` is cached, downgrade the top-level package to match what's available locally.

### `PrecisionDateTime` vs `PrecisionTimestamp`

`PrecisionDateTime.UtcNow` exists **only** in the high-level wrapper packages. The raw gRPC API uses `PrecisionTimestamp`:

```csharp
// In raw gRPC pattern, create timestamps manually:
var ts = new PrecisionTimestamp { Seconds = DateTimeOffset.UtcNow.ToUnixTimeSeconds() };
```

Do NOT use `PrecisionDateTime.UtcNow` with the gRPC stub pattern — it will not compile.

## Complete Publishing Example

```csharp
using NationalInstruments.Measurements.Data.V1;
using NationalInstruments.Protobuf.Types;

using var client = new DataStoreClient();

// Timestamp for all entities
var now = DateTimeOffset.UtcNow;
var timestamp = new PrecisionTimestamp { Seconds = now.ToUnixTimeSeconds() };

// 1. Create TestResult
var testResult = new TestResult
{
    Name = "My_Test",
    Outcome = Outcome.Passed,
    StartDateTime = timestamp,
    EndDateTime = timestamp
};
var testResultRequest = new CreateTestResultRequest { TestResult = testResult };
var testResultId = await client.CreateTestResultAsync(testResultRequest, CancellationToken.None);

// 2. Create Step
var step = new Step
{
    Name = "Measurement_Step",
    TestResultId = testResultId,    // REQUIRED - links to parent
    StepType = "Measurement",
    Outcome = Outcome.Passed,
    StartDateTime = timestamp,
    EndDateTime = timestamp
};
var stepRequest = new CreateStepRequest { Step = step };
var stepResponse = await client.CreateStepAsync(stepRequest, CancellationToken.None);
var stepId = stepResponse.StepId;   // Note: .StepId not .Step.Id

// 3. Publish Measurement
var measurementRequest = new PublishMeasurementRequest
{
    Name = "Voltage_Output",
    StepId = stepId,                // REQUIRED - links to parent step
    Outcome = Outcome.Passed,
    Notes = "Optional notes",
    Scalar = new Scalar { DoubleValue = 3.14159 }
};
var measurementId = await client.PublishMeasurementAsync(measurementRequest, CancellationToken.None);
```

## Key Types

### Outcome Enum
```csharp
Outcome.Unspecified   // Default
Outcome.Passed
Outcome.Failed
Outcome.Indeterminate
```

### PrecisionTimestamp
```csharp
// In NationalInstruments.Protobuf.Types
var timestamp = new PrecisionTimestamp 
{ 
    Seconds = DateTimeOffset.UtcNow.ToUnixTimeSeconds()  // long, not ulong
};
```

### Scalar (for measurement values)
```csharp
// In NationalInstruments.Protobuf.Types
new Scalar { DoubleValue = 3.14159 }
new Scalar { Int64Value = 42 }
new Scalar { StringValue = "text" }
new Scalar { BoolValue = true }
```

### DoubleAnalogWaveform (for waveform data)
```csharp
// In NationalInstruments.Protobuf.Types
var waveform = new DoubleAnalogWaveform
{
    ChannelName = "CH1",           // Channel identifier
    UnitDescription = "Volts",     // Y-axis units
    T0 = timestamp,                // Start time (PrecisionTimestamp)
    Dt = 1.0 / sampleRate          // Time between samples in seconds
};
waveform.YData.AddRange(yData);    // Add sample data (double[])
```

**DoubleAnalogWaveform properties**:
- `ChannelName` - String identifier for the channel
- `UnitDescription` - Units for the Y data (e.g., "Volts", "Amps")
- `T0` - Start timestamp (`PrecisionTimestamp`)
- `Dt` - Delta time between samples in seconds (`double`)
- `YData` - Sample values (`RepeatedField<double>`, use `.AddRange()`)
- `Attributes` - Optional key-value metadata

### Publishing Waveform Example

```csharp
// Generate a 1kHz sine wave - 100 samples at 100kHz sample rate
const int sampleCount = 100;
const double sampleRate = 100000;  // 100 kHz
const double frequency = 1000;     // 1 kHz sine wave
const double amplitude = 5.0;      // 5V amplitude

var yData = new double[sampleCount];
for (int i = 0; i < sampleCount; i++)
{
    double t = i / sampleRate;
    yData[i] = amplitude * Math.Sin(2 * Math.PI * frequency * t);
}

// Create DoubleAnalogWaveform
var waveform = new DoubleAnalogWaveform
{
    ChannelName = "CH1",
    UnitDescription = "Volts",
    T0 = timestamp,
    Dt = 1.0 / sampleRate
};
waveform.YData.AddRange(yData);

// Publish waveform (use DoubleAnalogWaveform instead of Scalar)
var measurementRequest = new PublishMeasurementRequest
{
    Name = "SineWave_1kHz",
    StepId = stepId,
    Outcome = Outcome.Passed,
    Notes = "1 kHz sine wave, 5V amplitude",
    DoubleAnalogWaveform = waveform  // Use this instead of Scalar
};
await client.PublishMeasurementAsync(measurementRequest, CancellationToken.None);
```

### Other Waveform Types

`PublishMeasurementRequest` supports multiple value types (use only one per request):

| Property | Type | Description |
|----------|------|-------------|
| `Scalar` | `Scalar` | Single value (double, int, string, bool) |
| `Vector` | `Vector` | Array of values |
| `DoubleAnalogWaveform` | `DoubleAnalogWaveform` | Analog waveform (Y data + timing) |
| `I16AnalogWaveform` | `I16AnalogWaveform` | 16-bit integer analog waveform |
| `DoubleComplexWaveform` | `DoubleComplexWaveform` | Complex waveform (real + imaginary) |
| `I16ComplexWaveform` | `I16ComplexWaveform` | 16-bit complex waveform |
| `DoubleSpectrum` | `DoubleSpectrum` | Frequency spectrum data |
| `DigitalWaveform` | `DigitalWaveform` | Digital waveform |
| `XYData` | `DoubleXYData` | XY coordinate data |

## Publishing Conditions

Conditions capture test inputs, environmental parameters, or setup values — as distinct from measurements which capture test outputs/results.

**Use cases:**
- **Conditions** = Test inputs/parameters (e.g., "InputVoltage = 12V", "Temperature = 25°C", "LoadCurrent = 2A")
- **Measurements** = Test outputs/results (e.g., "OutputVoltage = 3.3V", "Efficiency = 92%")

### PublishConditionRequest Properties

| Property | Type | Description |
|----------|------|-------------|
| `Name` | `string` | Condition name (e.g., "InputVoltage") |
| `ConditionType` | `string` | Category: "Input", "Environment", "Setup", "Limit", etc. |
| `Scalar` | `Scalar` | The value (double, int, string, bool) |
| `StepId` | `string` | Links condition to parent step |

### Condition Publishing Example

```csharp
// Publish environmental condition
await client.PublishConditionAsync(new PublishConditionRequest
{
    Name = "AmbientTemperature",
    ConditionType = "Environment",
    StepId = stepId,
    Scalar = new Scalar { DoubleValue = 23.5, Units = "deg C" }
}, CancellationToken.None);

// Publish test input parameters
await client.PublishConditionAsync(new PublishConditionRequest
{
    Name = "InputVoltage",
    ConditionType = "Input",
    StepId = stepId,
    Scalar = new Scalar { DoubleValue = 12.0, Units = "V" }
}, CancellationToken.None);

await client.PublishConditionAsync(new PublishConditionRequest
{
    Name = "LoadCurrent",
    ConditionType = "Input",
    StepId = stepId,
    Scalar = new Scalar { DoubleValue = 2.0, Units = "A" }
}, CancellationToken.None);
```

### Querying Conditions

```csharp
// Query all conditions for a step
var conditions = await client.QueryConditionsAsync(
    $"$filter=StepId eq '{stepId}'", CancellationToken.None);

foreach (var c in conditions)
{
    Console.WriteLine($"{c.Name} ({c.ConditionType}): {c.Scalar.DoubleValue}");
}
```

## Querying Data

### Query Test Results
```csharp
using var client = new DataStoreClient();

// All results
var results = await client.QueryTestResultsAsync("", CancellationToken.None);

// With OData filter
var filtered = await client.QueryTestResultsAsync(
    "$filter=Outcome eq 'Failed'", 
    CancellationToken.None);

// Results is IReadOnlyList<TestResult>
foreach (var result in results)
{
    Console.WriteLine($"{result.Name} - {result.Outcome}");
}
```

### Query UUT Instances (for serial numbers)
```csharp
using var metaClient = new MetadataStoreClient();

var uutInstances = await metaClient.QueryUutInstancesAsync("", CancellationToken.None);

// Build lookup: UutInstanceId -> SerialNumber
var serialLookup = uutInstances.ToDictionary(u => u.Id, u => u.SerialNumber ?? "(blank)");

// TestResult.UutInstanceId links to UutInstance
var serialNumber = serialLookup[testResult.UutInstanceId];
```

## DataStoreClient Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `CreateTestResultAsync(request, ct)` | `string` (ID) | Create a test result |
| `CreateStepAsync(request, ct)` | `CreateStepResponse` | Create a step (use `.StepId`) |
| `PublishMeasurementAsync(request, ct)` | `PublishMeasurementResponse` | Publish a measurement |
| `PublishConditionAsync(request, ct)` | `PublishConditionResponse` | Publish a condition |
| `QueryTestResultsAsync(odata, ct)` | `IReadOnlyList<TestResult>` | Query test results |
| `QueryStepsAsync(odata, ct)` | `IReadOnlyList<Step>` | Query steps |
| `QueryMeasurementsAsync(odata, ct)` | `IReadOnlyList<Measurement>` | Query measurements |
| `GetTestResultAsync(id, ct)` | `TestResult` | Get single test result |

## MetadataStoreClient Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `QueryUutInstancesAsync(odata, ct)` | `IReadOnlyList<UutInstance>` | Query UUT instances |
| `QueryOperatorsAsync(odata, ct)` | `IReadOnlyList<Operator>` | Query operators |
| `QueryTestStationsAsync(odata, ct)` | `IReadOnlyList<TestStation>` | Query test stations |
| `CreateUutInstanceAsync(request, ct)` | `CreateUutInstanceResponse` | Create UUT instance (use `.UutInstanceId`) |
| `CreateOperatorAsync(request, ct)` | `CreateOperatorResponse` | Create operator (use `.OperatorId`) |

## Creating Metadata Entities

To associate a test result with a serial number and operator, create the metadata entities first:

```csharp
using NationalInstruments.Measurements.Data.V1;
using NationalInstruments.Measurements.Metadata.V1;
using NationalInstruments.Protobuf.Types;

using var client = new DataStoreClient();
using var metaClient = new MetadataStoreClient();

var timestamp = new PrecisionTimestamp { Seconds = DateTimeOffset.UtcNow.ToUnixTimeSeconds() };

// Create UutInstance (serial number)
var uutInstance = new UutInstance { SerialNumber = "DUT001" };
var uutRequest = new CreateUutInstanceRequest { UutInstance = uutInstance };
var uutResponse = await metaClient.CreateUutInstanceAsync(uutRequest, CancellationToken.None);
var uutInstanceId = uutResponse.UutInstanceId;  // Note: .UutInstanceId not direct string

// Create Operator
var operatorEntity = new Operator { Name = "Phil" };
var opRequest = new CreateOperatorRequest { Operator = operatorEntity };
var opResponse = await metaClient.CreateOperatorAsync(opRequest, CancellationToken.None);
var operatorId = opResponse.OperatorId;  // Note: .OperatorId not direct string

// Create TestResult with metadata links
var testResult = new TestResult
{
    Name = "My_Test",
    Outcome = Outcome.Passed,
    StartDateTime = timestamp,
    EndDateTime = timestamp,
    UutInstanceId = uutInstanceId,  // Links to serial number
    OperatorId = operatorId         // Links to operator
};
var testResultRequest = new CreateTestResultRequest { TestResult = testResult };
var testResultId = await client.CreateTestResultAsync(testResultRequest, CancellationToken.None);
```

### Metadata Entity Properties

**UutInstance**:
- `Id` - GUID (set by server)
- `SerialNumber` - The serial number string
- `UutId` - Optional link to Uut type definition

**Operator**:
- `Id` - GUID (set by server)
- `Name` - Operator name

**TestResult** metadata links:
- `UutInstanceId` - Links to UutInstance for serial number
- `OperatorId` - Links to Operator
- `TestStationId` - Links to TestStation
- `TestDescriptionId` - Links to TestDescription
- `HardwareItemIds` - List of hardware item IDs
- `SoftwareItemIds` - List of software item IDs

## Common Mistakes

1. **Wrong namespace for Scalar/PrecisionTimestamp**: Use `NationalInstruments.Protobuf.Types`, not `NationalInstruments.Measurements.Data.V1`

2. **Wrong property for step ID**: Use `stepResponse.StepId`, not `stepResponse.Step.Id`

3. **Missing testResultId on Step**: Step requires `TestResultId` to link to parent

4. **Missing stepId on Measurement**: Measurement requires `StepId` to link to parent step

5. **Wrong timestamp type**: `PrecisionTimestamp.Seconds` is `long`, not `ulong`

6. **Wrong return type for metadata creation**: `CreateUutInstanceAsync` returns `CreateUutInstanceResponse`, not `string`. Use `.UutInstanceId` to get the ID.

7. **Wrong return type for operator creation**: `CreateOperatorAsync` returns `CreateOperatorResponse`, not `string`. Use `.OperatorId` to get the ID.

6. **UutInstance vs TestResult**: Serial numbers are on `UutInstance`, not `TestResult`. Use `TestResult.UutInstanceId` to look up the serial.

## Response Types

```csharp
// CreateTestResultAsync returns string directly
string testResultId = await client.CreateTestResultAsync(...);

// CreateStepAsync returns CreateStepResponse
CreateStepResponse stepResponse = await client.CreateStepAsync(...);
string stepId = stepResponse.StepId;

// PublishMeasurementAsync returns PublishMeasurementResponse (JSON-like)
var measurementResponse = await client.PublishMeasurementAsync(...);
// Contains measurementId in the response
```
