---
name: ni-hw-drivers-csharp
description: "Generate complete, production-ready C# code for NI (National Instruments) modular instrument drivers with automatic signal generation. Covers NI-DCPower, NI-DMM, NI-SCOPE, NI-FGEN, NI-Switch, NI-Digital, NI-RFSA, NI-RFSG, and RFmx (SpecAn, LTE, NR, WLAN, BT, GSM, WCDMA). Specializes in complete RF test workflows: generate wireless signals with RFSG → trigger with IQPowerEdge → measure with RFmx. Use when users mention C#, .NET, Visual Studio, NuGet, or request RF measurements like 'measure 802.11ac EVM' or 'test LTE signal'. Automatically includes RFSG signal generation for all RF measurement requests."
argument-hint: "Describe the instrument type (SMU, DMM, scope, RF analyzer, etc.), measurement task, wireless standard (WLAN/LTE/5G/BT if RF), and target hardware. For RF measurements, will automatically generate appropriate test signal."
user-invocable: true
---

# NI Hardware Drivers for C#

Generate production-quality C# code for NI modular instrument drivers. Covers both traditional instrument drivers (DC Power, DMM, Scope, FGEN, Switch, Digital) and RF drivers (RFSA, RFSG, RFmx personalities). Supports both **console applications** and **WinForms GUI applications** with professional dark themes.

## ⚠️ CRITICAL: Read This First

**Before generating any NI C# code**, read [`references/RF-MEASUREMENT-GUIDE.md`](references/RF-MEASUREMENT-GUIDE.md) for complete patterns and corrections:

- **✅ MUST use .NET Framework 4.8** (NOT .NET Core/5+/8.0) for GAC assembly compatibility
- **📁 Waveform files location**: `C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\` — **always list files before hardcoding, prefix varies by NI version**
- **🏭 RFmx factory methods**: Use `instrSession.GetWlanSignalConfiguration()` NOT `new RFmxWlanMX()`
- **🔤 Property naming**: `Txp` not `TxP`, `OfdmModAcc` not `OFDMModAcc` (camelCase)
- **🔧 Hardware selection**: Use PXIe-5842/5841 VST for RF, NEVER use PXIe-5655 for waveform generation
- **📡 SEM arrays use `ref`**: `FetchSpectrum`, `FetchLowerOffsetMarginArray`, `FetchUpperOffsetMarginArray` — all use `ref` not `out`
- **📡 SEM `ConfigureAveraging` needs 4 params**: `(selectorString, enabled, count, averagingType)`
- **📡 `Spectrum<float>` properties**: `StartFrequency`, `FrequencyIncrement`, `SampleCount`, `Samples.ToArray()` — NOT `RelativeInitialX`/`RelativeDeltaX`
- **🔤 `RFmxWlanMXStandard` enum**: `Standard802_11ag` covers both 802.11a and 802.11g — `Standard802_11a`/`_11g` do NOT exist
- **📝 Script naming**: No underscores in waveform names (`wlanwaveform` not `wlan_waveform`)
- **📡 Load real waveforms**: DO NOT generate WLAN/LTE/5G signals in code, use NI waveform files
- **⚙️ OfdmModAcc settings**: Always configure FrequencyErrorEstimationMethod, PhaseTracking, and ChannelEstimationType for optimal EVM
- **🖥️ GUI apps**: Use async/await pattern with Task.Run() for background measurement threads
- **📊 SEM in GUI**: When SEM is measured in a GUI, **ALWAYS** include an overlaid SEM spectrum trace chart (PSD + mask centered at 0 Hz offset). Use one PSD series per frequency with color-coding, single shared mask, downsample to ~800 pts. Use `TabControl` for grid+log to avoid clipping charts.

**This guide enables "one-prompt measurement" capability** - complete, working RF measurements from a single request.

## Why This Skill Exists

LLMs frequently hallucinate NI C# API details: inventing method names, using wrong enum values, misunderstanding the property hierarchy, or producing code that doesn't compile. This skill provides ground-truth patterns from NI's official C# examples and real-world validation.

## Supported Drivers

### Traditional Modular Instruments

| Driver | Instrument Type | Namespace | Status |
|--------|----------------|-----------|--------|
| NI-DCPower | DC Power Supplies, SMUs, Electronic Loads | `NationalInstruments.ModularInstruments.NIDCPower` | ✅ Active |
| NI-DMM | Digital Multimeters | `NationalInstruments.ModularInstruments.NIDmm` | ✅ Active |
| NI-SCOPE | Oscilloscopes, Digitizers | `NationalInstruments.ModularInstruments.NIScope` | ✅ Active |
| NI-FGEN | Function/Arbitrary Waveform Generators | `NationalInstruments.ModularInstruments.NIFgen` | ✅ Active |
| NI-Switch | Matrix/Multiplexer Switches | `NationalInstruments.ModularInstruments.NISwitch` | ✅ Active |
| NI-Digital | Digital Pattern Instruments | `NationalInstruments.ModularInstruments.NIDigital` | ✅ Active |

### RF Instruments

| Driver | Purpose | Namespace | Status |
|--------|---------|-----------|--------|
| NI-RFSA | RF Vector Signal Analyzer | `NationalInstruments.ModularInstruments.NIRfsa` | ✅ Active |
| NI-RFSG | RF Vector Signal Generator | `NationalInstruments.ModularInstruments.NIRfsg` | ✅ Active |
| **NI-RFSG Playback** | **TDMS Waveform Loading (CRITICAL)** | `NationalInstruments.ModularInstruments.NIRfsgPlayback` | ✅ Active |

### Synchronization

| Driver | Purpose | Namespace | Status |
|--------|---------|-----------|--------|
| **NI-TClock** | **Sub-nanosecond multi-instrument synchronization** | `NationalInstruments.ModularInstruments.SystemServices.TimingServices` | ✅ Active |
| RFmx SpecAn | Spectrum Analysis | `NationalInstruments.RFmx.SpecAnMX` | ✅ Active |
| RFmx LTE | LTE/LTE-Advanced Analysis | `NationalInstruments.RFmx.LTEMX` | ✅ Active |
| RFmx NR | 5G NR Analysis | `NationalInstruments.RFmx.NRMX` | ✅ Active |
| RFmx WLAN | Wi-Fi Analysis | `NationalInstruments.RFmx.WLANMX` | ✅ Active |
| RFmx Bluetooth | Bluetooth/BLE Analysis | `NationalInstruments.RFmx.BTMX` | ✅ Active |
| RFmx GSM/WCDMA/CDMA2k | Cellular Standards | Various RFmx personalities | ✅ Active |
| RFmx Pulse | Pulsed RF Analysis | `NationalInstruments.RFmx.PulseMX` | ✅ Active |
| RFmx Demod | Analog/Digital Demod | `NationalInstruments.RFmx.DemodMX` | ✅ Active |

## Installation & Setup

### GAC Assembly References (Recommended for .NET Framework 4.8)

For RF generation and measurement workflows, use GAC references with `.NET Framework 4.8`:

```xml
<ItemGroup>
  <!-- Core -->
  <Reference Include="Ivi.Driver">
    <HintPath>C:\Program Files\IVI Foundation\IVI\Microsoft.NET\Framework64\v2.0.50727\IviFoundationSharedComponents 2.0.0\Ivi.Driver.dll</HintPath>
    <Private>False</Private>
  </Reference>
  <Reference Include="NationalInstruments.Common">
    <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.Common\v4.0_19.1.40.49152__dc6ad606294fc298\NationalInstruments.Common.dll</HintPath>
    <Private>False</Private>
  </Reference>
  <Reference Include="NationalInstruments.ModularInstruments.Common">
    <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.Common 23.0.0\NationalInstruments.ModularInstruments.Common.dll</HintPath>
    <Private>False</Private>
  </Reference>

  <!-- RFSG + Playback (CRITICAL for TDMS waveforms) -->
  <Reference Include="NationalInstruments.ModularInstruments.NIRfsg.Fx40">
    <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.NIRfsg 23.0.0\NationalInstruments.ModularInstruments.NIRfsg.Fx40.dll</HintPath>
    <Private>False</Private>
  </Reference>
  <Reference Include="NationalInstruments.ModularInstruments.NIRfsgPlayback.Fx40">
    <HintPath>C:\Program Files (x86)\National Instruments\MeasurementStudioVS2010\DotNET\Assemblies\26.0.0.49263\NationalInstruments.ModularInstruments.NIRfsgPlayback.Fx40.dll</HintPath>
    <Private>False</Private>
  </Reference>

  <!-- RFmx -->
  <Reference Include="NationalInstruments.RFmx.InstrMX.Fx40">
    <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.RFmx.InstrMX.Fx40\v4.0_23.8.0.49286__dc6ad606294fc298\NationalInstruments.RFmx.InstrMX.Fx40.dll</HintPath>
    <Private>False</Private>
  </Reference>
  <Reference Include="NationalInstruments.RFmx.WlanMX.Fx40">
    <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.RFmx.WlanMX.Fx40\v4.0_23.8.0.49286__dc6ad606294fc298\NationalInstruments.RFmx.WlanMX.Fx40.dll</HintPath>
    <Private>False</Private>
  </Reference>
</ItemGroup>
```

### NuGet Packages (Alternative for .NET Core/5+)

**Note**: GAC references with .NET Framework 4.8 are recommended. NuGet packages may work for .NET Core but require additional configuration.

```xml
<!-- Traditional Instruments -->
<PackageReference Include="NationalInstruments.ModularInstruments.NIDCPower" Version="*" />
<PackageReference Include="NationalInstruments.ModularInstruments.NIDmm" Version="*" />
<PackageReference Include="NationalInstruments.ModularInstruments.NIScope" Version="*" />
<PackageReference Include="NationalInstruments.ModularInstruments.NIFgen" Version="*" />

<!-- RF Instruments -->
<PackageReference Include="NationalInstruments.ModularInstruments.NIRfsa" Version="*" />
<PackageReference Include="NationalInstruments.ModularInstruments.NIRfsg" Version="*" />
<PackageReference Include="NationalInstruments.RFmx.InstrMX" Version="*" />
<PackageReference Include="NationalInstruments.RFmx.SpecAnMX" Version="*" />
<PackageReference Include="NationalInstruments.RFmx.LTEMX" Version="*" />
<PackageReference Include="NationalInstruments.RFmx.NRMX" Version="*" />
<PackageReference Include="NationalInstruments.RFmx.WLANMX" Version="*" />
<PackageReference Include="NationalInstruments.RFmx.BTMX" Version="*" />

<!-- Device Discovery -->
<PackageReference Include="NationalInstruments.ModularInstruments.SystemServices" Version="*" />
```

### Runtime Requirements

- **NI driver runtime** must be installed (from ni.com/downloads)
- **✅ .NET Framework 4.8** (REQUIRED for GAC assemblies - see [RF-MEASUREMENT-GUIDE.md](references/RF-MEASUREMENT-GUIDE.md))
- **❌ NOT .NET Core/5+/8.0** (GAC assembly loading issues without additional configuration)
- C# NuGet packages are wrappers around native drivers

## Universal Patterns (All Drivers)

### 1. Session Lifecycle - IDisposable Pattern

**CRITICAL**: Always use `using` statements. NI driver sessions implement `IDisposable` and must be properly closed to release hardware resources.

```csharp
using NationalInstruments.ModularInstruments.NIDCPower;

// CORRECT: Using statement ensures disposal even on exception
using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    // Configure, measure...
}
// Session automatically closed, hardware safely released

// WRONG: Never do this
var session = new NIDCPower("PXI1Slot2/0", false, false);
// If exception occurs, session is leaked, hardware stays locked
```

### 2. Device Discovery

```csharp
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;

// Discover devices by driver family
using (var system = new ModularInstrumentsSystem("NI-DCPower"))
{
    foreach (DeviceInfo device in system.DeviceCollection)
    {
        Console.WriteLine($"{device.Name}: {device.Model}");
        // Example: "PXI1Slot2: PXIe-4162"
    }
}

// For RF instruments
using (var system = new ModularInstrumentsSystem("NI-RFSA"))
{
    // Lists all RFSA-compatible devices
}
```

### 3. Property-Based Configuration

NI C# APIs use a hierarchical property structure:

```csharp
// Traditional instruments use session.Outputs[channel] or direct properties
session.Source.Mode = DCPowerSourceMode.SinglePoint;
session.Outputs["0"].Source.Voltage.VoltageLevel = 5.0;
session.Outputs["0"].Source.Voltage.VoltageLevelRange = 6.0;
session.Outputs["0"].Source.Current.CurrentLimit = 0.1;

// RF instruments use direct property access
rfsaSession.Configuration.IQ.IQRate = 10e6;  // 10 MHz
rfsaSession.Configuration.ReferenceLevel = -10.0;  // dBm
```

### 4. Channel Addressing

```csharp
// Single channel
var channel = session.Outputs["0"];
channel.Source.Voltage.VoltageLevel = 3.3;

// Multiple channels with same configuration
var channels = session.Outputs["0,1"];
channels.Source.Voltage.VoltageLevel = 5.0;

// Channel range
var channelRange = session.Outputs["0-3"];
channelRange.Control.Commit();
```

### 5. Error Handling

```csharp
using NationalInstruments.ModularInstruments.NIDCPower;
using System;

try
{
    using (var session = new NIDCPower(resourceName, false, false))
    {
        session.Outputs[channel].Source.Voltage.VoltageLevel = voltageLevel;
        session.Control.Initiate();
        var measurement = session.Outputs[channel].Measurement.Measure(
            DCPowerMeasurementTypes.Voltage | DCPowerMeasurementTypes.Current);
    }
}
catch (NationalInstruments.ModularInstruments.NIDCPower.NIDCPowerException ex)
{
    Console.WriteLine($"NI-DCPower Error: {ex.Message}");
    Console.WriteLine($"Error Code: {ex.ErrorCode}");
}
catch (Exception ex)
{
    Console.WriteLine($"Unexpected error: {ex.Message}");
}
```

## Common Instrument Patterns

### DC Power (SMU/Power Supply)

```csharp
using NationalInstruments.ModularInstruments.NIDCPower;

using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    var channel = session.Outputs["0"];

    // Configure for voltage sourcing
    session.Source.Mode = DCPowerSourceMode.SinglePoint;
    channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
    channel.Source.Voltage.VoltageLevel = 5.0;
    channel.Source.Voltage.VoltageLevelRange = 6.0;
    channel.Source.Current.CurrentLimit = 0.5;
    channel.Source.Current.CurrentLimitRange = 0.6;

    // Enable output and measure
    channel.Control.Initiate();

    // Fetch measurement
    var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(1));
    Console.WriteLine($"Voltage: {measurement.Voltage} V");
    Console.WriteLine($"Current: {measurement.Current} A");
    Console.WriteLine($"In Compliance: {measurement.InCompliance}");

    // Disable output
    channel.Control.Abort();
}
```

### DMM (Multimeter)

```csharp
using NationalInstruments.ModularInstruments.NIDmm;

using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure DC voltage measurement
    dmm.ConfigureMeasurement(
        NIDmmMeasurementFunction.DCVolts,
        range: 10.0,
        resolutionDigits: 6.5);

    // Set aperture time for accuracy
    dmm.Configuration.MeasurementOptions.ApertureTime = 0.01;  // 10ms

    // Take reading
    double reading = dmm.Measurement.Read(TimeSpan.FromSeconds(1));
    Console.WriteLine($"Voltage: {reading:F6} V");

    // Multi-point acquisition
    dmm.Configuration.MultiPoint.MeasurementCount = 10;
    double[] readings = dmm.Measurement.ReadMultiPoint(10, TimeSpan.FromSeconds(5));
}
```

### Oscilloscope

```csharp
using NationalInstruments.ModularInstruments.NIScope;

using (var scope = new NIScope("PXI1Slot4", true, false))
{
    var channel = scope.Channels["0"];

    // Configure vertical
    channel.ConfigureVertical(
        range: 10.0,
        coupling: NIScopeVerticalCoupling.DC,
        offset: 0.0,
        probeAttenuation: 1.0,
        enabled: true);

    // Configure horizontal (timebase)
    scope.Timing.ConfigureHorizontalTiming(
        minSampleRate: 100e6,  // 100 MS/s
        minRecordLength: 1000,
        refPosition: 50.0,
        numRecords: 1,
        enforceRealtime: true);

    // Configure trigger
    scope.Trigger.ConfigureEdgeTrigger(
        triggerSource: "0",
        level: 0.0,
        slope: NIScopeTriggerSlope.Positive,
        triggerCoupling: NIScopeTriggerCoupling.DC,
        holdoff: 0.0,
        delay: 0.0);

    // Acquire
    scope.Acquisition.Initiate();

    // Fetch waveform
    AnalogWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        numSamples: 1000,
        timeout: TimeSpan.FromSeconds(5));

    // Process waveform
    foreach (var sample in waveforms[0].Samples)
    {
        double voltage = waveforms[0].GetScaledValue(sample);
        // Process voltage...
    }
}
```

## RF Instrument Patterns

### RFSA (Vector Signal Analyzer)

```csharp
using NationalInstruments.ModularInstruments.NIRfsa;

using (var rfsa = new NIRfsa("RFSA", false, false))
{
    // Configure basic settings
    rfsa.Configuration.AcquisitionType = RFsaAcquisitionType.IQ;
    rfsa.Configuration.ReferenceLevel = -10.0;  // dBm
    rfsa.RF.Configure(
        carrierFrequency: 2.4e9,  // 2.4 GHz
        referenceLevel: -10.0);

    // Configure IQ acquisition
    rfsa.Configuration.IQ.IQRate = 10e6;  // 10 MS/s
    rfsa.Configuration.IQ.NumberOfSamples = 10000;

    // Configure trigger
    rfsa.Trigger.Type = RFsaTriggerType.IQPowerEdge;
    rfsa.Trigger.IQPowerEdge.Configure(
        source: RFsaIQPowerEdgeTriggerSource.Channel0,
        level: -20.0,
        slope: RFsaIQPowerEdgeTriggerSlope.Rising);

    // Initiate acquisition
    rfsa.Acquisition.Initiate();

    // Fetch IQ data
    ComplexWaveform<ComplexSingle> waveform = 
        rfsa.Acquisition.IQ.FetchIQSingleRecordComplexF32(
            recordNumber: 0,
            numberOfSamples: 10000,
            timeout: TimeSpan.FromSeconds(5));

    // Process IQ data
    foreach (var sample in waveform.Samples)
    {
        float magnitude = sample.Magnitude;
        float phase = sample.Phase;
        // Process...
    }
}
```

### RFSG (Vector Signal Generator)

```csharp
using NationalInstruments.ModularInstruments.NIRfsg;

using (var rfsg = new NIRfsg("RFSG", false, false))
{
    // Configure basic settings
    rfsg.RF.Configure(
        carrierFrequency: 2.4e9,  // 2.4 GHz
        powerLevel: -10.0);  // dBm

    // Configure continuous wave (CW)
    rfsg.RF.OutputEnabled = true;
    rfsg.Generation.GenerationMode = RFsgGenerationMode.CW;

    // Initiate generation
    rfsg.Generation.Initiate();

    // Wait for generation
    System.Threading.Thread.Sleep(1000);  // Generate for 1 second

    // Stop generation
    rfsg.Generation.Abort();
    rfsg.RF.OutputEnabled = false;
}
```

### RFmx (Signal-Specific Analysis)

RFmx uses a two-session pattern: `RFmxInstrMX` for hardware + personality class for measurements.

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.SpecAnMX;

using (var instrSession = new RFmxInstrMX("RFSA", ""))
using (var specAn = new RFmxSpecAnMX(instrSession))
{
    // Configure basic settings
    instrSession.ConfigureFrequencyReference(
        source: RFmxInstrMXConstants.OnboardClock,
        frequency: 10e6);

    specAn.ConfigureFrequency(
        centerFrequency: 2.4e9,
        referenceLevel: -10.0,
        externalAttenuation: 0.0);

    // Select measurement
    specAn.SelectMeasurements("", RFmxSpecAnMXMeasurementTypes.Acp, false);

    // Configure ACP (Adjacent Channel Power)
    specAn.Acp.Configuration.ConfigureNumberOfOffsets(
        numberOfOffsets: 2);
    specAn.Acp.Configuration.ConfigureOffsetFrequency(
        offsetNumber: 0,
        offsetFrequency: 1e6);  // 1 MHz offset

    // Configure averaging
    specAn.Acp.Configuration.ConfigureAveraging(
        averagingEnabled: RFmxSpecAnMXAcpAveragingEnabled.True,
        averagingCount: 10);

    // Initiate measurement
    specAn.Initiate("", "");

    // Fetch results
    double carrierPower;
    double[] lowerRelativePower = new double[2];
    double[] upperRelativePower = new double[2];

    specAn.Acp.Results.FetchRelativePowers(
        timeout: TimeSpan.FromSeconds(10),
        carrierChannelPower: out carrierPower,
        lowerRelativePower: lowerRelativePower,
        upperRelativePower: upperRelativePower);

    Console.WriteLine($"Carrier Power: {carrierPower:F2} dBm");
    Console.WriteLine($"Lower Offset 1: {lowerRelativePower[0]:F2} dBc");
    Console.WriteLine($"Upper Offset 1: {upperRelativePower[0]:F2} dBc");
}
```

### RFmx LTE Example

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.LTEMX;

using (var instrSession = new RFmxInstrMX("RFSA", ""))
using (var lte = new RFmxLTEMX(instrSession))
{
    // Configure frequency and reference level
    lte.ConfigureFrequency(
        centerFrequency: 1.95e9,  // Band 1 LTE
        referenceLevel: -20.0,
        externalAttenuation: 0.0);

    // Configure LTE standard
    lte.ComponentCarrier.SetBandwidth("", RFmxLTEMXBandwidth.Bandwidth20MHz);
    lte.ComponentCarrier.SetCellID("", 0);
    lte.SetDownlinkTestModel("", RFmxLTEMXDownlinkTestModel.TM1_1);
    lte.SetAutoResourceBlockDetectionEnabled("", RFmxLTEMXAutoResourceBlockDetectionEnabled.True);

    // Select ModAcc measurement
    lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ModAcc, true);

    // Configure averaging
    lte.ModAcc.Configuration.SetAveragingEnabled("", RFmxLTEMXModAccAveragingEnabled.True);
    lte.ModAcc.Configuration.SetAveragingCount("", 10);

    // Initiate
    lte.Initiate("", "");

    // Fetch EVM results
    double rmsEvm, peakEvm, frequencyError;
    lte.ModAcc.Results.FetchCompositeEVM(
        selectorString: "",
        timeout: TimeSpan.FromSeconds(10),
        compositeMeanRmsEVM: out rmsEvm,
        compositeMeanPeakEVM: out peakEvm,
        componentCarrierMeanFrequencyError: out frequencyError);

    Console.WriteLine($"RMS EVM: {rmsEvm:F2} dB");
    Console.WriteLine($"Peak EVM: {peakEvm:F2} dB");
    Console.WriteLine($"Frequency Error: {frequencyError:F2} Hz");
}
```

## Common Mistakes to Avoid

**⚠️ FIRST**: See [`references/RF-MEASUREMENT-GUIDE.md`](references/RF-MEASUREMENT-GUIDE.md) for recently discovered API corrections that are NOT in NI documentation:
- RFmx factory method pattern (NOT constructors)
- Property naming (camelCase not PascalCase)
- Waveform file locations and loading
- Hardware selection rules
- .NET Framework requirements

### 1. Using Wrong .NET Framework (CRITICAL)
```csharp
// WRONG: .NET Core/5+/8.0 cannot load GAC assemblies properly
// Project file with <TargetFramework>net8.0</TargetFramework>
// Results in: System.IO.FileNotFoundException for NI assemblies

// CORRECT: Use .NET Framework 4.8
// <TargetFramework>net48</TargetFramework>
// See RF-MEASUREMENT-GUIDE.md for complete GAC reference configuration
```

### 2. Generating WLAN/LTE/5G Waveforms in Code
```csharp
// WRONG: Generate complex modulated waveforms in code
ComplexSingle[] waveform = GenerateWlan11axWaveform();  // Missing proper preamble!

// CORRECT: Load from NI waveform files
string waveformPath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\WLAN_80211ax_80MHz.tdms";
rfsg.Arb.WriteWaveformFromFileTDMS(waveformPath, "wlanwaveform");
```

### 3. RFmx Constructor vs Factory Method
```csharp
// WRONG: Try to construct RFmx personality directly
var wlan = new RFmxWlanMX(instrSession, "");  // Compile error!

// CORRECT: Use factory method
RFmxInstrMX instrSession = new RFmxInstrMX("5842", "");
RFmxWlanMX wlan = instrSession.GetWlanSignalConfiguration();  // Factory method
```

### 4. RFmx Property Naming
```csharp
// WRONG: PascalCase (doesn't exist)
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.TxP, false);  // Compile error
wlan.OFDMModAcc.Results.FetchCompositeRmsEvm(...);  // Compile error

// CORRECT: camelCase
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.Txp, false);  // Txp
wlan.OfdmModAcc.Results.FetchCompositeRmsEvm(...);  // OfdmModAcc
```

### 5. RFSG Script Waveform Naming
```csharp
// WRONG: Underscores in waveform names
rfsg.Arb.WriteWaveform("wlan_waveform", data);  // Error: Invalid character '_'

// CORRECT: Alphanumeric only, no special characters
rfsg.Arb.WriteWaveform("wlanwaveform", data);  // Valid
```

### 6. Forgetting IDisposable Pattern
```csharp
// WRONG: Session not disposed
var session = new NIDCPower("PXI1Slot2/0", false, false);
session.Source.Mode = DCPowerSourceMode.SinglePoint;

// CORRECT: Use using statement
using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    session.Source.Mode = DCPowerSourceMode.SinglePoint;
}
```

### 2. Wrong Property Hierarchy
```csharp
// WRONG: Direct property doesn't exist
session.VoltageLevel = 5.0;  // Compile error

// CORRECT: Navigate property hierarchy
session.Outputs["0"].Source.Voltage.VoltageLevel = 5.0;
```

### 3. Forgetting to Initiate
```csharp
// WRONG: Configure but never initiate
session.Outputs["0"].Source.Voltage.VoltageLevel = 5.0;
var reading = session.Outputs["0"].Measurement.Measure();  // No output!

// CORRECT: Initiate before measuring
session.Outputs["0"].Source.Voltage.VoltageLevel = 5.0;
session.Outputs["0"].Control.Initiate();
var reading = session.Outputs["0"].Measurement.Measure();
```

### 4. Not Handling Compliance
```csharp
// WRONG: Ignore compliance status
var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(1));
Console.WriteLine($"Current: {measurement.Current}");

// CORRECT: Check compliance
var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(1));
if (measurement.InCompliance)
{
    Console.WriteLine("WARNING: Output hit current limit!");
}
Console.WriteLine($"Current: {measurement.Current}");
```

### 5. Wrong Enum Types
```csharp
// WRONG: Using wrong enum or raw values
session.Source.Mode = 0;  // Compile error or wrong mode

// CORRECT: Use correct enum type
session.Source.Mode = DCPowerSourceMode.SinglePoint;
```

### 6. RFmx Personality Class Confusion
```csharp
// WRONG: Try to measure directly from instrSession
instrSession.SelectMeasurements(...);  // Wrong class!

// CORRECT: Use personality class
using (var specAn = new RFmxSpecAnMX(instrSession))
{
    specAn.SelectMeasurements(...);  // Correct
}
```

## Performance Tips

1. **Reuse sessions** when making multiple measurements
2. **Batch property configuration** before `Initiate()` or `Commit()`
3. **Use appropriate timeout values** - too short causes errors, too long hangs UI
4. **Pre-allocate arrays** for waveform fetches
5. **Consider threading** for UI responsiveness during long measurements

## References

- **[📘 RF Measurement Guide](./references/RF-MEASUREMENT-GUIDE.md)** ⭐ **READ THIS FIRST** - Complete guide for "one-prompt measurement" capability: factory methods, camelCase, waveform files, .NET Framework requirements, optimal EVM configuration, GUI patterns, and working examples
- [NI-DCPower C# Reference](./references/nidcpower-csharp.md)
- [NI-DMM C# Reference](./references/nidmm-csharp.md)
- [NI-SCOPE C# Reference](./references/niscope-csharp.md)
- [RFSA/RFSG C# Reference](./references/rfsa-rfsg-csharp.md)
- [RFmx Personalities Reference](./references/rfmx-csharp.md)
- **[RFmx Generation + Measurement Workflows](./references/rfmx-generation-measurement-workflows.md)** ⭐ **Use this for complete RF test automation**
- [Common Patterns & Best Practices](./references/common-patterns-csharp.md)

**For RF measurements**: When users request wireless signal measurements (WLAN/LTE/5G/BT), **always read `RF-MEASUREMENT-GUIDE.md` and `rfmx-generation-measurement-workflows.md` first**. They contain complete patterns for:
- Signal generation with RFSG + NIRfsgPlayback
- IQPowerEdge triggering (default)
- RFmx measurements with optimal OfdmModAcc configuration
- Pass/Fail validation
- Resource cleanup
- **WinForms GUI patterns** with async/await for responsive UI

**For GUI applications**: See `RF-MEASUREMENT-GUIDE.md` WinForms section for:
- Async measurement pattern with Task.Run()
- Thread-safe UI updates (InvokeRequired)
- Professional dark theme styling
- DataGridView and Chart display components
- Input validation and file browsing
- Progress indication and error handling

## 🚨 GUI Crash Prevention — Lessons Learned (CRITICAL)

When building WinForms GUI applications for NI measurements, these issues cause **runtime crashes on startup or during measurement**. They MUST be avoided:

### 1. NumericUpDown Value Before Maximum (CRASH ON STARTUP)

**Root cause**: Object initializer does not guarantee property set order. Setting `Value` before `Maximum` throws `ArgumentOutOfRangeException` if value exceeds default max (100).

❌ **CRASHES** (value 600 > default max 100):
```csharp
var nud = new NumericUpDown { Value = 600m, Minimum = 0, Maximum = 10000, ... };
```

✅ **CORRECT** (set bounds first, then value):
```csharp
var nud = new NumericUpDown { DecimalPlaces = 1, Location = ..., Size = ... };
nud.Minimum = 0;
nud.Maximum = 10000;
nud.Value = 600m;
```

### 2. SEM Trace Fetch Requires EnableAllTraces (CRASH DURING MEASUREMENT)

**Root cause**: RFmx disables trace storage by default. Calling `FetchSpectrum` without enabling traces throws `-380408`.

✅ **REQUIRED** — call immediately after creating `RFmxInstrMX`:
```csharp
instrSession = new RFmxInstrMX(vstResource, "");
instrSession.SetForceAllTracesEnabled("", true);  // MUST be set before any measurement
```

### 3. Spectrum<float> API (COMPILE ERROR)

- `FetchSpectrum` 4th parameter is `ref Spectrum<float>`, NOT `ref float[]`
- Access sample data via `spectrum.Samples.ToArray()`, NOT `spectrum.GetRawData()`
- Properties: `StartFrequency`, `FrequencyIncrement`, `SampleCount`

### 4. SEM Trace Centering for Overlay Charts

When plotting SEM traces from multiple frequencies on one chart, subtract center frequency so traces overlap at 0 MHz:
```csharp
double centerFreqMHz = freq / 1e6;
double offsetMHz = (startFreqMHz + s * stepMHz) - centerFreqMHz;
semSeries.Points.AddXY(offsetMHz, data[s]);
```

## GUI Frequency Sweep Pattern — WLAN Multi-Band

**Trigger**: User asks to "Create a GUI" with frequency sweep for WLAN bands (2.4 GHz, 5 GHz, 6 GHz), or asks to add GUI to an existing RF measurement application.

**Reference implementation**: `WlanMeasurementGui/MainForm.cs` in this workspace.

### Architecture

| Component | Pattern |
|---|---|
| Project type | .NET Framework 4.8 SDK-style, `<OutputType>WinExe</OutputType>`, `<UseWindowsForms>true</UseWindowsForms>` |
| Chart library | `System.Windows.Forms.DataVisualization` (built-in, no NuGet) |
| Threading | `async void BtnRun_Click` → `await Task.Run(() => RunSweep(...))` |
| UI updates | `Invoke(new Action(() => { ... }))` from background thread |
| Frequency selection | `CheckedListBox` with Select All / Clear All buttons |
| Charts | Line charts for EVM/TxP, overlapping SEM spectrum traces per frequency |

### Standard WLAN Channel Frequencies

```csharp
// 2.4 GHz band
("2.4G Ch1 (2.412)", 2.412e9),
("2.4G Ch6 (2.437)", 2.437e9),
("2.4G Ch11 (2.462)", 2.462e9),
// 5 GHz band (UNII-1, UNII-2, UNII-2e, UNII-3)
("5G Ch36 (5.180)", 5.180e9),
("5G Ch44 (5.220)", 5.220e9),
("5G Ch52 (5.260)", 5.260e9),
("5G Ch100 (5.500)", 5.500e9),
("5G Ch149 (5.745)", 5.745e9),
("5G Ch161 (5.805)", 5.805e9),
// 6 GHz band (Wi-Fi 6E/7)
("6G Ch1 (5.955)", 5.955e9),
("6G Ch37 (5.985)", 5.985e9),
("6G Ch69 (6.145)", 6.145e9),
("6G Ch101 (6.305)", 6.305e9),
("6G Ch133 (6.465)", 6.465e9),
("6G Ch165 (6.625)", 6.625e9),
("6G Ch197 (6.785)", 6.785e9),
```

### GUI Layout (Dark Theme, 1440×900)

- **Left panel (300px)**: SMU config, RF config, CheckedListBox for frequencies, Run/Stop buttons, progress bar
- **Right top**: EVM line chart + TxP line chart (side by side)
- **Right middle**: SEM spectrum overlay chart (full width, all traces overlapping centered at 0 MHz, mask in red dashed)
- **Right bottom**: Console log (RichTextBox, Consolas font, green on black)

### Frequency Sweep Implementation (Named Signal Configs)

```csharp
// Independent LOs required for frequency sweep on PXIe-5842
instrSession.SetForceAllTracesEnabled("", true);
instrSession.SetAutomaticSGSASharedLO("", RFmxInstrMXAutomaticSGSASharedLO.Disabled);
instrSession.SetLOSource("", "Onboard");
rfsg.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;

for (int i = 0; i < frequencies.Count; i++)
{
    // Retune RFSG
    if (i > 0) { rfsg.Abort(); rfsg.RF.Frequency = freq; NIRfsgPlayback.SetScriptToGenerateSingleRfsg(...); rfsg.Initiate(); }

    // Fresh named signal config per point (avoids -380413)
    wlan?.Dispose();
    wlan = instrSession.GetWlanSignalConfiguration($"freq{i}");
    // ... full configure, AutoLevel, SelectMeasurements(..., false), Initiate, fetch ...
}
```

## Related Skills

- [Python NI Hardware Drivers](../ni-hw-drivers/SKILL.md) - Python equivalent
- [NI Measurement Data Services](../ni-measurement-data-services/SKILL.md) - Data logging
- [Creating TestStand Sequences](../creating-teststand-sequences/SKILL.md) - Test sequencing integration
