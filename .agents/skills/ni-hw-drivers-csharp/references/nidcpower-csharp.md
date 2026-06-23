# NI-DCPower C# API Reference

Complete reference for DC Power Supplies, SMUs (Source Measure Units), and Electronic Loads in C#.

## ⚠️ CRITICAL: .NET Framework 4.8 Required

NI-DCPower drivers **ONLY** work with **.NET Framework 4.8**, NOT .NET Core/5+/6/7/8.

**Project file template:**
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net48</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <Reference Include="NationalInstruments.ModularInstruments.NIDCPower.Fx40">
      <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.NIDCPower 24.3.0\NationalInstruments.ModularInstruments.NIDCPower.Fx40.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="NationalInstruments.ModularInstruments.Common">
      <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.Common 23.0.0\NationalInstruments.ModularInstruments.Common.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="NationalInstruments.Common">
      <HintPath>C:\Program Files (x86)\National Instruments\MeasurementStudioVS2015\DotNET\Assemblies\Current\NationalInstruments.Common.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="Ivi.Driver">
      <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\Ivi.Driver 2.0.0\Ivi.Driver.dll</HintPath>
      <Private>False</Private>
    </Reference>
  </ItemGroup>
</Project>
```

**Note:** Assembly versions (24.3.0, 23.0.0, etc.) must match installed NI software versions.

> **v25.5 system example** (verified working on NICon-2026 lab system):
> ```xml
> <Reference Include="NationalInstruments.ModularInstruments.NIDCPower.Fx40">
>   <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.NIDCPower 25.5.0\NationalInstruments.ModularInstruments.NIDCPower.Fx40.dll</HintPath>
>   <Private>False</Private>
> </Reference>
> <Reference Include="NationalInstruments.ModularInstruments.Common">
>   <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.Common 25.5.0\NationalInstruments.ModularInstruments.Common.dll</HintPath>
>   <Private>False</Private>
> </Reference>
> ```
> `NationalInstruments.Common` and `Ivi.Driver` are transitive — they produce MSB3245 warnings from the dotnet SDK resolver but resolve correctly from the NI GAC at runtime. This is expected and harmless.

## Namespace
```csharp
using NationalInstruments.ModularInstruments.NIDCPower;
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## Session Class

```csharp
// Constructor
public NIDCPower(string resourceName, bool idQuery, bool resetDevice)

// Parameters:
// - resourceName: "PXI1Slot2/0", "Dev1", "4139" (NI MAX alias), etc.
// - idQuery: false (recommended for performance)
// - resetDevice: false (recommended to preserve calibration)
```

## 🚨 CRITICAL API PATTERN: Abort Before Configuration

**Unlike RFmx/RFSG drivers, NIDCPower sessions START in a "running" state.**

You **MUST** call `Abort()` immediately after creating the session before setting any properties:

```csharp
var session = new NIDCPower("4139", false, false);
var channel = session.Outputs["0"];

// ✅ REQUIRED: Abort to allow property configuration
channel.Control.Abort();

// Now you can configure properties
session.Source.Mode = DCPowerSourceMode.SinglePoint;
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
// ... rest of configuration
```

**If you skip `Abort()`, you will get:**
```
IviCDriverException: Specified property cannot be set while the task is running.
Property: Output Function
Status Code: -200557
```

## 🚨 CRITICAL: Output.Enabled Must Be Set to True (Added 2026)

**The SMU output will NOT turn on unless `Output.Enabled = true` is explicitly set.**

Without this, `Commit()` + `Initiate()` succeed silently but the output stays at 0V/0mA.

❌ **WRONG** (output remains at 0V — no error raised!):
```csharp
channel.Control.Abort();
session.Source.Mode = DCPowerSourceMode.SinglePoint;
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
channel.Source.Voltage.VoltageLevel = 12.0;
channel.Source.Voltage.CurrentLimitHigh = 0.6;
channel.Control.Commit();
channel.Control.Initiate();
// Result: V=0.000V, I=0.00mA — output never enabled!
```

✅ **CORRECT** (always set `Output.Enabled = true` before `Commit`):
```csharp
channel.Control.Abort();
session.Source.Mode = DCPowerSourceMode.SinglePoint;
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
channel.Source.Voltage.VoltageLevel = 12.0;
channel.Source.Voltage.CurrentLimitHigh = 0.6;
channel.Source.Output.Enabled = true;  // ✅ REQUIRED
channel.Control.Commit();
channel.Control.Initiate();
// Result: V=12.000V, I=413.2mA — output enabled!
```

## 🚨 CRITICAL: CurrentLimit AND CurrentLimitHigh Both Required (Added 2026)

**Setting only `CurrentLimitHigh` causes the SMU to clamp at a low default (100mA).**

The `CurrentLimit` property sets the primary symmetric limit. `CurrentLimitHigh` sets the upper asymmetric limit. Both must be set to the desired value for the limit to take effect.

❌ **WRONG** (clamps at 100mA despite requesting 600mA):
```csharp
channel.Source.Voltage.CurrentLimitHigh = 0.6;  // Only sets asymmetric high
// Result: Current clamps at 100mA, InCompliance=True
```

✅ **CORRECT** (set both properties):
```csharp
channel.Source.Voltage.CurrentLimit = 0.6;      // Primary limit
channel.Source.Voltage.CurrentLimitHigh = 0.6;  // Asymmetric high limit
// Result: Current allowed up to 600mA
```

## 🚨 CRITICAL: Use Autorange to Avoid Range Conflicts (Added 2026)

**Always use autorange instead of manual ranges.** Manual range values may silently clip the voltage or current limit to a lower value than requested.

❌ **WRONG** (manual range — may conflict with requested values):
```csharp
channel.Source.Voltage.VoltageLevelRange = 6.0;   // ❌ Too small for 12V!
channel.Source.Voltage.VoltageLevel = 12.0;        // Error: -225140
channel.Source.Voltage.CurrentLimitRange = 1.0;
channel.Source.Voltage.CurrentLimitHigh = 0.6;
```

✅ **CORRECT** (autorange — instrument selects optimal range):
```csharp
channel.Source.Voltage.VoltageLevelAutorange = DCPowerSourceVoltageLevelAutorange.On;
channel.Source.Voltage.VoltageLevel = 12.0;
channel.Source.Voltage.CurrentLimitAutorange = DCPowerSourceCurrentLimitAutorange.On;
channel.Source.Voltage.CurrentLimit = 0.6;
channel.Source.Voltage.CurrentLimitHigh = 0.6;
```

**Autorange enum types** (verified from NIDCPower 26.0.0 DLL):

| Property | Enum Type | Values |
|---|---|---|
| `channel.Source.Voltage.VoltageLevelAutorange` | `DCPowerSourceVoltageLevelAutorange` | `On`, `Off` |
| `channel.Source.Voltage.CurrentLimitAutorange` | `DCPowerSourceCurrentLimitAutorange` | `On`, `Off` |
| `channel.Source.Current.CurrentLevelAutorange` | `DCPowerSourceCurrentLevelAutorange` | `On`, `Off` |
| `channel.Source.Current.VoltageLimitAutorange` | `DCPowerSourceVoltageLimitAutorange` | `On`, `Off` |

## Key Enumerations

### DCPowerSourceMode
```csharp
DCPowerSourceMode.SinglePoint      // Static sourcing
DCPowerSourceMode.Sequence         // Hardware-timed sequence
```

### DCPowerSourceOutputFunction
```csharp
DCPowerSourceOutputFunction.DCVoltage         // Voltage source
DCPowerSourceOutputFunction.DCCurrent         // Current source
```

**Note:** Some models (like PXIe-4139) support pulsed modes, but enumerations vary by driver version.

## Property Hierarchy

### Session Level
```csharp
session.Source.Mode                          // SinglePoint or Sequence
session.Outputs[channelName]                 // Access specific channel ("0", "1", etc.)
```

### Channel Level (session.Outputs["0"])

#### Source Configuration - Voltage Mode
```csharp
// Output function
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;

// Voltage setpoint (use autorange)
channel.Source.Voltage.VoltageLevelAutorange = DCPowerSourceVoltageLevelAutorange.On;
channel.Source.Voltage.VoltageLevel = 6.0;           // Voltage setpoint (V)

// Current compliance (limit) in voltage mode — set BOTH properties
channel.Source.Voltage.CurrentLimitAutorange = DCPowerSourceCurrentLimitAutorange.On;
channel.Source.Voltage.CurrentLimit = 0.5;           // Primary current limit (A)
channel.Source.Voltage.CurrentLimitHigh = 0.5;       // Asymmetric high limit (A)

// Enable output — REQUIRED or output stays at 0V
channel.Source.Output.Enabled = true;
```

**Important:** You MUST set both `CurrentLimit` AND `CurrentLimitHigh` to the same value. Setting only `CurrentLimitHigh` causes the SMU to clamp at a low default (100mA). Always use autorange to avoid range conflicts.

#### Source Configuration - Current Mode
```csharp
// Output function
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCCurrent;

// Current setpoint
channel.Source.Current.CurrentLevel = 0.1;           // Current setpoint (A)
channel.Source.Current.CurrentLevelRange = 0.5;      // Current range (A)

// Voltage compliance (limit) in current mode
channel.Source.Current.VoltageLimitHigh = 10.0;      // Voltage limit (V)
channel.Source.Current.VoltageLimitRange = 20.0;     // Voltage range (V)
```

#### Control
```csharp
channel.Control.Abort()      // Stop output / allow configuration (CALL FIRST!)
channel.Control.Commit()     // Validate and apply configuration
channel.Control.Initiate()   // Enable output
```

**Standard sequence:**
1. Create session
2. `Abort()` to allow configuration
3. Set all properties (autorange, voltage/current, limits)
4. Set `Output.Enabled = true` — **REQUIRED or output stays at 0V**
5. `Commit()` to validate
6. `Initiate()` to enable output
7. `Abort()` to disable when done
8. Dispose/Close session

## 🚨 Measurement API (v25.5) — session-level, NOT channel-level

**The measurement API is on the session object, not the channel object.**

```csharp
// ❌ WRONG — DCPowerOutput.Measurement does NOT have Voltage/Current sub-objects in v25.5
double v = channel.Measurement.Voltage.Measure();   // CS1061 compile error
double i = channel.Measurement.Current.Measure();   // CS1061 compile error

// ✅ CORRECT — use session.Measurement.Measure(channelString)
var result = session.Measurement.Measure("0");       // pass channel name as string
double v   = result.VoltageMeasurements[0];          // first element = channel "0"
double i   = result.CurrentMeasurements[0];
```

**Compliance query:**
```csharp
// ✅ CORRECT — also session-level, takes channel string
bool inCompliance = session.Measurement.QueryInCompliance("0");
```

**`DCPowerMeasureResult` properties:**
```csharp
result.VoltageMeasurements   // double[]  — one element per channel in the channelString
result.CurrentMeasurements   // double[]  — one element per channel in the channelString
```

**Why you need to store the channel name separately:**
Because `session.Measurement.Measure()` needs the channel string and `DCPowerOutput` does not expose it, store the channel name in your worker class alongside the session:

```csharp
private NIDCPower     _session;
private DCPowerOutput _channel;   // used for Source configuration
private string        _channelName;  // used for Measurement calls

// In OpenSession:
_channelName = cfg.Channel;       // e.g. "0"
_channel     = _session.Outputs[_channelName];

// In PollAsync:
var result = _session.Measurement.Measure(_channelName);
double v   = result.VoltageMeasurements[0];
double i   = result.CurrentMeasurements[0];
bool comp  = _session.Measurement.QueryInCompliance(_channelName);
```

## Common Workflows

### 1. Simple DC Voltage Source (PXIe-4139 Pattern)

**This is the VALIDATED pattern from real hardware testing:**

```csharp
using System;
using NationalInstruments.ModularInstruments.NIDCPower;

class Program
{
    static void Main()
    {
        NIDCPower session = null;

        try
        {
            // Create session (use NI MAX alias or "PXI1Slot2/0" format)
            session = new NIDCPower("4139", false, false);
            Console.WriteLine("Session created");

            var channel = session.Outputs["0"];

            // ✅ CRITICAL: Abort to allow configuration
            channel.Control.Abort();

            // Configure as voltage source
            session.Source.Mode = DCPowerSourceMode.SinglePoint;
            channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;

            // Set voltage with autorange
            channel.Source.Voltage.VoltageLevelAutorange = DCPowerSourceVoltageLevelAutorange.On;
            channel.Source.Voltage.VoltageLevel = 6.0;          // 6V output

            // Set current limit — MUST set BOTH CurrentLimit and CurrentLimitHigh
            channel.Source.Voltage.CurrentLimitAutorange = DCPowerSourceCurrentLimitAutorange.On;
            channel.Source.Voltage.CurrentLimit = 0.1;           // Primary limit (A)
            channel.Source.Voltage.CurrentLimitHigh = 0.1;       // Asymmetric high (A)

            // Enable output — REQUIRED or output stays at 0V
            channel.Source.Output.Enabled = true;

            Console.WriteLine("Configuration set");

            // Commit and enable
            channel.Control.Commit();
            Console.WriteLine("Configuration committed");

            channel.Control.Initiate();
            Console.WriteLine("Output ENABLED - 6V @ 100mA limit");

            // Read back measured voltage and current (v25.5 API)
            var meas = session.Measurement.Measure("0");
            Console.WriteLine($"Measured: {meas.VoltageMeasurements[0]:F3} V, {meas.CurrentMeasurements[0]*1000:F2} mA");
            bool comp = session.Measurement.QueryInCompliance("0");
            if (comp) Console.WriteLine("WARNING: In compliance — current limit reached");

            // Keep output on for testing
            Console.WriteLine("\nPress any key to disable output...");
            Console.ReadKey();

            // Disable output
            channel.Control.Abort();
            Console.WriteLine("Output disabled");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
        }
        finally
        {
            session?.Close();
            Console.WriteLine("Session closed");
        }
    }
}
```

**Output behavior:**
- Maintains 6.0V until load draws >500mA
- If load exceeds 500mA, enters current compliance
- In compliance: voltage drops, current clamps to 500mA

### 2. DC Current Source

```csharp
using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    var channel = session.Outputs["0"];

    // ✅ REQUIRED: Abort before configuration
    channel.Control.Abort();

    // Configure as current source
    session.Source.Mode = DCPowerSourceMode.SinglePoint;
    channel.Source.Output.Function = DCPowerSourceOutputFunction.DCCurrent;

    // Set current and voltage limit
    channel.Source.Current.CurrentLevel = 0.1;               // 100mA
    channel.Source.Current.CurrentLevelRange = 0.5;          // 500mA range
    channel.Source.Current.VoltageLimitHigh = 10.0;          // 10V limit
    channel.Source.Current.VoltageLimitRange = 20.0;         // 20V range

    // Enable output
    channel.Control.Commit();
    channel.Control.Initiate();

    Console.WriteLine("Sourcing 100mA with 10V compliance");
    Console.ReadKey();

    // Disable
    channel.Control.Abort();
}
```

### 3. Voltage Sweep (Parameterization After Initiate)

After calling `Initiate()`, you can change voltage/current levels without calling `Abort()`:

```csharp
using (var session = new NIDCPower("4139", false, false))
{
    var channel = session.Outputs["0"];

    // Initial configuration
    channel.Control.Abort();
    session.Source.Mode = DCPowerSourceMode.SinglePoint;
    channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
    channel.Source.Voltage.CurrentLimitHigh = 0.5;
    channel.Source.Voltage.CurrentLimitRange = 1.0;

    // Enable output ONCE
    channel.Control.Commit();
    channel.Control.Initiate();

    // Sweep voltage (no Abort() needed between changes)
    for (double voltage = 0.0; voltage <= 5.0; voltage += 0.5)
    {
        channel.Source.Voltage.VoltageLevel = voltage;
        channel.Source.Voltage.VoltageLevelRange = Math.Max(voltage * 1.2, 1.0);

        System.Threading.Thread.Sleep(100);  // Settling time

        Console.WriteLine($"Voltage set to {voltage:F1}V");
    }

    channel.Control.Abort();
}
```

### 4. Multi-Channel Parallel Source

```csharp
using (var session = new NIDCPower("PXI1Slot2", false, false))
{
    // Configure all channels at once using channel list
    var channels = session.Outputs["0,1,2,3"];

    // ✅ Abort all channels
    channels.Control.Abort();

    session.Source.Mode = DCPowerSourceMode.SinglePoint;
    channels.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
    channels.Source.Voltage.VoltageLevel = 3.3;
    channels.Source.Voltage.VoltageLevelRange = 6.0;
    channels.Source.Voltage.CurrentLimitHigh = 0.5;
    channels.Source.Voltage.CurrentLimitRange = 1.0;

    // Initiate all channels simultaneously
    channels.Control.Commit();
    channels.Control.Initiate();

    Console.WriteLine("All 4 channels sourcing 3.3V");
    Console.ReadKey();

    channels.Control.Abort();
}
```

## ⚠️ Common Errors and Solutions

### Error: "Property cannot be set while task is running" (Status: -200557)

**Cause:** Trying to set properties after session is initiated.

**Solution:** Call `channel.Control.Abort()` immediately after creating the session:

```csharp
var session = new NIDCPower("4139", false, false);
var channel = session.Outputs["0"];

// ✅ FIX: Abort before configuration
channel.Control.Abort();

// Now properties can be set
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
```

### Error: "Device not found" or "Resource name invalid"

**Cause:** Incorrect resource name or device not simulated.

**Solutions:**
1. Use NI MAX alias (simpler): `"4139"`, `"DCPower1"`, etc.
2. Use PXI notation: `"PXI1Slot2/0"` (module in Slot 2, channel 0)
3. For simulated devices, create in NI MAX first:
   - Tools → Create Simulated Device
   - Select model (e.g., PXIe-4139)
   - Assign slot number
   - Give it an alias

### Error: Current limit clamps at 100mA despite setting 600mA (Added 2026)

**Cause:** Only `CurrentLimitHigh` was set. The primary `CurrentLimit` property was left at the default (100mA).

**Solution:** Set BOTH `CurrentLimit` AND `CurrentLimitHigh` to the desired value, and use autorange:
```csharp
channel.Source.Voltage.CurrentLimitAutorange = DCPowerSourceCurrentLimitAutorange.On;
channel.Source.Voltage.CurrentLimit = 0.6;       // Primary limit — REQUIRED
channel.Source.Voltage.CurrentLimitHigh = 0.6;   // Asymmetric high limit
```

### Error: 'CurrentLimit' or 'VoltageLimit' does not exist

**Cause:** API changed between driver versions. Both properties exist in v26.0.

**Solution:** Set both properties:
```csharp
// Voltage source mode — set both current limit properties
channel.Source.Voltage.CurrentLimit = 0.5;
channel.Source.Voltage.CurrentLimitHigh = 0.5;

// Current source mode — set both voltage limit properties
channel.Source.Current.VoltageLimitHigh = 10.0;
```

**Use autorange instead of manual ranges** to avoid range conflicts:
```csharp
channel.Source.Voltage.CurrentLimitAutorange = DCPowerSourceCurrentLimitAutorange.On;
channel.Source.Voltage.CurrentLimit = currentLimitA;
channel.Source.Voltage.CurrentLimitHigh = currentLimitA;
```

### Error: `channel.Measurement.Voltage.Measure()` — CS1061 'DCPowerOutputMeasurement' does not contain a definition for 'Voltage'

**Cause:** In v25.5, `DCPowerOutputMeasurement` (the type of `channel.Measurement`) no longer has `Voltage`/`Current` sub-properties. The measurement API moved to the session level.

**Solution:** Use `session.Measurement.Measure(channelString)` instead:
```csharp
// ❌ v24 style — does not compile in v25.5
double v = channel.Measurement.Voltage.Measure();

// ✅ v25.5 style
var result = session.Measurement.Measure("0");
double v   = result.VoltageMeasurements[0];
double i   = result.CurrentMeasurements[0];
bool comp  = session.Measurement.QueryInCompliance("0");
```

### Error: "PrecisionTimeSpan" not found

**Cause:** API varies by driver version.

**Solution:** Use standard `TimeSpan` or omit timing properties for simple applications.

### Error: ".NET Framework 4.8 targeting pack not installed"

**Cause:** Missing .NET Framework 4.8 SDK.

**Solution:** Install from Visual Studio Installer:
1. Open Visual Studio Installer
2. Modify your VS installation
3. Individual Components → .NET Framework 4.8 targeting pack

## API Version Differences

NI-DCPower API varies significantly between versions:

| Version | CurrentLimit Property | Measurement API | Notes |
|---------|----------------------|-----------------|-------|
| 24.3.0  | `CurrentLimitHigh`   | Limited         | Stable, use for compatibility |
| 25.0.0  | `CurrentLimitHigh`   | Enhanced        | More measurement methods |
| 25.5.0+ | `CurrentLimitHigh`   | Full featured   | Latest features — **use patterns below** |

**Recommendation:** Use v25.5.0 patterns shown in this guide. The measurement API changed substantially in v25.5 — see the Measurement section below.

## Best Practices

1. **Always call `Abort()` before configuration** - Critical difference from RFmx/RFSG
2. **Use NI MAX aliases** - Simpler than PXI notation, portable across systems
3. **Set ranges explicitly** - Don't rely on autoranging for critical applications
4. **Size `CurrentLimitRange` to ≥ 2× the limit** - e.g. `CurrentLimitRange = Math.Max(limit * 2, 0.01)`
5. **Check compliance** - Use `session.Measurement.QueryInCompliance(channelString)` (v25.5+)
6. **Use `session.Measurement.Measure(channelString)` for readback** - NOT `channel.Measurement.Voltage/Current` (removed in v25.5)
7. **Store channel name alongside session** - `session.Measurement.Measure()` needs the channel string; `DCPowerOutput` does not expose it
8. **Use `Commit()` before `Initiate()`** - Validates configuration before enabling output
9. **Clean up properly** - Always `Abort()` and `Close()` in finally block
10. **Target .NET Framework 4.8** - Required for NI GAC assemblies; `NationalInstruments.Common` and `Ivi.Driver` MSB3245 warnings are expected and harmless
11. **Use `.Fx40` assemblies** - These are the Framework 4.0+ compatible versions

## Resource Name Formats

```csharp
// NI MAX alias (RECOMMENDED for simulated devices)
"4139"
"DCPower1"
"MySMU"

// PXI notation
"PXI1Slot2"         // All channels on module in slot 2
"PXI1Slot2/0"       // Channel 0 only
"PXI1Slot2/0,1"     // Channels 0 and 1

// DAQmx-style alias
"Dev1"
"Dev1/0"
```

## Simulated Device Setup in NI MAX

1. Open NI MAX (Start → NI MAX)
2. Right-click "Devices and Interfaces"
3. Create New → Simulated NI-DAQmx Device or Modular Instrument
4. Select device model (e.g., PXIe-4139)
5. Configure:
   - Slot: Choose available slot (e.g., 8)
   - Alias: Give friendly name (e.g., "4139")
6. Click Finish
7. Use the alias in your code: `new NIDCPower("4139", false, false)`

## Related Skills

- **ni-hw-drivers**: Python version of NI-DCPower
- **ni-hw-drivers-csharp**: General C# NI driver patterns
- **RF-MEASUREMENT-GUIDE.md**: Complete .NET Framework 4.8 project setup patterns
    channel.Source.Voltage.VoltageLevel = 5.0;
    channel.Source.Voltage.VoltageLevelRange = 6.0;
    channel.Source.Current.CurrentLimit = 1.0;

    // Configure continuous measurement
    channel.Measurement.Record.Length = 1000;  // Buffer size
    channel.Measurement.Record.LengthIsFinite = false;  // Continuous
    channel.Measurement.MeasureWhen = DCPowerMeasureWhen.AutomaticallyAfterSourceComplete;

    channel.Control.Initiate();

    // Continuous fetch loop
    int totalSamples = 0;
    while (totalSamples < 10000)
    {
        // Fetch available data
        var measurements = channel.Measurement.FetchMultiple(
            count: 100,
            timeout: TimeSpan.FromSeconds(1));

        foreach (var m in measurements)
        {
            Console.WriteLine($"{totalSamples}: {m.Voltage:F6}V, {m.Current:F6}A");
            totalSamples++;

            // Save to file or database
            LogMeasurement(m);
        }
    }

    channel.Control.Abort();
}
```

## Measurement Result Properties

```csharp
DCPowerMeasurement measurement = channel.Measurement.Measure();

// Available properties:
measurement.Voltage          // double, measured voltage (V)
measurement.Current          // double, measured current (A)
measurement.InCompliance     // bool, true if hit limit
measurement.ChannelName      // string, channel that measured
```

## Range Selection Guidelines

- Set range to ~20% above expected value for best resolution
- Larger ranges = less resolution but more margin
- Auto-ranging available but slower

```csharp
// Manual ranging (recommended for performance)
channel.Source.Voltage.VoltageLevelRange = 6.0;  // For 5V output

// Auto-ranging
channel.Source.Voltage.VoltageLevelAutoRange = true;
```

## Remote vs Local Sense

```csharp
// Local sense (2-wire, default)
channel.Measurement.Sense = DCPowerSense.Local;

// Remote sense (4-wire, compensates for lead resistance)
channel.Measurement.Sense = DCPowerSense.Remote;
```

## Common Errors

### Error -200532: Channel Already Initiated
```csharp
// WRONG: Calling Initiate() twice
channel.Control.Initiate();
channel.Control.Initiate();  // ERROR!

// CORRECT: Abort before re-initiating
channel.Control.Abort();
channel.Control.Initiate();  // OK
```

### Error -200229: Insufficient Range
```csharp
// WRONG: Range too small for level
channel.Source.Voltage.VoltageLevelRange = 1.0;
channel.Source.Voltage.VoltageLevel = 5.0;  // ERROR: 5V > 1V range

// CORRECT: Range >= level
channel.Source.Voltage.VoltageLevelRange = 6.0;
channel.Source.Voltage.VoltageLevel = 5.0;  // OK
```

## Performance Tips

1. **Reuse sessions** - Don't create/dispose repeatedly
2. **Set properties before Initiate()** - Batch configuration
3. **Use appropriate ranges** - Auto-ranging is slow
4. **Optimize measurement timing** - Balance speed vs accuracy
5. **Use FetchMultiple** for high-speed logging

## Supported Devices

- PXIe-4135/4136/4137/4138/4139 (SMU)
- PXIe-4141/4142/4143/4144/4145 (SMU)
- PXIe-4154/4162/4163 (SMU)
- PXIe-4051 (Electronic Load)
- PXI-4130/4132 (Power Supply)
- And many others - check NI website

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [Example: Voltage Sweep](../examples/dcpower-voltage-sweep.cs)
- [Example: IV Characterization](../examples/dcpower-iv-curve.cs)
