# NI-RFSA and NI-RFSG C# API Reference

Complete reference for RF Vector Signal Analyzers (RFSA) and RF Vector Signal Generators (RFSG) in C#.

## Namespaces
```csharp
using NationalInstruments.ModularInstruments.NIRfsa;
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## NI-RFSA (RF Vector Signal Analyzer)

### Session Class

```csharp
// Constructor
public NIRfsa(string resourceName, bool idQuery, bool resetDevice)

// Parameters:
// - resourceName: "PXI1Slot4", "VST_5842", "Dev1", etc.
// - idQuery: false (recommended)
// - resetDevice: false (recommended)
```

### Key RFSA Enumerations

```csharp
// Acquisition Type
RfsaAcquisitionType.Iq          // IQ acquisition
RfsaAcquisitionType.Spectrum    // Spectrum/FFT

// Reference Clock Source
RfsaFrequencyReferenceSource.OnboardClock
RfsaFrequencyReferenceSource.RefIn
RfsaFrequencyReferenceSource.PxiClock

// Trigger Type
RfsaDigitalEdgeTriggerSource.PxiTrig0
RfsaDigitalEdgeTriggerSource.PxiTrig1
RfsaDigitalEdgeTriggerSource.PxiStar
RfsaDigitalEdgeTriggerSource.TimerEvent

// Trigger Edge
RfsaDigitalEdgeTriggerEdge.Rising
RfsaDigitalEdgeTriggerEdge.Falling
```

### RFSA Configuration Properties

```csharp
// Frequency configuration
session.Configuration.AcquisitionType                // Iq or Spectrum
session.Configuration.IQ.CarrierFrequency            // Center frequency (Hz)
session.Configuration.IQ.IQRate                      // Sample rate (S/s)
session.Configuration.IQ.NumberOfSamplesToAcquire    // Sample count

// Reference level
session.Configuration.ReferenceLevel                 // Expected input level (dBm)

// Trigger configuration
session.Configuration.Triggers.StartTrigger.DigitalEdge.Source  // Trigger source
session.Configuration.Triggers.StartTrigger.DigitalEdge.Edge    // Rising/Falling

// Advanced settings
session.Configuration.Attenuation                    // Input attenuation (dB)
session.Configuration.ExternalGain                   // External preamp gain (dB)
session.Configuration.IQ.AdvancedIQBandwidth         // Resolution BW (Hz)
```

### RFSA Common Workflows

#### 1. Simple IQ Acquisition

```csharp
using NationalInstruments.ModularInstruments.NIRfsa;

using (var rfsa = new NIRfsa("PXI1Slot4", false, false))
{
    // Configure acquisition
    rfsa.Configuration.AcquisitionType = RfsaAcquisitionType.Iq;
    rfsa.Configuration.IQ.CarrierFrequency = 2.4e9;        // 2.4 GHz
    rfsa.Configuration.IQ.IQRate = 10e6;                    // 10 MS/s
    rfsa.Configuration.IQ.NumberOfSamplesToAcquire = 10000; // 10k samples
    rfsa.Configuration.ReferenceLevel = 0.0;                // 0 dBm

    // Configure trigger (optional - use immediate if omitted)
    rfsa.Configuration.Triggers.StartTrigger.DigitalEdge.Source = 
        RfsaDigitalEdgeTriggerSource.PxiTrig0;
    rfsa.Configuration.Triggers.StartTrigger.DigitalEdge.Edge = 
        RfsaDigitalEdgeTriggerEdge.Rising;

    // Initiate acquisition
    rfsa.Acquisition.Initiate();

    // Fetch IQ data
    ComplexWaveform<ComplexSingle> waveform = 
        rfsa.Acquisition.IQ.FetchIQSingleRecordComplexF32(
            recordNumber: 0,
            numberOfSamples: 10000,
            timeout: TimeSpan.FromSeconds(5)
        );

    Console.WriteLine($"Acquired {waveform.SampleCount} samples");
    Console.WriteLine($"IQ Rate: {waveform.PrecisionTiming.SampleInterval.FractionalSeconds * 1e9:F3} ns");

    // Process IQ data
    ComplexSingle[] iqData = waveform.GetRawData();
    for (int i = 0; i < Math.Min(10, iqData.Length); i++)
    {
        Console.WriteLine($"Sample {i}: I={iqData[i].Real:F6}, Q={iqData[i].Imaginary:F6}");
    }

    // Abort acquisition
    rfsa.Acquisition.Abort();
}
```

#### 2. Multi-Record Acquisition

```csharp
using (var rfsa = new NIRfsa("PXI1Slot4", false, false))
{
    // Configure for multiple records
    rfsa.Configuration.AcquisitionType = RfsaAcquisitionType.Iq;
    rfsa.Configuration.IQ.CarrierFrequency = 2.4e9;
    rfsa.Configuration.IQ.IQRate = 10e6;
    rfsa.Configuration.IQ.NumberOfSamplesToAcquire = 1000;   // Samples per record
    rfsa.Configuration.IQ.NumberOfRecords = 10;               // 10 records

    rfsa.Configuration.ReferenceLevel = -10.0;  // -10 dBm

    // Trigger on each record
    rfsa.Configuration.Triggers.StartTrigger.DigitalEdge.Source = 
        RfsaDigitalEdgeTriggerSource.PxiTrig0;

    rfsa.Acquisition.Initiate();

    // Fetch all records
    for (int record = 0; record < 10; record++)
    {
        ComplexWaveform<ComplexSingle> waveform = 
            rfsa.Acquisition.IQ.FetchIQSingleRecordComplexF32(
                recordNumber: record,
                numberOfSamples: 1000,
                timeout: TimeSpan.FromSeconds(5)
            );

        Console.WriteLine($"Record {record}: {waveform.SampleCount} samples acquired");

        // Calculate average power for this record
        ComplexSingle[] iqData = waveform.GetRawData();
        double avgPower = iqData.Average(sample => 
            sample.Real * sample.Real + sample.Imaginary * sample.Imaginary);
        double avgPowerDbm = 10 * Math.Log10(avgPower) + 30;

        Console.WriteLine($"  Average power: {avgPowerDbm:F2} dBm");
    }

    rfsa.Acquisition.Abort();
}
```

#### 3. Spectrum Acquisition

```csharp
using (var rfsa = new NIRfsa("PXI1Slot4", false, false))
{
    // Configure spectrum measurement
    rfsa.Configuration.AcquisitionType = RfsaAcquisitionType.Spectrum;
    rfsa.Configuration.Spectrum.CenterFrequency = 2.4e9;     // 2.4 GHz
    rfsa.Configuration.Spectrum.Span = 100e6;                 // 100 MHz span
    rfsa.Configuration.Spectrum.ResolutionBandwidth = 100e3;  // 100 kHz RBW
    rfsa.Configuration.Spectrum.NumberOfAverages = 10;        // Average 10 sweeps

    rfsa.Configuration.ReferenceLevel = 0.0;

    rfsa.Acquisition.Initiate();

    // Fetch spectrum
    SpectrumInfo spectrumInfo;
    double[] spectrum = rfsa.Acquisition.Spectrum.ReadPowerSpectrumF64(
        timeout: TimeSpan.FromSeconds(10),
        spectrumInfo: out spectrumInfo
    );

    Console.WriteLine($"Spectrum points: {spectrum.Length}");
    Console.WriteLine($"Start frequency: {spectrumInfo.InitialFrequency / 1e9:F6} GHz");
    Console.WriteLine($"Frequency increment: {spectrumInfo.FrequencyIncrement / 1e3:F3} kHz");

    // Find peak
    int peakIndex = Array.IndexOf(spectrum, spectrum.Max());
    double peakFrequency = spectrumInfo.InitialFrequency + 
                          peakIndex * spectrumInfo.FrequencyIncrement;
    double peakPower = spectrum[peakIndex];

    Console.WriteLine($"Peak at {peakFrequency / 1e9:F6} GHz: {peakPower:F2} dBm");

    rfsa.Acquisition.Abort();
}
```

---

## NI-RFSG (RF Vector Signal Generator)

**API Verified Against**: NI-RFSG 26.0.0 (.NET Framework 4.8, Fx40 assembly)

### Critical API Corrections

| Wrong (common hallucination) | Correct (verified against DLL + NI examples) |
|---|---|
| `rfsg.RF.GenerationMode = RfsgGenerationMode.Script` | `rfsg.Arb.GenerationMode = RfsgWaveformGenerationMode.Script` |
| `RfsgGenerationMode.ContinuousWaveform` | `RfsgWaveformGenerationMode.ContinuousWave` |
| `RfsgGenerationMode.Arb` | `RfsgWaveformGenerationMode.ArbitraryWaveform` |
| `rfsg.Arb.WriteWaveformComplexF32(name, data)` | `rfsg.Arb.WriteWaveform(name, complexSingleArray)` |
| `rfsg.Arb.LoadWaveformFromFileF64(path, name)` | `rfsg.Arb.ReadAndDownloadWaveformFromFileTdms(name, path, 0)` |
| `RfsgArbGenerationMode.Continuous` | Does not exist. Use `RfsgWaveformGenerationMode.Script` with a repeat-forever script |

### Session Class

```csharp
// Constructor (from NI examples)
public NIRfsg(string resourceName, bool idQuery, bool resetDevice)
public NIRfsg(string resourceName, bool idQuery, bool resetDevice, string optionString)

// Parameters:
// - resourceName: "VST3_1", "PXI1Slot7", etc. (prefer nisyscfg aliases)
// - idQuery: true (NI examples use true) or false
// - resetDevice: false (recommended)
```

### Key RFSG Enumerations

```csharp
// Generation Mode (on rfsg.Arb.GenerationMode, NOT rfsg.RF)
RfsgWaveformGenerationMode.ContinuousWave       // Single tone (CW)
RfsgWaveformGenerationMode.ArbitraryWaveform    // Single waveform playback
RfsgWaveformGenerationMode.Script               // Script-controlled generation

// Power Level Type
RfsgRFPowerLevelType.AveragePower    // Average power (default for modulated signals)
RfsgRFPowerLevelType.PeakPower       // Peak power

// Reference Clock Source
RfsgFrequencyReferenceSource.OnboardClock
RfsgFrequencyReferenceSource.RefIn
RfsgFrequencyReferenceSource.PxiClock
```

### RFSG Properties and Methods (Verified)

```csharp
// --- Top-level NIRfsg methods ---
rfsg.Initiate()                        // Start generation
rfsg.Abort()                           // Stop generation
rfsg.CheckGenerationStatus()           // Returns RfsgGenerationStatus (InProgress/Complete)
rfsg.Close()                           // Close session
rfsg.GetInstrumentHandle()             // Returns SafeHandle
rfsg.VstSelfCalibrate(resourceName)    // VST self-cal

// --- rfsg.RF ---
rfsg.RF.Frequency                      // Carrier frequency (Hz) - get/set
rfsg.RF.PowerLevel                     // Output power (dBm) - get/set
rfsg.RF.PowerLevelType                 // AveragePower or PeakPower
rfsg.RF.OutputEnabled                  // Enable/disable RF output
rfsg.RF.ExternalGain                   // External gain (dB), use negative for attenuation
rfsg.RF.Configure(frequency, power)    // Convenience: set both freq + power at once

// --- rfsg.Arb ---
rfsg.Arb.GenerationMode                // ContinuousWave, ArbitraryWaveform, or Script
rfsg.Arb.IQRate                        // IQ sample rate (S/s)
rfsg.Arb.PreFilterGain                 // Pre-filter gain (dB)
rfsg.Arb.SignalBandwidth               // Signal bandwidth (Hz)
rfsg.Arb.SelectedWaveform              // Currently selected waveform name
rfsg.Arb.WaveformSoftwareScalingFactor // Software scaling factor

// --- rfsg.Arb waveform methods ---
rfsg.Arb.WriteWaveform(name, double[] iData, double[] qData)         // Write from I/Q arrays
rfsg.Arb.WriteWaveform(name, ComplexSingle[] data)                    // Write from ComplexSingle[]
rfsg.Arb.WriteWaveform(name, ComplexDouble[] data)                    // Write from ComplexDouble[]
rfsg.Arb.WriteWaveform(name, ComplexWaveform<ComplexSingle> data)     // Write from typed waveform
rfsg.Arb.ReadAndDownloadWaveformFromFileTdms(name, filePath, index)  // Load TDMS file directly
rfsg.Arb.ClearWaveform(name)                                         // Remove waveform from memory
rfsg.Arb.ClearAllWaveforms()                                         // Remove all waveforms
rfsg.Arb.CheckIfWaveformExists(name)                                 // Check if waveform loaded

// --- rfsg.Arb.Scripting ---
rfsg.Arb.Scripting.WriteScript(scriptText)          // Upload a generation script
rfsg.Arb.Scripting.SelectedScriptName               // Set active script name
rfsg.Arb.Scripting.DeleteScript(name)               // Remove a script
rfsg.Arb.Scripting.CheckIfScriptExists(name)        // Check if script exists

// --- rfsg.FrequencyReference ---
rfsg.FrequencyReference.Configure(source, frequency)  // e.g., (OnboardClock, 10e6)

// --- rfsg.Utility ---
rfsg.Utility.Commit()                  // Commit configuration without initiating
```

### NIRfsgPlayback Static Methods (for advanced waveform control)

NIRfsgPlayback provides additional waveform management beyond what NIRfsg.Arb offers.
All methods require an `IntPtr` handle: `rfsg.GetInstrumentHandle().DangerousGetHandle()`

```csharp
using NationalInstruments.ModularInstruments.NIRfsgPlayback;

IntPtr handle = rfsg.GetInstrumentHandle().DangerousGetHandle();

// Load waveform from TDMS file (alternative to rfsg.Arb.ReadAndDownloadWaveformFromFileTdms)
NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle, filePath, waveformName);

// Retrieve waveform metadata
NIRfsgPlayback.RetrieveWaveformSignalBandwidth(handle, waveformName, out double bandwidth);
NIRfsgPlayback.RetrieveWaveformSampleRate(handle, waveformName, out double sampleRate);
NIRfsgPlayback.RetrieveWaveformPapr(handle, waveformName, out double papr);
NIRfsgPlayback.RetrieveWaveformPeakPowerAdjustment(handle, waveformName, out double adj);

// Script generation helpers
NIRfsgPlayback.SetScriptToGenerateSingleRfsg(handle, scriptText);

// Shared LO configuration (for VSTs)
NIRfsgPlayback.StoreAutomaticSGSASharedLO(handle, "", RfsgPlaybackAutomaticSGSASharedLO.Enabled);

// Waveform property storage
NIRfsgPlayback.StoreWaveformLOOffsetMode(handle, waveformName, NIRfsgPlaybackLOOffsetMode.Auto);

// Cleanup
NIRfsgPlayback.ClearWaveform(handle, waveformName);
```

#### When to use NIRfsgPlayback vs NIRfsg.Arb:
- **`rfsg.Arb.ReadAndDownloadWaveformFromFileTdms()`** — Simple TDMS loading, no metadata retrieval needed
- **`NIRfsgPlayback.ReadAndDownloadWaveformFromFile()`** — When you also need RetrieveWaveformSignalBandwidth, PAPR, shared LO, or burst locations

### RFSG Common Workflows

#### 1. Continuous Wave (CW) Generation

```csharp
using NationalInstruments.ModularInstruments.NIRfsg;

// Based on NI example: GettingStarted\SingleToneGeneration
var rfsg = new NIRfsg("VST3_1", true, false);
try
{
    rfsg.RF.Configure(2.45e9, -10.0);  // 2.45 GHz, -10 dBm
    rfsg.Initiate();

    Console.WriteLine("Generating CW at 2.45 GHz, -10 dBm");
    Console.WriteLine("Press Enter to stop...");
    Console.ReadLine();
}
finally
{
    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
    rfsg.Close();
}
```

#### 2. TDMS Waveform File Generation (Script Mode)

```csharp
// Based on NI example: ArbitraryWaveforms\GenFromFileSingle
using NationalInstruments.ModularInstruments.NIRfsg;

var rfsg = new NIRfsg("VST3_1", true, false);
try
{
    string waveformName = "mywaveform";
    string filePath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\80211ax_80M_MCS11.tdms";

    // Configure RF
    rfsg.RF.Configure(5.18e9, -10.0);
    rfsg.RF.PowerLevelType = RfsgRFPowerLevelType.PeakPower;
    rfsg.RF.ExternalGain = 0.0;  // Use negative value for external attenuation

    // Load TDMS waveform directly via NIRfsg
    rfsg.Arb.ReadAndDownloadWaveformFromFileTdms(waveformName, filePath, 0);

    // Set generation mode to Script
    rfsg.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;

    // Write and select script
    string script = @"script GenerateWfm
        repeat forever
            generate mywaveform
        end repeat
    end script";
    rfsg.Arb.Scripting.WriteScript(script);

    // Initiate
    rfsg.Initiate();

    Console.WriteLine("Generating waveform. Press any key to stop.");
    Console.ReadKey();
}
finally
{
    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
    rfsg.Utility.Commit();
    rfsg.Arb.ClearWaveform("mywaveform");
    rfsg.Close();
}
```

#### 3. TDMS Waveform with NIRfsgPlayback (Metadata Access)

```csharp
// Based on NI example: RFmxWlanFemTestWithAutomaticSGSASharedLO
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.NIRfsgPlayback;

var rfsg = new NIRfsg("VST3_1", true, false);
try
{
    string waveformName = "80211axwaveform";  // No underscores in script names
    string filePath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\80211ax_80M_MCS11.tdms";

    // Get IntPtr handle for NIRfsgPlayback
    IntPtr handle = rfsg.GetInstrumentHandle().DangerousGetHandle();

    // Load waveform and retrieve metadata
    NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle, filePath, waveformName);

    double signalBandwidth = 0;
    NIRfsgPlayback.RetrieveWaveformSignalBandwidth(handle, waveformName, out signalBandwidth);

    // Configure RF
    rfsg.RF.Configure(5.18e9, -10.0);
    rfsg.RF.PowerLevelType = RfsgRFPowerLevelType.PeakPower;
    rfsg.Arb.IQRate = signalBandwidth;  // Use bandwidth from waveform metadata

    // Configure shared LO (for VST instruments)
    NIRfsgPlayback.StoreAutomaticSGSASharedLO(handle, "", RfsgPlaybackAutomaticSGSASharedLO.Enabled);
    NIRfsgPlayback.StoreWaveformLOOffsetMode(handle, waveformName, NIRfsgPlaybackLOOffsetMode.Auto);

    // Script for continuous generation with marker
    string script =
        "script myScript\n" +
        "  repeat forever\n" +
        $"    generate {waveformName} marker0(0)\n" +
        "  end repeat\n" +
        "end script";

    rfsg.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;
    rfsg.Arb.Scripting.WriteScript(script);
    rfsg.Arb.Scripting.SelectedScriptName = "myScript";

    rfsg.RF.OutputEnabled = true;
    rfsg.Initiate();

    Console.WriteLine($"Generating at IQ rate: {signalBandwidth / 1e6:F1} MS/s");
    Console.ReadKey();
}
finally
{
    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
    rfsg.Close();
}
```

#### 4. Custom IQ Waveform Generation

```csharp
// Based on NI example: Scripts\SimpleScript
using NationalInstruments.ModularInstruments.NIRfsg;

var rfsg = new NIRfsg("VST3_1", true, false);
try
{
    int numSamples = 1000;
    double[] iData = new double[numSamples];
    double[] qData = new double[numSamples];

    // Generate a simple tone offset waveform
    for (int i = 0; i < numSamples; i++)
    {
        double phase = 2.0 * Math.PI * i / numSamples;
        iData[i] = Math.Cos(phase);
        qData[i] = Math.Sin(phase);
    }

    rfsg.RF.Configure(2.4e9, -10.0);
    rfsg.RF.PowerLevelType = RfsgRFPowerLevelType.PeakPower;
    rfsg.Arb.IQRate = 10e6;
    rfsg.Arb.PreFilterGain = -2.0;
    rfsg.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;

    // Write two waveforms
    rfsg.Arb.WriteWaveform("tone1", iData, qData);
    rfsg.Arb.WriteWaveform("tone2", qData, iData);  // Swapped I/Q = phase shifted

    // Script alternating between waveforms
    string script = @"script myScript
        repeat forever
            generate tone1
            generate tone2
        end repeat
    end script";

    rfsg.Arb.Scripting.WriteScript(script);
    rfsg.Initiate();

    Console.ReadKey();
}
finally
{
    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
    rfsg.Close();
}
```

#### 3. Modulated Signal Generation (QPSK Example)

```csharp
using (var rfsg = new NIRfsg("PXI1Slot7", false, false))
{
    // Generate QPSK symbols
    int numSymbols = 1000;
    int samplesPerSymbol = 10;
    int totalSamples = numSymbols * samplesPerSymbol;

    ComplexSingle[] waveformData = new ComplexSingle[totalSamples];
    Random rnd = new Random();

    // QPSK constellation points: (±1, ±1) / sqrt(2)
    float scale = 1.0f / (float)Math.Sqrt(2);
    ComplexSingle[] qpskSymbols = new ComplexSingle[]
    {
        new ComplexSingle(scale, scale),      // 00
        new ComplexSingle(-scale, scale),     // 01
        new ComplexSingle(-scale, -scale),    // 10
        new ComplexSingle(scale, -scale)      // 11
    };

    for (int sym = 0; sym < numSymbols; sym++)
    {
        // Random QPSK symbol
        ComplexSingle symbol = qpskSymbols[rnd.Next(4)];

        // Repeat symbol for samplesPerSymbol (simplified - no pulse shaping)
        for (int samp = 0; samp < samplesPerSymbol; samp++)
        {
            waveformData[sym * samplesPerSymbol + samp] = symbol;
        }
    }

    // Configure RFSG
    rfsg.RF.GenerationMode = RfsgGenerationMode.Arb;
    rfsg.RF.Frequency = 2.4e9;
    rfsg.RF.PowerLevel = -5.0;
    rfsg.Arb.IQRate = 1e6;  // 1 MS/s (100 kHz symbol rate)

    // Write and generate waveform
    string waveformName = "qpsk_signal";
    rfsg.Arb.WriteWaveformComplexF32(waveformName, waveformData);

    string script = $"script qpskScript\n" +
                   $"  repeat forever\n" +
                   $"    generate {waveformName}\n" +
                   $"  end repeat\n" +
                   $"end script";

    rfsg.Arb.Scripting.WriteScript(script);
    rfsg.Arb.Scripting.SelectedScriptName = "qpskScript";
    rfsg.RF.OutputEnabled = true;

    rfsg.Initiate();

    Console.WriteLine("Generating QPSK signal at 2.4 GHz...");
    Console.WriteLine("Symbol rate: 100 kHz");
    Console.WriteLine("Press Enter to stop...");
    Console.ReadLine();

    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
}
```

#### 4. Triggered Burst Generation

```csharp
using (var rfsg = new NIRfsg("PXI1Slot7", false, false))
{
    // Create burst waveform (sine burst)
    int burstSamples = 1000;
    ComplexSingle[] burstData = new ComplexSingle[burstSamples];

    for (int i = 0; i < burstSamples; i++)
    {
        double phase = 2 * Math.PI * i / 100;  // 10 cycles
        burstData[i] = new ComplexSingle(
            (float)Math.Cos(phase),
            (float)Math.Sin(phase)
        );
    }

    // Configure RFSG
    rfsg.RF.GenerationMode = RfsgGenerationMode.Script;
    rfsg.RF.Frequency = 2.4e9;
    rfsg.RF.PowerLevel = 0.0;
    rfsg.Arb.IQRate = 10e6;

    // Configure trigger
    rfsg.Triggers.StartTrigger.DigitalEdge.Source = 
        RfsgDigitalEdgeTriggerSource.PxiTrig0;
    rfsg.Triggers.StartTrigger.DigitalEdge.Edge = 
        RfsgDigitalEdgeTriggerEdge.Rising;

    // Write waveform
    rfsg.Arb.WriteWaveformComplexF32("burst", burstData);

    // Script: wait for trigger, generate burst
    string script = "script burstScript\n" +
                   "  repeat forever\n" +
                   "    wait until scriptTrigger0\n" +
                   "    generate burst\n" +
                   "  end repeat\n" +
                   "end script";

    rfsg.Arb.Scripting.WriteScript(script);
    rfsg.Arb.Scripting.SelectedScriptName = "burstScript";
    rfsg.RF.OutputEnabled = true;

    rfsg.Initiate();

    Console.WriteLine("Waiting for trigger on PXI_Trig0...");
    Console.WriteLine("Press Enter to abort...");
    Console.ReadLine();

    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
}
```

---

## Combined RFSA + RFSG Workflows

### Loopback Testing

```csharp
using (var rfsg = new NIRfsg("PXI1Slot7", false, false))
using (var rfsa = new NIRfsa("PXI1Slot4", false, false))
{
    double centerFrequency = 2.45e9;
    double iqRate = 10e6;
    int numSamples = 10000;

    // Configure RFSG (generator)
    rfsg.RF.GenerationMode = RfsgGenerationMode.Arb;
    rfsg.RF.Frequency = centerFrequency;
    rfsg.RF.PowerLevel = -20.0;  // Low power for loopback
    rfsg.Arb.IQRate = iqRate;

    // Create test waveform (tone at 1 MHz offset)
    ComplexSingle[] testWaveform = new ComplexSingle[numSamples];
    for (int i = 0; i < numSamples; i++)
    {
        double phase = 2 * Math.PI * 1e6 * i / iqRate;  // 1 MHz tone
        testWaveform[i] = new ComplexSingle(
            (float)Math.Cos(phase),
            (float)Math.Sin(phase)
        );
    }

    rfsg.Arb.WriteWaveformComplexF32("test_tone", testWaveform);

    string script = "script loopbackScript\n" +
                   "  repeat forever\n" +
                   "    generate test_tone\n" +
                   "  end repeat\n" +
                   "end script";

    rfsg.Arb.Scripting.WriteScript(script);
    rfsg.Arb.Scripting.SelectedScriptName = "loopbackScript";

    // Configure RFSA (analyzer)
    rfsa.Configuration.AcquisitionType = RfsaAcquisitionType.Iq;
    rfsa.Configuration.IQ.CarrierFrequency = centerFrequency;
    rfsa.Configuration.IQ.IQRate = iqRate;
    rfsa.Configuration.IQ.NumberOfSamplesToAcquire = numSamples;
    rfsa.Configuration.ReferenceLevel = -10.0;

    // Start generation
    rfsg.RF.OutputEnabled = true;
    rfsg.Initiate();

    // Small delay for generator to stabilize
    System.Threading.Thread.Sleep(100);

    // Acquire
    rfsa.Acquisition.Initiate();
    ComplexWaveform<ComplexSingle> receivedWaveform = 
        rfsa.Acquisition.IQ.FetchIQSingleRecordComplexF32(
            recordNumber: 0,
            numberOfSamples: numSamples,
            timeout: TimeSpan.FromSeconds(5)
        );

    Console.WriteLine($"Loopback test complete");
    Console.WriteLine($"Transmitted: {numSamples} samples at {centerFrequency / 1e9:F3} GHz");
    Console.WriteLine($"Received: {receivedWaveform.SampleCount} samples");

    // Calculate received power
    ComplexSingle[] rxData = receivedWaveform.GetRawData();
    double avgPower = rxData.Average(s => s.Real * s.Real + s.Imaginary * s.Imaginary);
    double avgPowerDbm = 10 * Math.Log10(avgPower) + 30;
    Console.WriteLine($"Received power: {avgPowerDbm:F2} dBm");

    // Cleanup
    rfsa.Acquisition.Abort();
    rfsg.Abort();
    rfsg.RF.OutputEnabled = false;
}
```

---

## VST (Vector Signal Transceiver) Usage

For NI VST devices (PXIe-5644/5645/5646/5840/5841/5842), both RFSA and RFSG sessions can control the same hardware:

```csharp
// Same resource name for both sessions
string vstResource = "VST_5842";

using (var rfsg = new NIRfsg(vstResource, false, false))
using (var rfsa = new NIRfsa(vstResource, false, false))
{
    // Both sessions control the same VST hardware
    // RFSG controls TX path, RFSA controls RX path

    // Can run simultaneously for full-duplex operation
    // Share reference clocks automatically
}
```

---

## Common Patterns

### Reference Clock Sharing (Multi-Instrument)

```csharp
// Master device exports reference clock
using (var master = new NIRfsg("PXI1Slot7", false, false))
{
    master.FrequencyReference.Source = RfsgFrequencyReferenceSource.OnboardClock;
    master.FrequencyReference.ExportEnabled = true;  // Export to PXI backplane

    // Slave devices import reference clock
    using (var slave = new NIRfsa("PXI1Slot4", false, false))
    {
        slave.FrequencyReference.Source = RfsaFrequencyReferenceSource.PxiClock;

        // Now both instruments phase-locked
    }
}
```

### Digital Trigger Routing

```csharp
// Route RFSG start trigger to RFSA
using (var rfsg = new NIRfsg("PXI1Slot7", false, false))
using (var rfsa = new NIRfsa("PXI1Slot4", false, false))
{
    // RFSG exports trigger on PXI_Trig0 when it starts
    rfsg.Triggers.StartTrigger.ExportOutputTerminal = 
        RfsgExportOutputTerminal.PxiTrig0;

    // RFSA triggers from PXI_Trig0
    rfsa.Configuration.Triggers.StartTrigger.DigitalEdge.Source = 
        RfsaDigitalEdgeTriggerSource.PxiTrig0;

    // Result: RFSA acquisition synchronized with RFSG generation
}
```

---

## Performance Tips

1. **Reuse sessions** - Session creation is slow (~1-2 seconds)
2. **Pre-allocate waveforms** - Write waveforms once, reuse many times
3. **Use scripting for complex sequences** - Avoids software overhead
4. **Match IQ rates** - Use same rate for RFSA/RFSG in loopback tests
5. **Appropriate timeout values** - Calculate based on acquisition time

## Common Errors

### RFSA: Error -5040 (Timeout)
```csharp
// WRONG: Timeout too short for acquisition
rfsa.Configuration.IQ.NumberOfSamplesToAcquire = 100000000;  // 100M samples at 10MS/s = 10s
rfsa.Acquisition.Initiate();
var waveform = rfsa.Acquisition.IQ.FetchIQSingleRecordComplexF32(0, 100000000, 
    TimeSpan.FromSeconds(1));  // ERROR: Only 1s timeout for 10s acquisition

// CORRECT: Timeout > acquisition time
double acqTime = 100000000.0 / 10e6;  // 10 seconds
var waveform = rfsa.Acquisition.IQ.FetchIQSingleRecordComplexF32(0, 100000000, 
    TimeSpan.FromSeconds(acqTime + 2));  // 12s timeout
```

### RFSG: Error -5202 (Invalid Waveform)
```csharp
// WRONG: Waveform data exceeds ±1.0 range
ComplexSingle[] waveform = new ComplexSingle[1000];
for (int i = 0; i < 1000; i++)
{
    waveform[i] = new ComplexSingle(2.0f, 2.0f);  // ERROR: Exceeds ±1.0
}

// CORRECT: Normalize to ±1.0 range
double maxAmplitude = waveform.Max(s => Math.Sqrt(s.Real*s.Real + s.Imaginary*s.Imaginary));
for (int i = 0; i < waveform.Length; i++)
{
    waveform[i] = new ComplexSingle(
        waveform[i].Real / (float)maxAmplitude,
        waveform[i].Imaginary / (float)maxAmplitude
    );
}
```

## Supported Devices

### RFSA
- PXIe-5644/5645/5646 (VST)
- PXIe-5840/5841/5842 (VST)
- PXIe-5663/5663E/5665/5668 (Vector Signal Analyzer)

### RFSG
- PXIe-5644/5645/5646 (VST)
- PXIe-5840/5841/5842 (VST)
- PXIe-5650/5651/5652/5653/5654/5655 (RF Signal Generator)

## NI TClock — Sub-Nanosecond Multi-Instrument Synchronization

**API Verified Against**: NI-TClock 26.3.0 (.NET Framework 4.8, Fx40 assembly)

TClock provides **sub-nanosecond sample-aligned synchronization** across multiple NI modular instruments. Use TClock whenever you need phase-coherent measurements between instruments — such as measuring phase offset between two VST signal analyzers.

### Assembly Reference

```xml
<Reference Include="NationalInstruments.ModularInstruments.TClock.Fx40">
  <HintPath>C:\Windows\Microsoft.NET\assembly\GAC_MSIL\NationalInstruments.ModularInstruments.TClock.Fx40\v4.0_26.3.40.4__dc6ad606294fc298\NationalInstruments.ModularInstruments.TClock.Fx40.dll</HintPath>
  <Private>False</Private>
</Reference>
```

### Namespace

```csharp
using NationalInstruments.ModularInstruments;                              // ITClockSynchronizableDevice
using NationalInstruments.ModularInstruments.SystemServices.TimingServices; // TClock
```

### TClock Class (Verified)

```csharp
// Constructor — pass all devices to synchronize
var tclock = new TClock(new ITClockSynchronizableDevice[] { rfsa1, rfsa2 });

// Key methods
tclock.ConfigureForHomogeneousTriggers();  // Auto-routes triggers between same-type devices
tclock.Synchronize();                       // Aligns sample clocks to sub-nanosecond precision
tclock.Synchronize(PrecisionTimeSpan minTime);  // With minimum sync time
tclock.Initiate();                          // Starts ALL devices simultaneously
tclock.WaitUntilDone(PrecisionTimeSpan timeout);  // Waits for all acquisitions to complete
bool isDone = tclock.IsDone;                // Check completion status

// Devices collection (alternative to constructor)
tclock.DevicesToSynchronize.Add(rfsa1);     // Add individual device
tclock.DevicesToSynchronize.AddRange(new ITClockSynchronizableDevice[] { rfsa1, rfsa2 });
```

**Supported devices** (implement `ITClockSynchronizableDevice`):
- `NIRfsa` — RF Vector Signal Analyzer
- `NIRfsg` — RF Vector Signal Generator
- `NIScope` — Oscilloscope / Digitizer
- `NIFgen` — Function / Arbitrary Waveform Generator

### Critical API Corrections

| Wrong (common hallucination) | Correct (verified against DLL) |
|---|---|
| `TClock.Synchronize(rfsa1, rfsa2)` | `new TClock(new ITClockSynchronizableDevice[] { rfsa1, rfsa2 })` then `tclock.Synchronize()` |
| `TClock.InitiateSynchronously(...)` | `tclock.Initiate()` |
| `rfsa.Acquisition.Initiate()` (with TClock) | `tclock.Initiate()` — **never** call individual Initiate when using TClock |
| `using NationalInstruments.ModularInstruments.TClock` | `using NationalInstruments.ModularInstruments.SystemServices.TimingServices` |
| `ITClockSynchronizableDevice` in `SystemServices.TimingServices` | `ITClockSynchronizableDevice` is in `NationalInstruments.ModularInstruments` (Common assembly) |
| Setting `LOSource = LOIn` without `LOFrequency` | **MUST** read `LOFrequency` from exporter and set on importer: `rfsa2.Configuration.SignalPath.LocalOscillator.LOFrequency = rfsa1.Configuration.SignalPath.LocalOscillator.LOFrequency` |
| `rfsa.Configuration.SignalPath.LOExportEnabled` | **Deprecated** — use `rfsa.Configuration.SignalPath.LocalOscillator.LOExportEnabled` |
| `rfsa.Configuration.SignalPath.LOSource` | **Deprecated** — use `rfsa.Configuration.SignalPath.LocalOscillator.LOSource` |
| `rfsa.Configuration.SignalPath.LOFrequency` | **Deprecated** — use `rfsa.Configuration.SignalPath.LocalOscillator.LOFrequency` |

### ⚠️ When to Use TClock (CRITICAL for Phase Measurements)

**ALWAYS use TClock when measuring phase offset between instruments.** Phase measurements require three levels of synchronization:

1. **Shared Reference Clock** — Locks frequency references so both instruments derive timing from the same source. Without this, frequency drift between instruments makes phase measurements meaningless.
2. **Shared LO (Local Oscillator)** — Ensures both instruments downconvert using the same LO signal, eliminating independent LO phase noise that would corrupt phase offset measurements.
3. **TClock Synchronized Start** — Aligns the first sample of both acquisitions to sub-nanosecond precision, so sample N from instrument 1 corresponds to the same moment as sample N from instrument 2.

**Without all three**, phase offset measurements will show random, non-repeatable results.

### Phase Offset Measurement — Complete Workflow

```csharp
using System;
using System.Linq;
using NationalInstruments;
using NationalInstruments.ModularInstruments.NIRfsa;
using NationalInstruments.ModularInstruments;
using NationalInstruments.ModularInstruments.SystemServices.TimingServices;

// ── Configuration ──
string rfsa1Resource = "VST1";   // DUT output 1
string rfsa2Resource = "VST2";   // DUT output 2
double carrierFrequencyHz = 1e9; // 1 GHz
double iqRateSps = 50e6;         // 50 MS/s
long numberOfSamples = 100000;   // 100k samples
double referenceLevelDbm = 0.0;

NIRfsa rfsa1 = null;
NIRfsa rfsa2 = null;

try
{
    rfsa1 = new NIRfsa(rfsa1Resource, false, false);
    rfsa2 = new NIRfsa(rfsa2Resource, false, false);

    // ── Step 1: Configure both analyzers identically ──
    foreach (var (rfsa, label) in new[] { (rfsa1, "RFSA1"), (rfsa2, "RFSA2") })
    {
        rfsa.Configuration.AcquisitionType = RfsaAcquisitionType.IQ;
        rfsa.Configuration.IQ.CarrierFrequency = carrierFrequencyHz;
        rfsa.Configuration.IQ.IQRate = iqRateSps;
        rfsa.Configuration.IQ.NumberOfSamples = numberOfSamples;
        rfsa.Configuration.Vertical.ReferenceLevel = referenceLevelDbm;
    }

    // ── Step 2: Share reference clock (PXI backplane 10 MHz) ──
    rfsa1.Configuration.ReferenceClock.Configure(RfsaReferenceClockSource.PxiClock, 10e6);
    rfsa2.Configuration.ReferenceClock.Configure(RfsaReferenceClockSource.PxiClock, 10e6);

    // ── Step 3: Share LO — RFSA1 exports, RFSA2 imports ──
    rfsa1.Configuration.SignalPath.LocalOscillator.LOExportEnabled = true;  // Export LO from RFSA1

    // Read LO frequency from exporter and set on importer (CRITICAL)
    double loFrequency = rfsa1.Configuration.SignalPath.LocalOscillator.LOFrequency;
    rfsa2.Configuration.SignalPath.LocalOscillator.LOSource = RfsaLOSource.LOIn;  // RFSA2 imports LO
    rfsa2.Configuration.SignalPath.LocalOscillator.LOFrequency = loFrequency;     // Must match exporter's LO freq

    // ── Step 4: TClock synchronization ──
    var tclock = new TClock(new ITClockSynchronizableDevice[] { rfsa1, rfsa2 });
    tclock.ConfigureForHomogeneousTriggers();
    tclock.Synchronize();

    // ── Step 5: Acquire and measure ──
    var timeout = PrecisionTimeSpan.FromSeconds(10);

    for (int meas = 0; meas < 10; meas++)
    {
        // TClock starts both acquisitions simultaneously
        tclock.Initiate();

        var waveform1 = rfsa1.Acquisition.IQ.FetchIQSingleRecordComplexWaveform<ComplexSingle>(
            0, numberOfSamples, timeout);
        var waveform2 = rfsa2.Acquisition.IQ.FetchIQSingleRecordComplexWaveform<ComplexSingle>(
            0, numberOfSamples, timeout);

        rfsa1.Acquisition.IQ.Abort();
        rfsa2.Acquisition.IQ.Abort();

        // Cross-correlation at zero lag to extract phase offset
        var iq1 = waveform1.GetRawData();
        var iq2 = waveform2.GetRawData();
        double sumReal = 0, sumImag = 0;
        for (int i = 0; i < iq1.Length; i++)
        {
            // iq1[n] * conj(iq2[n])
            sumReal += iq1[i].Real * iq2[i].Real + iq1[i].Imaginary * iq2[i].Imaginary;
            sumImag += iq1[i].Imaginary * iq2[i].Real - iq1[i].Real * iq2[i].Imaginary;
        }
        double phaseDeg = Math.Atan2(sumImag, sumReal) * 180.0 / Math.PI;
        Console.WriteLine($"  Measurement {meas + 1}: Phase Offset = {phaseDeg:F3} deg");
    }
}
finally
{
    try { rfsa1?.Acquisition.IQ.Abort(); } catch { }
    try { rfsa2?.Acquisition.IQ.Abort(); } catch { }
    rfsa1?.Close();
    rfsa2?.Close();
}
```

### LO Sharing — RFSA Properties (Verified)

**⚠️ CRITICAL: LO Frequency Transfer Rule**

When sharing LO between instruments, you **MUST** read the LO frequency from the exporting instrument and set it on the importing instrument. The LO frequency is determined by the carrier configuration and may differ from the carrier frequency due to LO injection side and IF frequency offsets.

```csharp
// CORRECT: Read LO freq from exporter, set on importer
rfsa1.Configuration.SignalPath.LocalOscillator.LOExportEnabled = true;
double loFreq = rfsa1.Configuration.SignalPath.LocalOscillator.LOFrequency;  // Read actual LO freq
rfsa2.Configuration.SignalPath.LocalOscillator.LOSource = RfsaLOSource.LOIn;
rfsa2.Configuration.SignalPath.LocalOscillator.LOFrequency = loFreq;          // Set matching freq

// WRONG: Only setting LOSource without LOFrequency
rfsa2.Configuration.SignalPath.LocalOscillator.LOSource = RfsaLOSource.LOIn;  // Missing LOFrequency!
```

```csharp
// ── Signal Path LO Configuration (use LocalOscillator sub-object) ──
// ⚠️ SignalPath.LOExportEnabled / LOSource / LOFrequency are DEPRECATED in v26.3+
// ✅ ALWAYS use SignalPath.LocalOscillator.* instead:
rfsa.Configuration.SignalPath.LocalOscillator.LOExportEnabled  // bool: export LO to external port
rfsa.Configuration.SignalPath.LocalOscillator.LO2ExportEnabled // bool: export LO2 (dual-stage downconversion)
rfsa.Configuration.SignalPath.LocalOscillator.LOSource         // RfsaLOSource: where LO comes from
rfsa.Configuration.SignalPath.LocalOscillator.LOFrequency      // double: LO frequency (read from exporter, write on importer)

// RfsaLOSource values:
RfsaLOSource.Onboard     // Use instrument's internal LO (default)
RfsaLOSource.LOIn        // Import LO from external source (another instrument)
RfsaLOSource.Secondary   // Use secondary LO path
RfsaLOSource.SGSAShared  // Share LO between SG/SA on same VST
RfsaLOSource.None        // No LO (baseband mode)

// ── Per-channel LO (LocalOscillator sub-object) ──
rfsa.Configuration.SignalPath.LocalOscillator.LOSource
rfsa.Configuration.SignalPath.LocalOscillator.LOExportEnabled
rfsa.Configuration.SignalPath.LocalOscillator.LOOutPower   // dBm
rfsa.Configuration.SignalPath.LocalOscillator.LOInPower    // dBm
```

### LO Sharing — RFSG Properties (Verified)

```csharp
// ── RFSG LO export for sharing with RFSA ──
rfsg.RF.LocalOscillator.LOOutEnabled   // bool: export LO
rfsg.RF.LocalOscillator.Source         // RfsgLocalOscillatorSource

// RfsgLocalOscillatorSource values:
RfsgLocalOscillatorSource.Onboard            // Internal LO (default)
RfsgLocalOscillatorSource.LOIn               // Import LO from external
RfsgLocalOscillatorSource.Secondary          // Secondary LO path
RfsgLocalOscillatorSource.SGSAShared         // Share LO between SG/SA on same VST
RfsgLocalOscillatorSource.AutomaticSGSAShared // Auto-configure SG/SA shared LO
```

### Synchronization Patterns Summary

| Synchronization Level | What It Does | API |
|---|---|---|
| **Reference Clock** | Locks frequency references to same source | `rfsa.Configuration.ReferenceClock.Configure(RfsaReferenceClockSource.PxiClock, 10e6)` |
| **Shared LO** | Eliminates independent LO phase noise | `rfsa1.Configuration.SignalPath.LocalOscillator.LOExportEnabled = true` → read `rfsa1.Configuration.SignalPath.LocalOscillator.LOFrequency` → set `rfsa2.Configuration.SignalPath.LocalOscillator.LOSource = RfsaLOSource.LOIn` + `rfsa2.Configuration.SignalPath.LocalOscillator.LOFrequency = loFreq` |
| **TClock Sync** | Sub-nanosecond sample alignment | `tclock.ConfigureForHomogeneousTriggers()` → `tclock.Synchronize()` → `tclock.Initiate()` |

**For phase offset measurements: ALL THREE levels are required.**

---

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [RFmx Reference](./rfmx-csharp.md)
- [RFmx Generation + Measurement Workflows](./rfmx-generation-measurement-workflows.md) — complete RF generation + measurement (loopback) worked examples
