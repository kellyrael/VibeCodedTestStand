# RF Measurement Guide - NI C# Drivers

**Purpose**: Complete guide for building RF measurement applications with NI C# drivers. Enables **"one-prompt measurement"** — generate complete, working WLAN measurements (console or GUI) from a single request.

**Covers**: .NET Framework 4.8 + GAC references, waveform loading via NIRfsgPlayback, RFmx API corrections (factory methods, camelCase, out/ref params), optimal EVM/SEM configuration, IQPowerEdge triggering + AutoLevel, frequency sweeps, RFSG script naming, hardware selection, and a complete console example. For GUI apps, see the dedicated `ni-measurement-gui-winforms` skill.

**Based on**: Real-world testing with PXIe-5842/5841/5860 VST, validated EVM results (-53 dB).

**Expected**: Compiles first try; EVM -50 to -56 dB typical; ~15-20 s per measurement (3-5s with AutoLevel).

---

## CRITICAL: .NET Framework Requirements

### ❌ DO NOT USE .NET Core / .NET 5+ / .NET 8.0

NI assemblies in the Global Assembly Cache (GAC) **do not work** with .NET Core/.NET 5+/.NET 8.0 without additional configuration.

### ✅ ALWAYS USE .NET Framework 4.8 SDK-Style Project

**COPY THIS EXACTLY** - Do not modify assembly names or hint paths:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>  <!-- Use WinExe for GUI -->
    <TargetFramework>net48</TargetFramework>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <!-- For GUI add: -->
    <!-- <UseWindowsForms>true</UseWindowsForms> -->
  </PropertyGroup>
  <ItemGroup>
    <!-- For GUI add: -->
    <!-- <Reference Include="System.Windows.Forms.DataVisualization" /> -->

    <!-- Core - COPY THESE EXACTLY -->
    <Reference Include="Ivi.Driver">
      <HintPath>C:\Program Files\IVI Foundation\IVI\Microsoft.NET\Framework64\v2.0.50727\IviFoundationSharedComponents 2.0.0\Ivi.Driver.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="NationalInstruments.Common">
      <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.Common\v4.0_19.1.40.49152__dc6ad606294fc298\NationalInstruments.Common.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="NationalInstruments.ModularInstruments.Common">
      <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.Common 26.0.0\NationalInstruments.ModularInstruments.Common.dll</HintPath>
      <Private>False</Private>
    </Reference>

    <!-- RFSG + Playback - NOTICE .Fx40 suffix -->
    <Reference Include="NationalInstruments.ModularInstruments.NIRfsg.Fx40">
      <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.ModularInstruments.NIRfsg.Fx40\v4.0_26.0.0.49398__dc6ad606294fc298\NationalInstruments.ModularInstruments.NIRfsg.Fx40.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="NationalInstruments.ModularInstruments.NIRfsgPlayback.Fx40">
      <HintPath>C:\Program Files (x86)\National Instruments\MeasurementStudioVS2010\DotNET\Assemblies\26.3.0.49278\NationalInstruments.ModularInstruments.NIRfsgPlayback.Fx40.dll</HintPath>
      <Private>False</Private>
    </Reference>

    <!-- RFmx - NOTICE .Fx40 suffix -->
    <Reference Include="NationalInstruments.RFmx.InstrMX.Fx40">
      <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.RFmx.InstrMX.Fx40\v4.0_26.3.0.49278__dc6ad606294fc298\NationalInstruments.RFmx.InstrMX.Fx40.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="NationalInstruments.RFmx.WlanMX.Fx40">
      <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.RFmx.WlanMX.Fx40\v4.0_26.3.0.49278__dc6ad606294fc298\NationalInstruments.RFmx.WlanMX.Fx40.dll</HintPath>
      <Private>False</Private>
    </Reference>

    <!-- Optional: NI-DCPower for SMU control (if combining RF + power supply) -->
    <!--
    <Reference Include="NationalInstruments.ModularInstruments.NIDCPower.Fx40">
      <HintPath>C:\Program Files (x86)\IVI Foundation\IVI\Microsoft.NET\Framework32\v4.0.30319\NationalInstruments.ModularInstruments.NIDCPower 26.0.0\NationalInstruments.ModularInstruments.NIDCPower.Fx40.dll</HintPath>
      <Private>False</Private>
    </Reference>
    -->
  </ItemGroup>
</Project>
```

**CRITICAL NOTES**:
- ✅ **USE SDK-style project format** (`<Project Sdk="Microsoft.NET.Sdk">`)
- ✅ **USE `.Fx40` suffix** on NI assembly names (e.g., `NIRfsg.Fx40` not `NIRfsg`)
- ✅ **SET `Private=False`** on all NI references
- ✅ **COPY hint paths exactly** - these are the actual GAC/IVI locations
- ❌ **DO NOT use old-style project format** (with ToolsVersion, Import statements)
- ❌ **DO NOT try to simplify or "fix" the hint paths**

**Why `.Fx40` suffix**:
- These are the .NET Framework 4.0+ compatible versions
- Standard assemblies (without suffix) may not have all APIs
- All validated examples use `.Fx40` versions

### Combining RF Measurements with Power Supply Control

To combine RF measurements (RFmx/RFSG) with SMU power control (NI-DCPower), uncomment the NIDCPower reference in the project template above.

**⚠️ CRITICAL SMU Configuration Rules (Added 2026):**
1. **`Output.Enabled = true`** — without this the SMU outputs 0V silently
2. **Set BOTH `CurrentLimit` AND `CurrentLimitHigh`** — setting only `CurrentLimitHigh` clamps at 100mA
3. **Use autorange** — manual ranges cause `-225140` if range is too small
4. **Source voltage BEFORE starting RF** — DUT must be powered before signal generation

**Example** (WLAN power amplifier characterization):
```csharp
// 1. Configure and enable SMU FIRST (DUT must be powered before RF)
var smu = new NIDCPower("PXI1Slot9_2", false, false);
var smuChannel = smu.Outputs["0"];
smuChannel.Control.Abort();  // CRITICAL: abort before config
smu.Source.Mode = DCPowerSourceMode.SinglePoint;
smuChannel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
smuChannel.Source.Voltage.VoltageLevelAutorange = DCPowerSourceVoltageLevelAutorange.On;
smuChannel.Source.Voltage.VoltageLevel = 12.0;
smuChannel.Source.Voltage.CurrentLimitAutorange = DCPowerSourceCurrentLimitAutorange.On;
smuChannel.Source.Voltage.CurrentLimit = 0.6;       // MUST set both
smuChannel.Source.Voltage.CurrentLimitHigh = 0.6;   // MUST set both
smuChannel.Source.Output.Enabled = true;            // REQUIRED or output stays at 0V!
smuChannel.Control.Commit();
smuChannel.Control.Initiate();
if (smu.Measurement.QueryInCompliance("0")) Console.WriteLine("WARNING: SMU in compliance!");

// 2. Set up RFSG + RFmx for RF measurements (see examples below)

// 3. Cleanup — disable RF first, then SMU
rfsg.Abort(); rfsg.RF.OutputEnabled = false; rfsg.Close();
wlan?.Dispose(); instrSession?.Close();
smuChannel.Control.Abort();  // disable power last
smu.Close();
```

**See also**: `.agents/skills/ni-hw-drivers-csharp/references/nidcpower-csharp.md` for complete NI-DCPower patterns.

---

## NI Waveform File Locations

### Standard Waveform Paths

**RFIC Test Software Waveforms** (Primary):
```
C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\
```

**NI-WLAN Waveforms** (Secondary):
```
C:\Users\Public\Documents\National Instruments\NI-WLAN\
```

**Common Formats**:
- `.tdms` - Time-Domain Measurement Signal format
- `.tdms.index` - Index file for TDMS
- `.rfws` - RF Waveform Signal format

### ⚠️ Waveform Naming — Discover Before Hardcoding

**CRITICAL**: Waveform filenames vary by NI software version and installation. The prefix `RFIC_` is present on some installations and absent on others. **Always list the actual files before hardcoding a path.**

**PowerShell — discover all waveforms on this system**:
```powershell
Get-ChildItem "C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\" -Filter "*.tdms" |
    Where-Object { $_.Name -notmatch "\.index$" } |
    Select-Object -ExpandProperty Name | Sort-Object
```

### Waveform Catalog — Actual Files on This System

The table below reflects the real filenames found in the waveform folder.
Run the PowerShell command above to refresh this list after NI software updates.

#### WLAN (802.11ac / ax / be)

| File | Standard | Bandwidth | MCS / Notes |
|---|---|---|---|
| `80211ac_20MHz.tdms` | 802.11ac | 20 MHz | — |
| `80211ac_40MHz.tdms` | 802.11ac | 40 MHz | — |
| `80211ac_80MHz.tdms` | 802.11ac | 80 MHz | — |
| `80211ax_20MHz.tdms` | 802.11ax | 20 MHz | — |
| `80211ax_40MHz.tdms` | 802.11ax | 40 MHz | — |
| `80211ax_80MHz.tdms` | 802.11ax | 80 MHz | generic |
| `80211ax_80M_MCS11.tdms` | 802.11ax | 80 MHz | **MCS11 (1024-QAM) — preferred for EVM** |
| `80211be_80M_MCS0.tdms` | 802.11be | 80 MHz | MCS0 |
| `80211be_80M_MCS11.tdms` | 802.11be | 80 MHz | MCS11 |
| `80211be_320M_MCS13_EHT_SIG.tdms` | 802.11be | 320 MHz | MCS13 EHT-SIG |

**Selection rule for WLAN**:
- Prefer the `_MCS11` variant for EVM testing (highest modulation, most demanding)
- Use the generic `_80MHz` variant when MCS-specific file is unavailable
- Match `ConfigureChannelBandwidth()` to the MHz value in the filename

> **LTE / 5G NR**: The same NIRfsgPlayback loading pattern applies. Discover actual files with the PowerShell command above (e.g. `LTE_FDD_DL_*`, `NR_FR1_DL_*`, `NR_FR2_*`) — do not hardcode filenames.

### Loading Waveforms with NIRfsgPlayback

**✅ CORRECT METHOD** (Use NIRfsgPlayback API):
```csharp
using System;
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.NIRfsgPlayback;

string waveformPath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\80211ax_80M_MCS11.tdms";
string waveformName = "wlan80211ax";  // No underscores!

// Create RFSG session
NIRfsg rfsg = new NIRfsg("5842", true, false, "");
IntPtr rfsgHandle = rfsg.GetInstrumentHandle().DangerousGetHandle();

// Load waveform using NIRfsgPlayback
NIRfsgPlayback.ReadAndDownloadWaveformFromFile(rfsgHandle, waveformPath, waveformName);

// Create script and initiate
string script = 
    "script wlanScript\n" +
    "repeat forever\n" +
    $"generate {waveformName}\n" +
    "end repeat\n" +
    "end script";

NIRfsgPlayback.SetScriptToGenerateSingleRfsg(rfsgHandle, script);
rfsg.Initiate();
```

**Why NIRfsgPlayback**: handles TDMS format and metadata (IQ rate, markers) correctly; used by all NI reference examples. More reliable than `Arb.WriteWaveform()`.

**❌ AVOID** `rfsg.Arb.WriteWaveformFromFileTDMS(...)` — may not work with complex TDMS files.

**Critical**: Do NOT generate WLAN/LTE/5G waveforms in code except for simple testing. Use pre-generated compliant waveforms from NI tools.

---

## RFmx API Corrections - MANDATORY PATTERNS

**CRITICAL**: These are the most common mistakes. Copy these patterns exactly.

### 0. RFmxWlanMXStandard Enum — Complete Valid Values

❌ **WRONG** (these enum members do NOT exist and cause compile errors):
```csharp
RFmxWlanMXStandard.Standard802_11a   // Does not exist!
RFmxWlanMXStandard.Standard802_11g   // Does not exist!
```

✅ **CORRECT** — complete enum (verified from assembly v25.5):

| String | ✅ Correct Enum Value | Notes |
|---|---|---|
| "802.11a" | `Standard802_11ag` | a and g share one entry |
| "802.11b" | `Standard802_11b` | |
| "802.11g" | `Standard802_11ag` | same as 802.11a |
| "802.11j" | `Standard802_11j` | |
| "802.11p" | `Standard802_11p` | |
| "802.11n" | `Standard802_11n` | |
| "802.11ac" | `Standard802_11ac` | |
| "802.11ax" | `Standard802_11ax` | Wi-Fi 6 |
| "802.11be" | `Standard802_11be` | Wi-Fi 7 |
| "802.11bn" | `Standard802_11bn` | Wi-Fi 8 |

### 1. Factory Method Pattern (Not Constructor)

❌ **WRONG** (will not compile):
```csharp
var wlan = new RFmxWlanMX(instrSession, "");
var wlan = instrSession.GetWlanSignalConfiguration("");  // Extra parameter!
```

✅ **CORRECT** (Copy this exactly):
```csharp
RFmxInstrMX instrSession = new RFmxInstrMX("5842", "");
RFmxWlanMX wlan = instrSession.GetWlanSignalConfiguration();  // NO parameters!
```

**All RFmx personalities use factory methods**:
- `instrSession.GetWlanSignalConfiguration()` → RFmxWlanMX (no parameters!)
- `instrSession.GetLteSignalConfiguration()` → RFmxLTEMX
- `instrSession.GetNRSignalConfiguration()` → RFmxNRMX

### 2. Frequency Reference Configuration

✅ **CORRECT**:
```csharp
// Three parameters: selectorString (empty), source (empty for default), frequency
instrSession.ConfigureFrequencyReference("", "", 10e6);
```

### 3. IQPowerEdge Trigger (Not DigitalEdge)

❌ **WRONG**:
```csharp
wlan.Trigger.SelectDigitalEdgeTrigger(...);  // Property doesn't exist!
```

✅ **CORRECT**:
```csharp
wlan.ConfigureIQPowerEdgeTrigger("", "0", 
    RFmxWlanMXIQPowerEdgeTriggerSlope.Rising,
    -20.0,  // trigger level dB relative
    0.0,    // trigger delay  
    RFmxWlanMXTriggerMinimumQuietTimeMode.Auto,  // ✅ correct enum name
    5e-6,   // minimum quiet time
    RFmxWlanMXIQPowerEdgeTriggerLevelType.Relative,
    true);  // trigger enabled
```

**⚠️ Minimum Quiet Time Mode enum** (verified v26.3):
- ✅ `RFmxWlanMXTriggerMinimumQuietTimeMode.Auto` — correct
- ❌ `RFmxWlanMXIQPowerEdgeTriggerMinimumQuietTimeMode` — does NOT exist, compile error

### 4. Standard and Channel Bandwidth Configuration

❌ **WRONG** (missing bandwidth - #1 cause of bad EVM!):
```csharp
wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
wlan.ConfigureFrequency("", 2.412e9);
// Missing ConfigureChannelBandwidth!
// RFmx defaults to 20 MHz, but waveform might be 80 MHz → EVM will be terrible!
```

✅ **CORRECT** (bandwidth MUST match waveform):
```csharp
// Configure standard
wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);

// Configure channel bandwidth - MUST match waveform file!
// If waveform is RFIC_80211ax_80M_*.tdms → use 80e6
wlan.ConfigureChannelBandwidth("", 80e6);  // 80 MHz

// Then frequency
wlan.ConfigureFrequency("", 2.412e9);
```

**Critical Bandwidth Matching**:
```csharp
// Match waveform filename to bandwidth parameter (filenames vary by install — list first).
// 80211ax_20MHz.tdms       → ConfigureChannelBandwidth("", 20e6);
// 80211ax_80M_MCS11.tdms   → ConfigureChannelBandwidth("", 80e6);  // preferred for EVM
// 80211be_320M_MCS13_*.tdms → ConfigureChannelBandwidth("", 320e6);
```

**Impact**: RFmx defaults to **20 MHz** regardless of waveform. An 80 MHz waveform demodulated as 20 MHz gives **EVM > -20 dB** (terrible). With matching bandwidth: **-50 to -56 dB** (excellent).

### 6. Averaging Configuration

❌ **WRONG**:
```csharp
wlan.OfdmModAcc.Configuration.ConfigureAveragingEnabled("", RFmxWlanMXOfdmModAccAveragingEnabled.True);  // Missing count!
```

✅ **CORRECT**:
```csharp
// Three parameters: selectorString, enabled, count
wlan.OfdmModAcc.Configuration.ConfigureAveraging("", 
    RFmxWlanMXOfdmModAccAveragingEnabled.True, 
    10);  // averaging count
```

### 7. RFSG Script Generation — MUST Use NIRfsgPlayback

**CRITICAL**: When using `NIRfsgPlayback.ReadAndDownloadWaveformFromFile()` to load waveforms, you **MUST** also use `NIRfsgPlayback.SetScriptToGenerateSingleRfsg()` to load the script. Using the manual `Arb.Scripting.WriteScript()` API will produce a signal with **incorrect IQ rate, scaling, and metadata**, resulting in **bad EVM (+6 dB instead of -47 dB)**.

❌ **WRONG** (missing waveform metadata — causes bad EVM!):
```csharp
// DO NOT use manual Arb.Scripting when waveform was loaded via NIRfsgPlayback
rfsg.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;
rfsg.Arb.Scripting.WriteScript($"script myScript\r\ngenerate {waveformName}\r\nend script");
rfsg.Arb.Scripting.SelectedScriptName = "myScript";
rfsg.RF.PowerLevelType = RfsgRFPowerLevelType.PeakPower;
rfsg.Initiate();
// Result: EVM = +6.98 dB (TERRIBLE — signal is malformed)
```

✅ **CORRECT** (NIRfsgPlayback handles IQ rate, scaling, and script):
```csharp
// Load waveform
NIRfsgPlayback.ReadAndDownloadWaveformFromFile(rfsgHandle, waveformPath, waveformName);

// Build script
var sb = new StringBuilder();
sb.AppendLine("script wlanScript");
sb.AppendLine("repeat forever");
sb.Append("generate ").AppendLine(waveformName);
sb.AppendLine("end repeat");
sb.AppendLine("end script");

// Use NIRfsgPlayback to load the script (NOT Arb.Scripting.WriteScript)
NIRfsgPlayback.SetScriptToGenerateSingleRfsg(rfsgHandle, sb.ToString());
rfsg.Initiate();
// Result: EVM = -47.63 dB (EXCELLENT)
```

**Why**: `SetScriptToGenerateSingleRfsg` configures the RFSG IQ rate, bandwidth, PAPR, and runtime scaling from the waveform metadata. Manual `Arb.Scripting.WriteScript` does none of this → malformed signal → bad EVM.

### 8. RFmx Configuration Order — CRITICAL for Correct EVM and No Timeouts

**CRITICAL**: Two ordering rules both matter. Getting either wrong produces bad results or a `-380401` timeout.

#### Rule A — RFSG must `Initiate()` BEFORE `AutoLevel` (prevents -380401 timeout)

❌ **WRONG** (AutoLevel runs with no live signal → sets reference level from noise floor → IQPowerEdge trigger never fires → `-380401` timeout):
```csharp
// configure RFSG...
// configure RFmx...
wlan.AutoLevel("", 0.001);   // ❌ No signal present — measures noise, sets wrong ref level
wlan.Initiate("", "");       // ❌ Trigger armed at wrong threshold → TIMEOUT -380401
rfsg.Initiate();             // ❌ Signal starts AFTER RFmx already timed out
```

✅ **CORRECT** — RFSG first, then AutoLevel:
```csharp
rfsg.Initiate();             // ✅ Live signal is now present
wlan.AutoLevel("", 0.001);   // ✅ Sees real signal → correct reference level
wlan.Initiate("", "");       // ✅ Trigger fires immediately → measurement succeeds
```

#### Rule B — Standard/Bandwidth BEFORE AutoLevel (prevents bad EVM)

❌ **WRONG** (AutoLevel before standard/bandwidth, missing ExternalAttenuation):
```csharp
wlan.ConfigureFrequency("", freq);
wlan.AutoLevel("", 0.001);  // Too early! Standard/bandwidth not set yet
wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
wlan.ConfigureChannelBandwidth("", 80e6);
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.OfdmModAcc, true);
// Result: EVM = +6.98 dB (WRONG)
```

✅ **CORRECT** (complete ordering — copy this exactly):
```csharp
// 1. Configure RFmx: frequency, attenuation, trigger
wlan.ConfigureFrequency("", freq);
wlan.ConfigureExternalAttenuation("", 0.0);
wlan.ConfigureIQPowerEdgeTrigger("", "0", ...);

// 2. Standard and bandwidth (MUST be before AutoLevel)
wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
wlan.ConfigureChannelBandwidth("", 80e6);

// 3. Start RFSG — live signal MUST exist before AutoLevel
rfsg.Initiate();

// 4. AutoLevel — signal is live AND standard/bandwidth are set
wlan.AutoLevel("", 0.001);

// 5. Select measurements and configure per-measurement settings
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.OfdmModAcc, true);
wlan.OfdmModAcc.Configuration.ConfigureAveraging(...);
wlan.OfdmModAcc.Configuration.ConfigureAmplitudeTrackingEnabled(...);
wlan.OfdmModAcc.Configuration.ConfigurePhaseTrackingEnabled(...);
wlan.OfdmModAcc.Configuration.ConfigureChannelEstimationType(...);

// 6. Initiate RFmx
wlan.Initiate("", "");
// Result: EVM = -47.63 dB (EXCELLENT)
```

**Why AutoLevel needs a live signal**: it briefly acquires to set the ADC reference level. With no signal it locks onto noise → reference level ~40 dB too low → IQPowerEdge threshold computed from the wrong baseline → trigger never fires → `-380401` timeout.

### 9. Fetch Result Methods

❌ **WRONG**:
```csharp
wlan.OfdmModAcc.Results.FetchCompositeRmsEvmMean(...);  // Method doesn't exist!
wlan.OfdmModAcc.Results.FetchCompositeRmsEvm("", 10.0, out double compositeRmsEvm);  // Wrong parameter count!
```

✅ **CORRECT**:
```csharp
// FetchCompositeRmsEvm has THREE out parameters
wlan.OfdmModAcc.Results.FetchCompositeRmsEvm("", 10.0,
    out double compositeDataRmsEvmMean,
    out double compositePilotRmsEvmMean,
    out double compositeRmsEvm);  // This is the main value to use
```

### 9b. Enable Traces Before Fetching SEM Spectrum (Added 2026 — CRITICAL)

**Root cause**: RFmx disables trace storage by default for performance. Attempting to fetch spectrum/trace data throws `-380408`.

❌ **WRONG** (runtime crash):
```csharp
instrSession = new RFmxInstrMX(vstResource, "");
// ... configure and measure ...
Spectrum<float> semSpectrum = null;
Spectrum<float> compositeMask = null;
wlan.Sem.Results.FetchSpectrum("", 10.0, ref semSpectrum, ref compositeMask);
// ERROR: -380408: Cannot query traces when Enable All Traces is False
```

✅ **CORRECT** (enable traces immediately after session creation):
```csharp
instrSession = new RFmxInstrMX(vstResource, "");
instrSession.SetForceAllTracesEnabled("", true);  // MUST be before any Initiate()
// ... configure and measure ...
Spectrum<float> semSpectrum = null;
Spectrum<float> compositeMask = null;
wlan.Sem.Results.FetchSpectrum("", 10.0, ref semSpectrum, ref compositeMask);  // Works!

// Access spectrum data:
float[] data = semSpectrum.Samples.ToArray();
double startHz = semSpectrum.StartFrequency;
double stepHz = semSpectrum.FrequencyIncrement;
```

### 10. SEM Measurement API Corrections (verified v26.3)

#### SEM Averaging Type enum
❌ **WRONG** (does not exist — compile error):
```csharp
wlan.Sem.Configuration.ConfigureAveraging("", RFmxWlanMXSemAveragingEnabled.True, 5,
    RFmxWlanMXSemAveragingType.RmsAveraging);  // member does not exist
```
✅ **CORRECT** (valid enum members: `Rms`, `Log`, `Scalar`, `Maximum`, `Minimum`):
```csharp
wlan.Sem.Configuration.ConfigureAveraging("", RFmxWlanMXSemAveragingEnabled.True, 5,
    RFmxWlanMXSemAveragingType.Rms);  // ✅
```

#### SEM and Trace fetch methods use `ref`, not `out`

Several RFmx WLAN fetch methods take array or object parameters **by reference** (`ref`), not `out`. Passing them with `out` causes compile error `CS1620`.

| Method | Parameter | Keyword |
|---|---|---|
| `Txp.Results.FetchPowerTrace` | `power` (AnalogWaveform) | **`ref`** |
| `OfdmModAcc.Results.FetchDataConstellationTrace` | `dataConstellation` | **`ref`** |
| `Sem.Results.FetchSpectrum` | `spectrum`, `compositeMask` | **`ref`** |
| `Sem.Results.FetchLowerOffsetMarginArray` | all array params | **`ref`** |
| `Sem.Results.FetchUpperOffsetMarginArray` | all array params | **`ref`** |

✅ **CORRECT** pattern:
```csharp
// Trace fetches
AnalogWaveform<float> txpTrace = null!;
wlan.Txp.Results.FetchPowerTrace("", timeout, ref txpTrace);   // ref, not out

ComplexSingle[] constellation = null!;
wlan.OfdmModAcc.Results.FetchDataConstellationTrace("", timeout, ref constellation);

// SEM offset margin arrays — must be non-nullable T[], not T[]?
RFmxWlanMXSemLowerOffsetMeasurementStatus[] lowerStatus = null!;
double[] lowerMargin = null!, lowerMarginFreq = null!,
         lowerMarginAbsPower = null!, lowerMarginRelPower = null!;
wlan.Sem.Results.FetchLowerOffsetMarginArray("", timeout,
    ref lowerStatus, ref lowerMargin, ref lowerMarginFreq,
    ref lowerMarginAbsPower, ref lowerMarginRelPower);
```

**Note on array nullability**: `ref` parameters cannot accept nullable `T[]?` — declare as `T[]` with `null!` initializer.

#### AnalogWaveform sample interval
❌ **WRONG** (property not on waveform directly):
```csharp
double dt = txpTrace.SampleInterval.TotalSeconds;  // CS1061 — no such property
```
✅ **CORRECT** (interval is on the nested `Timing` object):
```csharp
double dt = txpTrace.Timing.SampleInterval.TotalSeconds;
```

#### TxP Configuration — correct method names and signatures
❌ **WRONG**:
```csharp
wlan.Txp.Configuration.ConfigureMeasurementInterval("", 1e-3);  // method does not exist
wlan.Txp.Configuration.ConfigureAveraging("", RFmxWlanMXTxpAveragingEnabled.True, 10,
    RFmxWlanMXTxpAveragingType.Rms);  // 4-param overload does not exist
```
✅ **CORRECT** (verified from DLL reflection):
```csharp
wlan.Txp.Configuration.ConfigureMaximumMeasurementInterval("", 1e-3);  // correct name
wlan.Txp.Configuration.ConfigureAveraging("", RFmxWlanMXTxpAveragingEnabled.True, 10);  // 3 params only
```

### 11. AutoLevel in Power Sweeps (CRITICAL)

❌ **WRONG** (causes EVM degradation at higher powers):
```csharp
// AutoLevel ONCE before loop
wlan.AutoLevel("", 0.001);

for (double power = -20; power <= -10; power++)
{
    rfsg.RF.Configure(frequency, power);
    wlan.Initiate("", "");  // Uses same reference level - clips at high power!
    // Fetch results...
}
```

**Problem**: Reference level optimized for -20 dBm. When power increases to -10 dBm (+10 dB stronger), the signal clips/compresses the ADC → **EVM degradation at higher powers**.

✅ **CORRECT**:
```csharp
// NO AutoLevel before loop

for (double power = -20; power <= -10; power++)
{
    rfsg.RF.Configure(frequency, power);

    // AutoLevel at EACH power point
    wlan.AutoLevel("", 0.001);  // Adjusts reference level to prevent clipping

    wlan.Initiate("", "");
    // Fetch results...
}
```

**Why**: each power level needs its own optimal reference level to maximize ADC dynamic range without clipping. Adds ~2-3 s/point but keeps EVM consistent (-53 to -56 dB) across the range.

---

## RFmx Property Naming, Parameters & EVM Units

> Factory method creation and the full personality list are covered in [§1 Factory Method Pattern](#1-factory-method-pattern-not-constructor). The corrections below are additional verified rules.

### Property Naming (camelCase, not PascalCase)

❌ **WRONG**:
```csharp
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.TxP, false);  // TxP
wlan.OFDMModAcc.Results.FetchCompositeRmsEvm(...);                   // OFDMModAcc
```

✅ **CORRECT**:
```csharp
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.Txp, false);  // Txp
wlan.OfdmModAcc.Results.FetchCompositeRmsEvm(...);                   // OfdmModAcc
```

### Method Parameters (out, not ref)

❌ **WRONG**:
```csharp
double avgPower = 0;
wlan.Txp.Results.FetchMeasurement("", 10.0, ref avgPower, ref peakPower);
```

✅ **CORRECT**:
```csharp
double avgPower = 0;
wlan.Txp.Results.FetchMeasurement("", 10.0, out avgPower, out peakPower);
```

### EVM Result Units (dB, not %)

**CRITICAL**: RFmx WLAN EVM results are returned in **dB**, not **%**.

✅ **CORRECT**:
```csharp
double rmsEvm, dataEvm, pilotEvm;
wlan.OfdmModAcc.Results.FetchCompositeRmsEvm("", 10.0, out rmsEvm, out dataEvm, out pilotEvm);
Console.WriteLine($"Composite RMS EVM: {rmsEvm:F2} dB");  // Note: dB, not %
```

**Understanding EVM in dB**: more negative = better (-53 dB excellent, -40 to -50 dB typical good). Conversion: EVM(dB) = 20·log₁₀(EVM(%)/100) — e.g. -40 dB ≈ 1%, -46 dB ≈ 0.5%, -53 dB ≈ 0.22%.

### OfdmModAcc Configuration for Optimal EVM

**CRITICAL**: For best EVM measurement accuracy, configure all tracking and estimation settings:

✅ **CORRECT** (Complete configuration):
```csharp
// Select measurements
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.OfdmModAcc, true);

// Configure averaging (10+ recommended)
wlan.OfdmModAcc.Configuration.ConfigureAveraging("", RFmxWlanMXOfdmModAccAveragingEnabled.True, 10);

// Frequency error estimation (use Preamble for accuracy)
wlan.OfdmModAcc.Configuration.ConfigureFrequencyErrorEstimationMethod("", RFmxWlanMXOfdmModAccFrequencyErrorEstimationMethod.Preamble);

// Amplitude tracking (compensates for amplitude variations)
wlan.OfdmModAcc.Configuration.ConfigureAmplitudeTrackingEnabled("", RFmxWlanMXOfdmModAccAmplitudeTrackingEnabled.True);

// Phase tracking (compensates for phase noise - can improve EVM by 1-3 dB)
wlan.OfdmModAcc.Configuration.ConfigurePhaseTrackingEnabled("", RFmxWlanMXOfdmModAccPhaseTrackingEnabled.True);

// Channel estimation (use ReferenceAndData for best accuracy)
wlan.OfdmModAcc.Configuration.ConfigureChannelEstimationType("", RFmxWlanMXOfdmModAccChannelEstimationType.ReferenceAndData);
```

**Impact**: missing PhaseTracking degrades EVM 1-3 dB; missing FrequencyErrorEstimation/ChannelEstimation/Averaging gives less accurate, noisier results. All settings → **-53 dB**; without phase tracking → **-50 dB**; minimal config → **-45 dB or worse**.

---

## Hardware Resource Names

### Use nisyscfg for Discovery

**Never hardcode** resource names like "PXI1Slot4". Discover actual hardware with nisyscfg:

```python
python ".agents\skills\nisyscfg-equipment-discovery\scripts\list_ni_test_equipment.py"
```

### Use Aliases, Not Slot Numbers

```csharp
string vstResource = "5842";       // ✅ alias from nisyscfg
// string vstResource = "PXI1Slot4"; // ❌ avoid — depends on NI-VISA aliases
```

---

## NI PXIe-5655 vs PXIe-5842 VST

### ❌ NEVER USE PXIe-5655 for Waveform Generation

The **NI PXIe-5655** is a CW-only vector signal generator: no arbitrary waveform mode, `rfsg.Arb.WriteWaveform()` fails, and it cannot generate modulated WLAN/LTE/5G signals.

```
ModularInstruments.NIRfsg: IVI: (Hex 0xBFFA0011) Function or method not supported.
Error code: -1074135023
```

### ✅ ALWAYS USE PXIe-5842/5841/5860 VST

The **PXIe-5842/5841/5860 VSTs** support full arbitrary waveforms, simultaneous TX (RFSG) and RX (RFmx), and WLAN/LTE/5G generation + measurement. The PXIe-5860 adds wider bandwidth and improved dynamic range.

**⚠️ PXIe-5860 has hardware-specific differences** — see [`references/pxie-5860-vst.md`](pxie-5860-vst.md) for:
- Physical channel must be in resource name (`"5860/0"`)
- LO Source properties not supported (skip all LO configuration)
- Complete initialization pattern

**Usage**:
```csharp
// Use same VST resource for both TX and RX
string vstResource = "5842";

NIRfsg rfsg = new NIRfsg(vstResource, false, false);        // TX side
RFmxInstrMX instrSession = new RFmxInstrMX(vstResource, ""); // RX side
```

---

## RFSG Script Naming Rules

### ⚠️ Clearing Waveforms — Use `rfsg.Arb.ClearAllWaveforms()` Not `ResetInstrument`

❌ **WRONG** (method does not exist — compile error):
```csharp
rfsg.Utility.ResetInstrument();  // RfsgDriverUtility has no ResetInstrument method
```

✅ **CORRECT**:
```csharp
rfsg.Arb.ClearAllWaveforms();    // Removes all previously downloaded waveforms
```

Alternatively, use the NIRfsgPlayback static method inside loops (see below).

### ⚠️ ClearAllWaveforms Before Re-Loading in Loops

**CRITICAL**: When loading waveforms inside a loop (sequencer, frequency sweep, etc.), you **MUST** call `NIRfsgPlayback.ClearAllWaveforms()` before each `ReadAndDownloadWaveformFromFile`. If you skip this, the second iteration throws:

```
NIRfsgPlayback: A waveform with the specified name already exists.
```

✅ **CORRECT — clear before load in every loop iteration**:
```csharp
IntPtr handle = rfsg.GetInstrumentHandle().DangerousGetHandle();

foreach (var point in sweepPoints)
{
    // Clear all previously loaded waveforms before loading the next one
    NIRfsgPlayback.ClearAllWaveforms(handle);

    NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle, point.WaveformPath, point.WaveformName);
    NIRfsgPlayback.SetScriptToGenerateSingleRfsg(handle, BuildScript(point.WaveformName));
    rfsg.Initiate();
    // ... measurements ...
    rfsg.Abort();
}
```

❌ **WRONG — no clear, crashes on second point**:
```csharp
foreach (var point in sweepPoints)
{
    // Missing ClearAllWaveforms — 2nd iteration throws duplicate name error!
    NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle, point.WaveformPath, point.WaveformName);
}
```

---

### ✅ Frequency Sweep Pattern — Named Signal Configurations (Added 2026)

> **⚠️ Do NOT use `AbortMeasurements("")` to reconfigure RFmx in a sweep loop.** On PXIe-5842/5860 it throws `-380413: Invalid Acquisition State Transition (Configuring → Configuring)` and corrupts the state machine. Use a fresh named signal configuration per point instead.

**The only reliable way to sweep frequencies on a PXIe-5842/5860 VST** is to create a fresh named signal configuration per frequency point.

**Key requirements:**
1. **Independent LOs** — PXIe-5842 has separate SG and SA local oscillators. Set both to `Onboard` so they can tune independently.
2. **Named signal configs** — `instrSession.GetWlanSignalConfiguration("freqN")` creates a fresh state machine per point without session overhead.
3. **Single `instrSession`** — shared across all points; only lightweight signal configs are created/disposed per iteration.
4. **Dispose previous config** — call `wlan?.Dispose()` before creating the next named config.

✅ **CORRECT — validated, working frequency sweep:**
```csharp
// === Initialize RFSG and load waveform (once) ===
NIRfsg rfsg = new NIRfsg(vstResource, true, false, "");
IntPtr rfsgHandle = rfsg.GetInstrumentHandle().DangerousGetHandle();
NIRfsgPlayback.ReadAndDownloadWaveformFromFile(rfsgHandle, waveformPath, waveformName);

// Build script (once)
string script = "script wlanScript\nrepeat forever\n" +
    $"generate {waveformName}\nend repeat\nend script";

// === Initialize RFmx — set independent LOs on PXIe-5842/5860 ===
RFmxInstrMX instrSession = new RFmxInstrMX(vstResource, "");
instrSession.SetAutomaticSGSASharedLO("", RFmxInstrMXAutomaticSGSASharedLO.Disabled);
instrSession.SetLOSource("", "Onboard");
rfsg.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;

// === Start RFSG at first frequency ===
rfsg.RF.Frequency = frequencies[0];
rfsg.RF.PowerLevel = outputPower;
NIRfsgPlayback.SetScriptToGenerateSingleRfsg(rfsgHandle, script);
rfsg.RF.OutputEnabled = true;
rfsg.Initiate();

// === Sweep frequencies ===
RFmxWlanMX wlan = null;
for (int i = 0; i < frequencies.Length; i++)
{
    double freq = frequencies[i];

    // Change RFSG frequency (2nd+ points)
    if (i > 0)
    {
        rfsg.Abort();
        rfsg.RF.Frequency = freq;
        NIRfsgPlayback.SetScriptToGenerateSingleRfsg(rfsgHandle, script);
        rfsg.Initiate();
    }

    // Fresh named signal config per point — avoids -380413 state machine error
    wlan?.Dispose();
    wlan = instrSession.GetWlanSignalConfiguration($"freq{i}");

    // Full configure for this frequency
    wlan.ConfigureFrequency("", freq);
    wlan.ConfigureExternalAttenuation("", 0.0);
    wlan.ConfigureIQPowerEdgeTrigger("", "0",
        RFmxWlanMXIQPowerEdgeTriggerSlope.Rising, -20.0, 0.0,
        RFmxWlanMXTriggerMinimumQuietTimeMode.Auto, 5e-6,
        RFmxWlanMXIQPowerEdgeTriggerLevelType.Relative, true);
    wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
    wlan.ConfigureChannelBandwidth("", 80e6);
    wlan.AutoLevel("", 0.100);

    wlan.SelectMeasurements("",
        RFmxWlanMXMeasurementTypes.Txp |
        RFmxWlanMXMeasurementTypes.OfdmModAcc |
        RFmxWlanMXMeasurementTypes.Sem,
        false);

    // Configure per-measurement settings...
    // ... TxP, OfdmModAcc, SEM averaging, etc.

    wlan.Initiate("", "");
    wlan.WaitForMeasurementComplete("", 10.0);

    // Fetch results
    double avgPow, peakPow;
    wlan.Txp.Results.FetchMeasurement("", 10.0, out avgPow, out peakPow);
    // ... fetch EVM, SEM ...
}

// Cleanup
wlan?.Dispose();
instrSession?.Close();
rfsg.Abort();
rfsg.RF.OutputEnabled = false;
rfsg.Close();
```

**Why this works:** each `GetWlanSignalConfiguration("freqN")` is an independent state machine (no `Configuring → Configuring` errors); the single shared `instrSession` means hardware init happens once (~7s saved/point); `Dispose()` releases each config cleanly.

**What does NOT work:** reusing one `wlan` with `AbortMeasurements("")` (or try-catch) → `-380413` / corrupted state; disposing/recreating `wlan` on the same session → `-380413` stale state; reopening `instrSession` per point → works but ~1-2s slower. **Named signal configs are the only fast, reliable option.**

### ⚠️ PXIe-5842 LO Configuration — Independent LOs Required for Sweeps

The PXIe-5842 has **separate SG and SA local oscillators**. For sweeps, set both to `Onboard` so they tune independently — otherwise they share an LO and the SA retunes with the SG, causing trigger timeouts or wrong measurements.

```csharp
instrSession.SetAutomaticSGSASharedLO("", RFmxInstrMXAutomaticSGSASharedLO.Disabled);
instrSession.SetLOSource("", "Onboard");                 // RFmx SA side
rfsg.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;  // RFSG SG side
```

**`RfsgLocalOscillatorSource`**: `Onboard` (recommended), `LOIn` (external), `SGSAShared`/`AutomaticSGSAShared` (default on VSTs — **break sweeps!**).

---

### ⚠️ SelectMeasurements Third Parameter MUST Be `false` — CRITICAL for EVM and Trigger (Added 2026)

**CRITICAL**: The third parameter of `SelectMeasurements` is `autoLevelIfEnabled`. **Always pass `false`.**

Passing `true` causes RFmx to re-run AutoLevel internally — and before doing so it **resets the signal configuration (standard, channel bandwidth, trigger) back to defaults**. This produces two cascading failures:

1. **Channel bandwidth reverts to 20 MHz** even though you configured 80 MHz → wrong subcarrier mapping → EVM = **+6 dB**
2. **IQPowerEdge trigger is disabled** → RFmx acquires an arbitrary slice of the continuously looping waveform → OfdmModAcc cannot align to the 802.11ax preamble → EVM = **+6 dB**

If you then disable the trigger to work around the resulting `-380401` timeout, free-run acquisition produces the **same +6 dB EVM** for the same preamble-alignment reason.

❌ **WRONG** (resets BW/standard/trigger → +6 dB EVM or -380401 timeout):
```csharp
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.OfdmModAcc | RFmxWlanMXMeasurementTypes.Txp | RFmxWlanMXMeasurementTypes.Sem, true);
```

✅ **CORRECT** (preserves all configuration already set):
```csharp
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.OfdmModAcc | RFmxWlanMXMeasurementTypes.Txp | RFmxWlanMXMeasurementTypes.Sem, false);
```

**Correct full sequence** (copy exactly — ordering and `false` both matter):
```csharp
// 1. Frequency, attenuation, trigger
wlan.ConfigureFrequency("", freqHz);
wlan.ConfigureExternalAttenuation("", 0.0);
wlan.ConfigureIQPowerEdgeTrigger("", "0",
    RFmxWlanMXIQPowerEdgeTriggerSlope.Rising, -20.0, 0.0,
    RFmxWlanMXTriggerMinimumQuietTimeMode.Auto, 5e-6,
    RFmxWlanMXIQPowerEdgeTriggerLevelType.Relative, true);  // trigger ON

// 2. Standard and bandwidth (before AutoLevel)
wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
wlan.ConfigureChannelBandwidth("", 80e6);

// 3. RFSG live signal, then AutoLevel (100 ms for stable average over multiple bursts)
rfsg.Initiate();
wlan.AutoLevel("", 0.100);

// 4. Select measurements — MUST pass false
wlan.SelectMeasurements("",
    RFmxWlanMXMeasurementTypes.OfdmModAcc |
    RFmxWlanMXMeasurementTypes.Txp         |
    RFmxWlanMXMeasurementTypes.Sem,
    false);  // ✅ preserves standard, BW, and trigger

// 5. Per-measurement config, then Initiate
wlan.Initiate("", "");
// Result: EVM = -52 dB (excellent)
```

**Symptom table**:
| Symptom | Cause |
|---|---|
| EVM = +6 dB | `SelectMeasurements(..., true)` reset BW/trigger, or trigger disabled |
| `-380401` timeout | Trigger enabled but `SelectMeasurements(..., true)` reset it after AutoLevel |
| EVM = -50 to -56 dB | Correct — trigger on, `false` passed |

---

### Waveform Names: No Underscores Allowed

❌ **WRONG** — `rfsg.Arb.WriteWaveform("wlan_waveform", ...)` and `generate wlan_waveform` in a script both fail:
```
ModularInstruments.NIRfsg: The script contains an invalid character or symbol.
Bad Value: _    Error code: -1074101561
```

✅ **CORRECT** — use `"wlanwaveform"` (no underscore) in both the download and the `generate` line.

**Rules**:
- Waveform and script names: alphanumeric only, no special characters
- **Waveform name MUST start with a letter** — filenames like `80211ax_80M_MCS11.tdms` start with a digit; prepend a prefix (e.g. `"wf"`) when auto-generating from filename
- Marker names: `marker0`, `marker1`, `marker2`, `marker3`

---

## RFmx IQPowerEdge Triggering

The **IQPowerEdge trigger** is recommended — it auto-detects signal presence and minimizes preamble loss. See §3 for the full `ConfigureIQPowerEdgeTrigger` signature. Key parameters:
- **Trigger level** `-20.0` dB relative → fires when signal is 20 dB below reference level
- **Minimum quiet time** `5e-6` (5 µs) ensures a clean burst start; Auto mode computes it automatically

### AutoLevel

Always call `AutoLevel` before measurements to optimize the reference level (no clipping, good SNR):

```csharp
wlan.AutoLevel("", 0.100);  // 100 ms interval
```

**⚠️ Use 100ms, not 1ms.** A 1ms interval may not capture enough of a bursty WLAN signal to set the reference level accurately; 100ms averages over multiple bursts.

---

## VST TX/RX Synchronization

### ✅ Simultaneous TX/RX Works on PXIe-5842 VST

The PXIe-5842 VST **can transmit and receive simultaneously** on the same resource when properly configured.

**⚠️ CRITICAL Session Ordering (Added 2026):** Create the RFmx session and configure frequency/trigger/standard/bandwidth **BEFORE** `rfsg.Initiate()`. Then start RFSG, then AutoLevel. This uses the same ordering as the [SelectMeasurements sequence](#-selectmeasurements-third-parameter-must-be-false--critical-for-evm-and-trigger-added-2026) above — just create both sessions on the same VST alias:

```csharp
string vstResource = "VST3_1";  // same alias for TX and RX
NIRfsg rfsg = new NIRfsg(vstResource, true, false, "");        // TX
RFmxInstrMX instrSession = new RFmxInstrMX(vstResource, "");   // RX
// ...configure RFmx (freq/trigger/standard/BW) → rfsg.Initiate() → AutoLevel → SelectMeasurements("", ..., false) → Initiate...
```

**Key requirements**: IQPowerEdge trigger to sync acquisition; AutoLevel for reference level; wait ~500 ms after TX start before RX; adequate signal path.

### Physical Configuration

- **RF loopback cable (recommended)**: SMA male-to-male + 20-30 dB attenuator (protects RX from high TX power)
- **Internal routing**: available on some VST versions — check driver docs

### Common Timeout Error — `-380401`

```
NationalInstruments.RFmx.WlanMX: -380401: Timed out while waiting for measurement results.
```

**Causes / fixes**: no valid preamble (use real NI waveform files); TX/RX not synced (use IQPowerEdge trigger); insufficient signal level (check cable/attenuator); wrong trigger config; missing 500 ms TX-start delay. AutoLevel after the live signal is present.

---

## GAC Assembly References

The complete, copy-exact `<ItemGroup>` of GAC assembly references (Ivi.Driver, NationalInstruments.Common, ModularInstruments.Common, NIRfsg.Fx40, NIRfsgPlayback.Fx40, RFmx.InstrMX.Fx40, RFmx.WlanMX.Fx40) lives in the canonical project template under [CRITICAL: .NET Framework Requirements](#critical-net-framework-requirements). Add other RFmx personalities (LTEMX, NRMX, BTMX, etc.) following the same `.Fx40` pattern.

**Critical**:
- `Private=False` is required for .NET Framework 4.8
- Paths are in `C:\Windows\Microsoft.NET\assembly\GAC_MSIL\`
- Version numbers in path must match installed NI software

---

## RFmx WLAN SEM (Spectrum Emission Mask)

### Configure SEM

```csharp
// Select SEM along with other measurements (single acquisition)
wlan.SelectMeasurements("",
    RFmxWlanMXMeasurementTypes.Txp |
    RFmxWlanMXMeasurementTypes.OfdmModAcc |
    RFmxWlanMXMeasurementTypes.Sem,
    true);

// ConfigureAveraging requires FOUR parameters — averagingType is mandatory
// ❌ WRONG (missing averagingType):
//   wlan.Sem.Configuration.ConfigureAveraging("", RFmxWlanMXSemAveragingEnabled.True, 10);
// ✅ CORRECT:
wlan.Sem.Configuration.ConfigureAveraging("",
    RFmxWlanMXSemAveragingEnabled.True,
    10,                              // averagingCount
    RFmxWlanMXSemAveragingType.Rms); // averagingType — required!

// Use Standard mask (matches 802.11 spec limits automatically)
wlan.Sem.Configuration.ConfigureMaskType("", RFmxWlanMXSemMaskType.Standard);

// Enable traces so FetchSpectrum returns data
wlan.Sem.Configuration.SetAllTracesEnabled("", true);
```

### Fetch SEM Results

**CRITICAL**: All SEM fetch arrays use `ref`, not `out`.

```csharp
// Overall pass/fail
wlan.Sem.Results.FetchMeasurementStatus("", 30.0,
    out RFmxWlanMXSemMeasurementStatus semStatus);
// semStatus == RFmxWlanMXSemMeasurementStatus.Pass or .Fail

// Spectrum + composite mask trace (ref parameters — not out!)
NationalInstruments.Spectrum<float> semSpectrum = null!, semMask = null!;
wlan.Sem.Results.FetchSpectrum("", 30.0, ref semSpectrum, ref semMask);

// Lower offset margins (ref arrays — not out!)
RFmxWlanMXSemLowerOffsetMeasurementStatus[] lowerStatus = null!;
double[] lowerMargin = null!, lowerMarginFreq = null!,
         lowerMarginAbsPower = null!, lowerMarginRelPower = null!;
wlan.Sem.Results.FetchLowerOffsetMarginArray("", 30.0,
    ref lowerStatus, ref lowerMargin,
    ref lowerMarginFreq, ref lowerMarginAbsPower, ref lowerMarginRelPower);

// Upper offset margins (ref arrays — not out!)
RFmxWlanMXSemUpperOffsetMeasurementStatus[] upperStatus = null!;
double[] upperMargin = null!, upperMarginFreq = null!,
         upperMarginAbsPower = null!, upperMarginRelPower = null!;
wlan.Sem.Results.FetchUpperOffsetMarginArray("", 30.0,
    ref upperStatus, ref upperMargin,
    ref upperMarginFreq, ref upperMarginAbsPower, ref upperMarginRelPower);
```

### Reading Spectrum<float> Data for Charting

`FetchSpectrum` returns `NationalInstruments.Spectrum<float>` objects. Use these properties to iterate:

```csharp
// ❌ WRONG — these properties do not exist on Spectrum<float>:
//   spectrum.RelativeInitialX  (does not exist)
//   spectrum.RelativeDeltaX    (does not exist)
//   spectrum.Samples.Length    (Buffer<T> has no Length)

// ✅ CORRECT:
double startFreqHz  = semSpectrum.StartFrequency;   // absolute start frequency (Hz)
double freqStepHz   = semSpectrum.FrequencyIncrement;
int    count        = semSpectrum.SampleCount;
float[] data        = semSpectrum.Samples.ToArray(); // Buffer<T>.ToArray()

for (int i = 0; i < data.Length; i++)
{
    double offsetMHz = (startFreqHz + i * freqStepHz - centerFreqHz) / 1e6;
    chart.Series["PSD"].Points.AddXY(offsetMHz, data[i]);
}
```

**`Spectrum<float>` properties** (verified from `NationalInstruments.Common` v19.1):

| Property | Type | Description |
|---|---|---|
| `StartFrequency` | `double` | Absolute start frequency in Hz |
| `FrequencyIncrement` | `double` | Hz per sample |
| `SampleCount` | `int` | Number of samples |
| `Samples` | `Buffer<float>` | Sample data — call `.ToArray()` to get `float[]` |

**`Buffer<T>` access** (use `ToArray()` or indexer, NOT `.Length`):

```csharp
float[] arr = buffer.ToArray();  // ✅
int n = buffer.Size;             // ✅ (not .Length)
float v = buffer[i];             // ✅ indexer works too
```

---

### SEM Spectrum Trace in GUI — MANDATORY When SEM Is Measured (Added 2026)

**⚠️ RULE**: When SEM is measured in a GUI, **always** include a spectrum trace chart showing PSD + composite mask — margin numbers alone are insufficient. In frequency sweeps, **overlay** one PSD series per frequency (never clear/replace per point) so channels can be compared.

**Requirements**:
1. **Overlaid PSD traces**, all centered at **0 Hz offset (MHz)** on the X-axis — NOT absolute frequency
2. **Single shared mask** — same shape per standard/bandwidth, so draw it once (first point only)
3. **Enable traces** — `instrSession.SetForceAllTracesEnabled("", true)` before any `Initiate()`, or `FetchSpectrum` throws `-380408`
4. **Downsample** to ~800 points and **color-code per channel**
5. **Tabbed bottom panel** — put results grid + log in a `TabControl` so they share space instead of clipping charts (generic WinForms layout — see `ni-measurement-gui-winforms`)

**✅ CORRECT pattern** (per frequency point — fetch with `ref`, offset-center, downsample, add a new series):
```csharp
instrSession.SetForceAllTracesEnabled("", true);  // once, before the loop

Spectrum<float> semSpectrum = null!, compositeMask = null!;
wlan.Sem.Results.FetchSpectrum("", 10.0, ref semSpectrum, ref compositeMask);  // ref, not out!

double startHz = semSpectrum.StartFrequency, stepHz = semSpectrum.FrequencyIncrement, centerHz = freq;
float[] specData = semSpectrum.Samples.ToArray();
int step = Math.Max(1, specData.Length / 800);  // downsample

Invoke(new Action(() =>
{
    // Draw mask once (first point); then add one PSD series per channel, centered at 0 Hz:
    var psd = new Series(channelLabel) { ChartType = SeriesChartType.Line, Color = traceColors[si % traceColors.Length], IsVisibleInLegend = false };
    for (int p = 0; p < specData.Length; p += step)
        psd.Points.AddXY((startHz + p * stepHz - centerHz) / 1e6, specData[p]);  // offset MHz
    chartSemTrace.Series.Add(psd);
}));
```

**❌ Common mistakes**: clearing the trace each point (loses history); absolute frequency on X (traces don't overlap); stacking grid+log+status vertically (clips charts — use `TabControl`); missing `SetForceAllTracesEnabled` (`-380408` at runtime).

> **GUI layout details** (panel docking order, `TabControl`, themes, charting) live in the dedicated `ni-measurement-gui-winforms` skill. The one RF-critical rule: add the Fill chart panel to the form **before** the Left config panel (WinForms docks in reverse-add order, else charts clip on the left).

---

## Summary of Critical Lessons

| Issue | Wrong Approach | Correct Approach |
|-------|---------------|------------------|
| .NET Version | .NET 8.0 | **.NET Framework 4.8** |
| RFmx Creation | `new RFmxWlanMX()` | **Factory method pattern** |
| **Channel Bandwidth** | Missing `ConfigureChannelBandwidth` | **MUST match waveform (20/40/80/160 MHz)** |
| Waveforms | Generate in code | **Load from RFIC Test Software folder** |
| Waveform filenames | Assume `RFIC_` prefix | **List actual files first — prefix varies by NI version** |
| Hardware | Use PXIe-5655 | **Use PXIe-5842/5841 VST for TX/RX** |
| Resource Names | `"PXI1Slot4"` | **Use nisyscfg aliases** (`"5841"`) |
| Script Names | `wlan_waveform` | **No underscores, alphanumeric only, must start with a letter** — prepend `"wf"` when deriving from filenames like `80211ax_80M_MCS11` |
| **Script Loading** | `Arb.Scripting.WriteScript()` | **`NIRfsgPlayback.SetScriptToGenerateSingleRfsg()`** (preserves IQ rate/scaling) |
| **RFmx Config Order** | AutoLevel before Standard/Bandwidth | **Standard → Bandwidth → AutoLevel → SelectMeasurements → configure** |
| **External Attenuation** | Missing `ConfigureExternalAttenuation` | **Always call `ConfigureExternalAttenuation("", 0.0)`** |
| Property Names | `TxP`, `OFDMModAcc` | **camelCase** (`Txp`, `OfdmModAcc`) |
| Scalar fetch params | `ref` | **`out`** (e.g. `FetchMeasurementStatus`, `FetchCompositeRmsEvm`) |
| **SEM array fetch params** | `out` | **`ref`** (`FetchSpectrum`, `FetchLowerOffsetMarginArray`, `FetchUpperOffsetMarginArray`) |
| **SEM `ConfigureAveraging`** | 3 params | **4 params** — `averagingType` (`RFmxWlanMXSemAveragingType`) is required |
| **`Spectrum<float>` iteration** | `.RelativeInitialX`, `.RelativeDeltaX` | **`.StartFrequency`, `.FrequencyIncrement`, `.SampleCount`, `.Samples.ToArray()`** |
| **`Buffer<T>` size** | `.Length` | **`.Size`** or `.ToArray().Length` |
| **`RFmxWlanMXStandard` 802.11a/g** | `Standard802_11a`, `Standard802_11g` | **`Standard802_11ag`** (they share one enum) |
| SEM traces for charting | Missing `SetAllTracesEnabled` | **Call `wlan.Sem.Configuration.SetAllTracesEnabled("", true)`** before initiate |
| **WinForms docking order** | Add Fill before Bottom/Top | **Add Bottom-docked controls first, then Top, then Fill last** — otherwise `Chart` gets 0 height and crashes |
| **WinForms Left+Fill panel order** | `Controls.Add(panelLeft); Controls.Add(panelRight)` | **Add `panelRight` (Fill) FIRST, then `panelLeft` (Left) SECOND** — WinForms docks in reverse-add order; if Left is added first, the Fill panel renders behind it and charts get clipped on the left side |
| **WinForms chart type** | `SeriesChartType.Column` for sweep results | **Use `SeriesChartType.Line` with `BorderWidth = 2` and `MarkerStyle.Circle`/`MarkerSize = 6`** — line charts are preferred for frequency sweep plots |
| **WinForms freq sweep selection** | Hardcoded frequency list with no user choice | **Use checkboxes for each sweep point** with Select All / Select None buttons — let users pick which channels to measure |
| **`NumericUpDown` Value in initializer** | `new NumericUpDown { Value = -10m, Minimum = -60m }` | **Set `Minimum`/`Maximum` on separate lines BEFORE `Value`** — object initializer order is unspecified; default bounds are 0–100, so negative values crash immediately |
| **`SplitContainer.SplitterDistance` at construction** | `new SplitContainer { SplitterDistance = 400 }` | **Never set `SplitterDistance` at construction time** — control size is 0 before layout; use `TableLayoutPanel` with `SizeType.Percent` instead |
| **Session cleanup** | `rfsg.Abort(); rfsg.Close(); instrSession.Close()` | **`rfsg.Dispose(); instrSession.Dispose(); wlan.Dispose()`** — `Dispose()` handles abort+close in the correct order; calling `Abort()` before `Close()` on an already-stopped session causes a driver state error |
| **Fetching into result object** | `FetchMeasurement("", 30.0, out result.MyProp, ...)` | **Use local variables then assign**: `FetchMeasurement("", 30.0, out double v1, out double v2); result.Prop1 = v1;` — C# auto-properties cannot be passed as `out`/`ref` (CS0206) |
| **Console app exit** | No `Console.ReadKey()` | **Always end console apps with `Console.ReadKey()`** after the `finally` block so the window stays open; omitting it causes the console to close immediately after cleanup |
| **SEM trace in GUI** | Show only margin numbers, or replace trace each point | **ALWAYS add overlaid PSD traces (one per frequency, centered at 0 Hz offset) + single shared mask** — use `FetchSpectrum` with `ref`, downsample to ~800 pts, color-code per channel. Use `TabControl` for grid+log to avoid clipping charts |

---

## Quick Reference: Working Example

**Complete 802.11ax WLAN EVM Measurement** (Tested & Verified):

```csharp
using System;
using System.Text;
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.NIRfsgPlayback;
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.WlanMX;

// .NET Framework 4.8 project
string vstResource = "5842";  // From nisyscfg
string waveformPath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\80211ax_80M_MCS11.tdms";
string waveformName = "wlan80211ax";  // No underscores!

// === RFSG: Signal Generation ===
NIRfsg rfsg = new NIRfsg(vstResource, true, false, "");
IntPtr rfsgHandle = rfsg.GetInstrumentHandle().DangerousGetHandle();

// Load waveform using NIRfsgPlayback
NIRfsgPlayback.ReadAndDownloadWaveformFromFile(rfsgHandle, waveformPath, waveformName);

// Configure RFSG
rfsg.RF.Configure(2.412e9, -10.0);  // 2.412 GHz, -10 dBm
rfsg.FrequencyReference.Configure(RfsgFrequencyReferenceSource.OnboardClock, 10e6);

// Create and load script
var sb = new StringBuilder();
sb.AppendLine("script wlanScript");
sb.AppendLine("repeat forever");
sb.Append("generate ").AppendLine(waveformName);
sb.AppendLine("end repeat");
sb.AppendLine("end script");

NIRfsgPlayback.SetScriptToGenerateSingleRfsg(rfsgHandle, sb.ToString());
rfsg.Initiate();

// === RFmx: Measurement ===
RFmxInstrMX instrSession = new RFmxInstrMX(vstResource, "");
RFmxWlanMX wlan = instrSession.GetWlanSignalConfiguration();  // Factory method

// Configure frequency and trigger
instrSession.ConfigureFrequencyReference("", "", 10e6);
wlan.ConfigureFrequency("", 2.412e9);
wlan.ConfigureExternalAttenuation("", 0.0);
wlan.ConfigureIQPowerEdgeTrigger("", "0", RFmxWlanMXIQPowerEdgeTriggerSlope.Rising, 
    -20.0, 0.0, 0, 5e-6, RFmxWlanMXIQPowerEdgeTriggerLevelType.Relative, true);

// Configure standard
wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
wlan.ConfigureChannelBandwidth("", 80e6);

// Auto-level and select measurements
wlan.AutoLevel("", 0.001);
wlan.SelectMeasurements("", RFmxWlanMXMeasurementTypes.Txp | RFmxWlanMXMeasurementTypes.OfdmModAcc, true);

// Configure measurements
wlan.Txp.Configuration.ConfigureAveraging("", RFmxWlanMXTxpAveragingEnabled.True, 10);
wlan.OfdmModAcc.Configuration.ConfigureAveraging("", RFmxWlanMXOfdmModAccAveragingEnabled.True, 10);
wlan.OfdmModAcc.Configuration.ConfigureAmplitudeTrackingEnabled("", RFmxWlanMXOfdmModAccAmplitudeTrackingEnabled.True);

// Measure
wlan.Initiate("", "");

// Fetch results
double avgPower, peakPower;
wlan.Txp.Results.FetchMeasurement("", 30.0, out avgPower, out peakPower);  // out not ref

double rmsEvm, dataEvm, pilotEvm;
wlan.OfdmModAcc.Results.FetchCompositeRmsEvm("", 30.0, out rmsEvm, out dataEvm, out pilotEvm);

Console.WriteLine($"Average Power: {avgPower:F2} dBm");
Console.WriteLine($"Composite RMS EVM: {rmsEvm:F3} dB");

// Cleanup — use Dispose() on all sessions; never call Abort()+Close() separately
wlan.Dispose();
instrSession.Dispose();
rfsg.Dispose();

// Keep console open until user dismisses
Console.WriteLine("\nPress any key to exit...");
Console.ReadKey();
```

**Expected Results** (on PXIe-5842 VST):
- Average Power: ~-10.36 dBm
- Composite RMS EVM: ~-53.5 dB (excellent signal quality - more negative is better)
- Measurement time: ~15-20 seconds

---

## Optional Architecture Patterns

For larger parametric test frameworks, three optional patterns help organize WLAN testing. Full reference implementations were removed to keep this guide focused — the core ideas:

- **TestPoint** — an immutable value object holding one measurement's parameters (band, center frequency, standard, bandwidth, waveform path) with a computed `MatrixKey` (e.g., `2.4GHz_802.11ax_80MHz`) for catalog lookup. Build a `List<TestPoint>` to drive parametric sweeps and test matrices.
- **Waveform Catalog** — a JSON map of `MatrixKey` → TDMS file path, loaded at runtime so waveform locations live in config (lab vs production) rather than hardcoded in source.
- **Modular Measurement** — static modules (EVM-only, Txp-only, EVM+Txp composite) that each follow configure → initiate → fetch. Prefer the composite module: selecting `Txp | OfdmModAcc` in a single acquisition measures both in ~15 s versus ~23 s for two separate acquisitions.

For concrete implementations, see the **Frequency Sweep Pattern** and **Quick Reference: Working Example** sections above.

---

## WinForms GUI Development

For WLAN measurement GUIs, **use the dedicated `ni-measurement-gui-winforms` skill** for all generic WinForms concerns — runtime-safety rules (set `NumericUpDown` `Minimum`/`Maximum` before `Value`; never set `SplitContainer.SplitterDistance` at construction; add `DockStyle.Fill` controls last), `TableLayoutPanel` layout, dark theme, charting, and results grids.

This guide adds only the **RF-specific GUI essentials**:

1. **Project**: same NI GAC references as the console template, plus `<OutputType>WinExe</OutputType>`, `<UseWindowsForms>true</UseWindowsForms>`, and a `System.Windows.Forms.DataVisualization` reference for charts.
2. **Async**: run the measurement on a background thread (`await Task.Run(...)`), disable the Run button during the run, and marshal log/result updates back to the UI thread via `InvokeRequired`/`BeginInvoke`.
3. **Bandwidth-mismatch validation** (prevents the #1 EVM mistake) plus the standard/bandwidth parsing helpers:

```csharp
// Validate waveform bandwidth (from filename) matches the selected channel bandwidth
string waveformBw = ExtractBandwidthFromFilename(txtWaveformFile.Text);  // e.g. "80"
string selectedBw = cmbBandwidth.SelectedItem.ToString();
if (waveformBw != null && waveformBw != selectedBw &&
    MessageBox.Show($"Waveform is {waveformBw} MHz but {selectedBw} MHz is selected.\nThis causes bad EVM! Continue?",
        "Bandwidth Mismatch", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.No)
    return;

// Apply settings read from controls (SelectMeasurements MUST pass false — see RFmx section)
wlan.ConfigureStandard("", GetStandardEnum(cmbStandard.SelectedItem.ToString()));
wlan.ConfigureChannelBandwidth("", double.Parse(selectedBw) * 1e6);
wlan.SelectMeasurements("", measurements, false);  // false preserves standard/BW/trigger

RFmxWlanMXStandard GetStandardEnum(string s) => s switch
{
    "802.11a" or "802.11g" => RFmxWlanMXStandard.Standard802_11ag,  // a and g share one enum
    "802.11b"  => RFmxWlanMXStandard.Standard802_11b,
    "802.11n"  => RFmxWlanMXStandard.Standard802_11n,
    "802.11ac" => RFmxWlanMXStandard.Standard802_11ac,
    "802.11be" => RFmxWlanMXStandard.Standard802_11be,
    _          => RFmxWlanMXStandard.Standard802_11ax
};

string? ExtractBandwidthFromFilename(string filename)  // "..._80M_..." -> "80"
    => System.Text.RegularExpressions.Regex.Match(filename, @"_(\d+)M_") is { Success: true } m ? m.Groups[1].Value : null;
```

> When SEM is measured, also add the spectrum-trace chart — see [SEM Spectrum Trace in GUI](#sem-spectrum-trace-in-gui--mandatory-when-sem-is-measured-added-2026) above.

> **Generic WinForms patterns** (async measurement threading, `InvokeRequired`/`BeginInvoke`, dark UI theme, `DataGridView`/`Chart` results, reverse-add docking order, input validation, file browsing, progress/status) are documented once in the canonical GUI skill — see [`ni-measurement-gui-winforms`](../../ni-measurement-gui-winforms/SKILL.md) and [`rf-test-gui-patterns.md`](../../ni-measurement-gui-winforms/references/rf-test-gui-patterns.md). Do not duplicate them here.

---

## References

- Hardware discovery: `.agents/skills/nisyscfg-equipment-discovery`
- RFmx workflows: `.agents/skills/ni-hw-drivers-csharp/references/rfmx-generation-measurement-workflows.md`
- RFSG/RFSA API: `.agents/skills/ni-hw-drivers-csharp/references/rfsa-rfsg-csharp.md`
- GUI patterns: `.agents/skills/ni-measurement-gui-winforms/SKILL.md`

