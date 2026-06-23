# NI-TClk Synchronization Guide - C# (.NET Framework 4.8)

**Purpose**: Complete guide for synchronizing multiple NI modular instruments
(especially PXIe-5841/5842 VSTs) for phase coherent signal generation. Enables
**"one-prompt synchronization"** - generate complete, working multi-VST code
from a single request.

**Based on**: Real-world testing with two PXIe-5841 VSTs, validated phase
coherent generation with LO daisy-chaining, LO frequency propagation, and TClk.

---

## Quick Start: Phase Coherent Dual-VST Generation

This guide enables you to generate complete working code from prompts like:

- _"Generate phase coherent signals from 2 PXIe-5841 VSTs"_
- _"Synchronize two VSTs with TClk and shared LO"_
- _"Add a 90 degree phase offset between two synchronized generators"_
- _"Calibrate RF paths for phase coherent signals at the DUT"_

---

## Configuration Order - CRITICAL

The order of configuration matters. Follow this exact sequence:

```
1. Create all RFSG sessions
2. Configure reference clocks (PxiClock on all)
3. Configure LO daisy chain (first = Onboard + LOOut, rest = LOIn)
4. Configure RF parameters on the LO-source VST first (frequency, power)
5. Read LO frequency from source VST, set on all receiving VSTs
6. Configure RF parameters on remaining VSTs
7. Load waveforms on all sessions (NIRfsgPlayback)
8. Disable automatic SG/SA shared LO on all sessions
9. Set scripts on all sessions
10. Apply phase offsets (RF.PhaseOffset)
11. Apply time delays (DeviceEvents.SampleClockDelay)
12. Create NITClk with all sessions
13. ConfigureForHomogeneousTriggers()
14. Synchronize()
15. Initiate()  <- TClk starts all sessions simultaneously
```

**WARNING: Do NOT call `rfsg.Initiate()` on individual sessions** - TClk manages
initiation for all synchronized sessions via `tclk.Initiate()`.

---

## Assembly Reference

Add to your `.csproj` alongside the standard NI RFSG references:

```xml
<Reference Include="NationalInstruments.ModularInstruments.NITClk.Fx40">
  <HintPath>C:\Program Files (x86)\National Instruments\MeasurementStudioVS2010\DotNET\Assemblies\Current\NationalInstruments.ModularInstruments.NITClk.Fx40.dll</HintPath>
</Reference>
```

**Using directive**:
```csharp
using NationalInstruments.ModularInstruments.NITClk;
```

---

## Step 1: Reference Clock Sharing

All instruments must derive timing from the same reference clock. On a PXI
chassis, the 10 MHz backplane clock is shared automatically.

```csharp
// Both VSTs use the PXI backplane 10 MHz reference clock
rfsg1.FrequencyReference.Source = RfsgFrequencyReferenceSource.PxiClock;
rfsg1.FrequencyReference.Frequency = 10e6;
rfsg2.FrequencyReference.Source = RfsgFrequencyReferenceSource.PxiClock;
rfsg2.FrequencyReference.Frequency = 10e6;
```

**Why**: Without a shared reference clock, each VST's internal oscillator drifts
independently, making phase coherence impossible.

### Available Reference Clock Sources

| Source | Enum Value | Use Case |
|---|---|---|
| PXI backplane 10 MHz | `RfsgFrequencyReferenceSource.PxiClock` | Standard PXI chassis (most common) |
| Onboard oscillator | `RfsgFrequencyReferenceSource.OnboardClock` | Single instrument, no sync needed |
| External 10 MHz | `RfsgFrequencyReferenceSource.RefIn` | External reference from signal source |

---

## Step 2: LO Daisy Chain

For phase coherence, all VSTs must use the same Local Oscillator. The PXIe-5841
supports LO In/Out ports for daisy-chaining.

```csharp
// VST1: Use onboard LO and export it
rfsg1.RF.LocalOscillator.LOOutEnabled = true;
rfsg1.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;

// VST2: Receive LO from VST1
rfsg2.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.LOIn;
```

**CRITICAL: LO Frequency Configuration**

After configuring RF parameters on the LO-source VST, you **must** read its
actual LO frequency and set it on all receiving VSTs. Without this, the
receiving VST does not know the incoming LO frequency and will misconfigure
its mixer/IF chain.

```csharp
// Configure RF on VST1 first (this determines the LO frequency)
rfsg1.RF.Configure(centerFrequency, rfsgPower);

// Read actual LO frequency from VST1 and set on VST2
double loFrequency = rfsg1.RF.LocalOscillator.Frequency;
rfsg2.RF.LocalOscillator.Frequency = loFrequency;

// Now configure RF on VST2
rfsg2.RF.Configure(centerFrequency, rfsgPower);
```

### Daisy-Chaining 3+ VSTs

For more than 2 VSTs, the first exports LO and all subsequent VSTs receive:

```csharp
// VST1: LO source
rfsg1.RF.LocalOscillator.LOOutEnabled = true;
rfsg1.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;

// VST2: Receive LO, pass through to VST3
rfsg2.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.LOIn;
rfsg2.RF.LocalOscillator.LOOutEnabled = true;  // pass-through

// VST3: Receive LO from VST2
rfsg3.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.LOIn;

// Configure RF on VST1 first, then propagate LO frequency
rfsg1.RF.Configure(centerFrequency, rfsgPower);
double loFrequency = rfsg1.RF.LocalOscillator.Frequency;
rfsg2.RF.LocalOscillator.Frequency = loFrequency;
rfsg3.RF.LocalOscillator.Frequency = loFrequency;
rfsg2.RF.Configure(centerFrequency, rfsgPower);
rfsg3.RF.Configure(centerFrequency, rfsgPower);
```

**CRITICAL**: You must also disable automatic SG/SA shared LO on all
sessions when manually configuring LO sharing:

```csharp
NIRfsgPlayback.StoreAutomaticSGSASharedLO(rfsgHandle, "", RfsgPlaybackAutomaticSGSASharedLO.Disabled);
```

---

## Step 3: NI-TClk Synchronization

TClk aligns the sample clocks and triggers of all sessions so they start at
exactly the same time.

```csharp
// Create TClk with all RFSG sessions
NITClk tclk = new NITClk(new ITClkSessionReference[] { rfsg1, rfsg2 });

// Configure triggers - use homogeneous when all instruments are the same type
tclk.ConfigureForHomogeneousTriggers();

// Synchronize sample clocks across all sessions
tclk.Synchronize();

// Start all sessions simultaneously
tclk.Initiate();
```

### API Corrections - Common Hallucinations

| Wrong (hallucinated) | Correct |
|---|---|
| `NITClk.Synchronize(sessions)` (static) | `tclk.Synchronize()` (instance method) |
| `NITClk.Initiate(sessions)` (static) | `tclk.Initiate()` (instance method) |
| `rfsg.Initiate()` after TClk setup | `tclk.Initiate()` only - do NOT initiate individual sessions |
| `new NITClk(rfsg1, rfsg2)` | `new NITClk(new ITClkSessionReference[] { rfsg1, rfsg2 })` |
| Skipping LO frequency on receiving VST | Read `rfsg1.RF.LocalOscillator.Frequency` after `RF.Configure()`, set on rfsg2 before its `RF.Configure()` |

---

## Step 4: Phase Offset (Optional)

Apply a carrier phase offset to any VST relative to the reference (first VST).
The offset is in **degrees**.

```csharp
// VST1 at 0 deg, VST2 at 90 deg relative phase
rfsg1.RF.PhaseOffset = 0.0;
rfsg2.RF.PhaseOffset = 90.0;  // degrees
```

**Notes**:
- Set phase offset **before** `tclk.Synchronize()`
- Valid range: any double value (wraps modulo 360 deg)
- Phase relationship is maintained as long as LO is shared and TClk is active

---

## Step 5: Time Delay (Optional)

Apply a time delay to a VST's sample clock, shifting its waveform playback
in time relative to other synchronized sessions.

```csharp
// Delay VST2 by 10 nanoseconds relative to VST1
rfsg2.DeviceEvents.SampleClockDelay = 10e-9;  // seconds
```

**Notes**:
- Set time delay **before** `tclk.Synchronize()`
- Resolution depends on sample clock rate
- Useful for beamforming or simulating propagation delay

---

## Complete Working Example: Phase Coherent Dual-VST Generation

```csharp
using System;
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.NIRfsgPlayback;
using NationalInstruments.ModularInstruments.NITClk;

namespace PhaseCoherentGeneration
{
    class Program
    {
        static void Main(string[] args)
        {
            string vstResource1 = "5841_1";
            string vstResource2 = "5841_2";
            double centerFrequency = 5.18e9;
            double rfsgPower = -10.0;
            double phaseOffsetDegrees = 90.0;
            double timeDelaySeconds = 0.0;
            string waveformPath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\80211ax_80MHz.tdms";
            string waveformName = "wlan80211ax80M";

            NIRfsg rfsg1 = null;
            NIRfsg rfsg2 = null;

            try
            {
                // 1. Create sessions
                rfsg1 = new NIRfsg(vstResource1, true, false);
                rfsg2 = new NIRfsg(vstResource2, true, false);

                // 2. Reference clock sharing (PXI backplane 10 MHz)
                rfsg1.FrequencyReference.Source = RfsgFrequencyReferenceSource.PxiClock;
                rfsg1.FrequencyReference.Frequency = 10e6;
                rfsg2.FrequencyReference.Source = RfsgFrequencyReferenceSource.PxiClock;
                rfsg2.FrequencyReference.Frequency = 10e6;

                // 3. LO daisy chain - VST1 exports, VST2 receives
                rfsg1.RF.LocalOscillator.LOOutEnabled = true;
                rfsg1.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;
                rfsg2.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.LOIn;

                // 4. Configure RF parameters (VST1 first to determine LO frequency)
                rfsg1.RF.Configure(centerFrequency, rfsgPower);
                rfsg1.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;

                // 5. Read LO frequency from VST1 and set on VST2
                double loFrequency = rfsg1.RF.LocalOscillator.Frequency;
                rfsg2.RF.LocalOscillator.Frequency = loFrequency;

                rfsg2.RF.Configure(centerFrequency, rfsgPower);
                rfsg2.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;

                // 6. Load waveform on both
                IntPtr handle1 = rfsg1.GetInstrumentHandle().DangerousGetHandle();
                IntPtr handle2 = rfsg2.GetInstrumentHandle().DangerousGetHandle();
                NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle1, waveformPath, waveformName);
                NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle2, waveformPath, waveformName);

                // 7. Disable automatic SG/SA shared LO
                NIRfsgPlayback.StoreAutomaticSGSASharedLO(handle1, "", RfsgPlaybackAutomaticSGSASharedLO.Disabled);
                NIRfsgPlayback.StoreAutomaticSGSASharedLO(handle2, "", RfsgPlaybackAutomaticSGSASharedLO.Disabled);

                // 8. Set scripts
                string script = $"script GenerateWaveform\n  repeat forever\n    generate {waveformName}\n  end repeat\nend script";
                NIRfsgPlayback.SetScriptToGenerateSingleRfsg(handle1, script);
                NIRfsgPlayback.SetScriptToGenerateSingleRfsg(handle2, script);
                rfsg1.Arb.Scripting.SelectedScriptName = "GenerateWaveform";
                rfsg2.Arb.Scripting.SelectedScriptName = "GenerateWaveform";

                // Adjust power for PAPR
                double papr;
                NIRfsgPlayback.RetrieveWaveformPapr(handle1, waveformName, out papr);
                rfsg1.RF.PowerLevel = rfsgPower - papr;
                rfsg2.RF.PowerLevel = rfsgPower - papr;

                // 9. Phase offset (VST2 relative to VST1)
                rfsg1.RF.PhaseOffset = 0.0;
                rfsg2.RF.PhaseOffset = phaseOffsetDegrees;

                // 10. Time delay (VST2 relative to VST1)
                rfsg2.DeviceEvents.SampleClockDelay = timeDelaySeconds;

                // 11-15. TClk synchronization and initiation
                NITClk tclk = new NITClk(new ITClkSessionReference[] { rfsg1, rfsg2 });
                tclk.ConfigureForHomogeneousTriggers();
                tclk.Synchronize();
                tclk.Initiate();

                Console.WriteLine("Both VSTs generating phase coherent signal.");
                Console.WriteLine($"Phase offset: {phaseOffsetDegrees} deg, Time delay: {timeDelaySeconds * 1e9:F2} ns");
                Console.WriteLine("Press Enter to stop...");
                Console.ReadLine();
            }
            finally
            {
                if (rfsg1 != null) { rfsg1.Abort(); rfsg1.Close(); }
                if (rfsg2 != null) { rfsg2.Abort(); rfsg2.Close(); }
            }
        }
    }
}
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Phase drifts over time | LO not shared | Enable LO daisy chain (Step 2) |
| Sessions start at different times | Not using TClk | Use `tclk.Initiate()` instead of `rfsg.Initiate()` |
| `-200220` error on Synchronize | Ref clock not configured | Set `PxiClock` on all sessions (Step 1) |
| Inconsistent phase between runs | Auto SG/SA shared LO interfering | Disable with `StoreAutomaticSGSASharedLO` |
| Phase offset has no effect | Set after `Synchronize()` | Set `RF.PhaseOffset` before `tclk.Synchronize()` |
| Time delay has no effect | Set after `Synchronize()` | Set `SampleClockDelay` before `tclk.Synchronize()` |
| Incorrect RF output on receiving VST | LO frequency not configured | Read `rfsg1.RF.LocalOscillator.Frequency` after `RF.Configure()`, set on rfsg2 |

---

## RF Path Calibration (Interferometric Combiner Method)

When two VSTs feed a DUT through different RF paths (cables, connectors,
filters), the paths introduce different phase shifts and delays. To ensure
signals arrive phase-aligned at the DUT, calibrate using a power combiner.

### Physical Setup

```
VST1 RF-OUT --> DUT Path 1 --> Combiner Port 1 --+
                                                  +--> Combiner Output --> Analyzer SA
VST2 RF-OUT --> DUT Path 2 --> Combiner Port 2 --+
```

The analyzer can be a third VST's SA, one of the two VSTs' SA, or any
NIRfsa-compatible instrument.

### Algorithm (Two-Pass Null Search)

1. Both VSTs generate CW at the target frequency (TClk-synchronized)
2. **Coarse sweep**: VST2 `PhaseOffset` 0-360 deg in 10 deg steps, measure
   combined power at combiner output
3. Find the **null** (minimum power = destructive interference)
4. **Fine sweep**: +/-15 deg around the null in 0.5 deg steps for sub-degree
   accuracy
5. **Constructive phase** = null + 180 deg -> this is the correction that
   makes signals arrive in-phase at the DUT

**Why find the null, not the peak**: The destructive null is much sharper than
the constructive peak, giving sub-degree resolution even with modest power
measurement accuracy.

### Amplitude Mismatch from Max/Min Ratio

The max/min power ratio reveals amplitude imbalance between paths:

```
R = P_max / P_min  (linear)
A/B = (sqrt(R) + 1) / (sqrt(R) - 1)
delta_dB = 20 * log10(A/B)
```

A deeper null means better amplitude matching.

### Applying Calibration Results

```csharp
// The calibration returns the constructive phase (in-phase at DUT)
rfsg2.RF.PhaseOffset = cal.PhaseOffsetCorrectionDegrees;
rfsg2.DeviceEvents.SampleClockDelay = cal.TimeDelayCorrectionSeconds;

// Optional: warn if amplitude mismatch is significant
if (cal.AmplitudeDeltaDB > 0.5)
    Console.WriteLine($"WARNING: {cal.AmplitudeDeltaDB:F2} dB mismatch between paths");
```

### Key Implementation Notes

- Use `RfsgWaveformGenerationMode.ContinuousWave` during calibration (no waveform needed)
- Average multiple IQ acquisitions at each phase step to reduce noise
- Add settling time (50 ms default) after each phase change
- Disable automatic SG/SA shared LO on both VSTs during calibration
- Calibration sessions must be closed before opening generation sessions

---

## Using TClk with RFmx (Analysis-Only Mode)

**Problem**: RFmx sessions (`RFmxInstrMX`) cannot be passed to TClk and cannot have
their acquisitions initiated by TClk. Attempting to use `tclk.Initiate()` with RFmx
causes `Fetch` to time out because RFmx's internal state machine never sees the
acquisition start.

### Common Mistakes

| Wrong | Correct | Why |
|---|---|---|
| Pass `RFmxInstrMX` to `NITClk` constructor | Pass `NIRfsa` sessions to `NITClk` | `RFmxInstrMX` does not implement `ITClkSessionReference` |
| Call `tclk.Initiate()` then `specAn.Pavt.Results.Fetch...()` | Use analysis-only mode with `AnalyzeIQ` | RFmx Fetch times out because it didn't initiate the acquisition |
| Call `specAn.Initiate()` on each session independently | Use TClk for initiation (NIRfsa) or shared trigger | Independent initiation breaks synchronization |

### Correct Pattern: NIRfsa + TClk for Acquisition, RFmx for Analysis

When you need both TClk precision **and** RFmx measurement processing (e.g., PAVT),
use the **analysis-only** pattern:

1. **Acquire** with NIRfsa + TClk (full synchronization control)
2. **Analyze** with RFmx in `"AnalysisOnly=1"` mode (no hardware, just signal processing)

```csharp
// --- ACQUISITION: NIRfsa + TClk ---
NIRfsa rfsa1 = new NIRfsa(vstResource1, true, false);
NIRfsa rfsa2 = new NIRfsa(vstResource2, true, false);

// Configure ref clock, LO chain, IQ params on NIRfsa sessions...
// (see Steps 1-4 in main guide)

NITClk tclk = new NITClk(new ITClkSessionReference[] { rfsa1, rfsa2 });
tclk.ConfigureForHomogeneousTriggers();
tclk.Synchronize();
tclk.Initiate();

// Fetch synchronized IQ data
var waveform1 = rfsa1.Acquisition.IQ.FetchIQSingleRecordComplexWaveform(0, numSamples, 10.0);
var waveform2 = rfsa2.Acquisition.IQ.FetchIQSingleRecordComplexWaveform(0, numSamples, 10.0);
rfsa1.Abort();
rfsa2.Abort();

// --- ANALYSIS: RFmx in analysis-only mode ---
var instrSession1 = new RFmxInstrMX(vstResource1, "AnalysisOnly=1");
var specAn1 = new RFmxSpecAnMX(instrSession1, "");

specAn1.ConfigureFrequency("", centerFrequency);
specAn1.ConfigureReferenceLevel("", referenceLevel);
specAn1.SelectMeasurements("", RFmxSpecAnMXMeasurementTypes.Pavt, true);
// Configure PAVT parameters...

// Feed IQ data for processing - no hardware involved
specAn1.AnalyzeIQ("", "", waveform1, true, out _);

// Fetch computed results
specAn1.Pavt.Results.FetchPhaseAndAmplitude("", 10.0, ...);
```

### Key Points

- `"AnalysisOnly=1"` in the RFmx constructor option string disables all hardware access
- `AnalyzeIQ()` accepts a `ComplexWaveform<ComplexDouble>` - the same type returned by NIRfsa fetch
- RFmx handles all PAVT signal processing (segmentation, phase/amplitude extraction, averaging)
- LO sharing and TClk are configured solely on NIRfsa sessions
- This pattern works for any RFmx personality (SpecAn, WLAN, NR, etc.) that supports `AnalyzeIQ`

---

**Last Updated**: Session 2025
**Validated**: Two PXIe-5841 VSTs, phase coherent 802.11ax generation with TClk, LO sharing (with LO frequency propagation), phase offset, time delay, and interferometric combiner-based RF path calibration