# RFmx Generation + Measurement Complete Workflows

**Purpose**: Production-ready C# patterns for RF signal generation with RFSG followed by RFmx measurements. These workflows implement the complete test automation pattern: generate a known signal → trigger acquisition → measure → validate.

**Default Triggering**: All workflows use **IQPowerEdge triggering** for reliable signal acquisition. This trigger fires when the signal power crosses a threshold, ensuring clean measurements with minimal preamble loss.

**API Verified Against**: NI RFmx WLAN 26.3.0 / NIRfsg 26.0.0 (.NET Framework 4.8, Fx40 assemblies)

---

## Critical API Corrections

| Wrong (common hallucination) | Correct (verified against DLL) |
|---|---|
| `wlan.Triggers.IQPowerEdgeTrigger.Configure(...)` | `wlan.ConfigureIQPowerEdgeTrigger(...)` (flat method on RFmxWlanMX) |
| `rfsg.DangerousGetInstrumentHandle()` | `rfsg.GetInstrumentHandle().DangerousGetHandle()` (returns IntPtr) |
| `rfsg.Arb.LoadWaveformFromFileF64(path, name)` | `NIRfsgPlayback.ReadAndDownloadWaveformFromFile(handle, path, name)` |
| `RFmxWlanMXIQPowerEdgeTriggerEnabled.True` | `true` (plain bool parameter) |
| `NIRfsgPlayback.RetrieveWaveformSignalBandwidth()` for IQ rate | `NIRfsgPlayback.RetrieveWaveformSampleRate()` — bandwidth ≠ sample rate! |
| Waveform name starting with digit (e.g., `80211ax...`) | Must start with a letter (e.g., `wlan80211ax...`) — RFSG script parser rejects leading digits |
| Missing `rfsg.Arb.GenerationMode = Script` | **REQUIRED** before `Initiate()` when using scripts — without it, RFSG stays in CW mode and no waveform plays |
| `spectrum.Data[i]`, `spectrum.GetRawData()` | `spectrum.Samples.ToArray()` — use `.Samples` property, then `.ToArray()` to get `float[]` |
| `spectrum.InitialFrequency`, `spectrum.X0` | `spectrum.StartFrequency` — initial frequency in Hz |
| `spectrum.DeltaX` | `spectrum.FrequencyIncrement` — frequency step in Hz |

### Spectrum<float> Data Access Pattern

When fetching SEM spectrum or other frequency-domain data from RFmx:

```csharp
Spectrum<float> spectrum = null;
Spectrum<float> compositeMask = null;
wlan.Sem.Results.FetchSpectrum("", 10.0, ref spectrum, ref compositeMask);

// Access spectrum data:
float[] spectrumData = spectrum.Samples.ToArray();
double startFreq = spectrum.StartFrequency;  // Hz
double freqStep = spectrum.FrequencyIncrement;  // Hz
int numPoints = spectrum.SampleCount;

for (int i = 0; i < numPoints; i++)
{
    double frequency = startFreq + i * freqStep;
    float power = spectrumData[i];
    // Plot or process (frequency, power) point
}
```

---

## Prerequisites

```csharp
using System;
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.NIRfsgPlayback;
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.WlanMX;      // Or other RFmx personality
```

### Required Assemblies (from installed NI drivers)

| Assembly | Location |
|---|---|
| `NationalInstruments.ModularInstruments.NIRfsg.Fx40` | `C:\Program Files\IVI Foundation\IVI\Microsoft.NET\Framework64\v4.0.30319\` |
| `NationalInstruments.ModularInstruments.NIRfsgPlayback.Fx40` | `C:\Program Files (x86)\National Instruments\MeasurementStudioVS2010\DotNET\Assemblies\Current\` |
| `NationalInstruments.RFmx.InstrMX.Fx40` | Same as above |
| `NationalInstruments.RFmx.WlanMX.Fx40` | Same as above |
| `NationalInstruments.ModularInstruments.Common` | `C:\Program Files\IVI Foundation\IVI\Microsoft.NET\Framework64\v4.0.30319\` |

---

## Standard Workflow Pattern

All generation + measurement workflows follow this sequence:

1. **Initialize RFSG** - Create generator session
2. **Load Waveform via NIRfsgPlayback** - Download TDMS waveform to instrument memory
3. **Configure & Start Generation** - Set frequency, power, script, initiate
4. **Initialize RFmx** - Create analyzer session with `GetWlanSignalConfiguration()`
5. **Configure IQPowerEdge Trigger** - Flat method call with all parameters
6. **Configure Measurement** - Select measurements, configure averaging
7. **Initiate & Fetch Results** - Start acquisition and retrieve data
8. **Cleanup** - Stop generation, dispose sessions

---

## Workflow 1: WLAN (Wi-Fi) Signal Generation + EVM/TxP Measurement

Complete 802.11ax signal generation with EVM and transmit power measurements.
Based on NI official example: `RFmxWlanOfdmModAccTxpComposite` and `RFmxWlanFemTestWithAutomaticSGSASharedLO`.

```csharp
using System;
using NationalInstruments.ModularInstruments.NIRfsg;
using NationalInstruments.ModularInstruments.NIRfsgPlayback;
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.WlanMX;

public class WlanGenerationMeasurement
{
    public static void MeasureWlanTxpAndEvm()
    {
        NIRfsg rfsg = null;
        RFmxInstrMX instrSession = null;
        RFmxWlanMX wlan = null;

        try
        {
            // ============================================
            // 1. INITIALIZE RFSG (Signal Generator)
            // ============================================
            string resourceName = "VST3_1";  // Use nisyscfg alias
            rfsg = new NIRfsg(resourceName, false, false);

            // ============================================
            // 2. LOAD WAVEFORM VIA NIRfsgPlayback
            // ============================================
            // IMPORTANT: Use NIRfsgPlayback for TDMS waveform loading
            // rfsg.Arb.LoadWaveformFromFileF64() does NOT work for TDMS files
            string waveformPath = @"C:\Users\Public\Documents\National Instruments\RFIC Test Software\Waveforms\80211ax_80M_MCS11.tdms";
            string waveformName = "wlan80211ax80MMCS11";  // Must start with a letter, no underscores

            // Get IntPtr handle (required by NIRfsgPlayback)
            IntPtr instrumentHandle = rfsg.GetInstrumentHandle().DangerousGetHandle();
            NIRfsgPlayback.ReadAndDownloadWaveformFromFile(instrumentHandle, waveformPath, waveformName);

            // Retrieve SAMPLE RATE (not signal bandwidth!) from waveform metadata
            // SignalBandwidth = occupied BW (e.g. 80 MHz), SampleRate = actual IQ rate (e.g. 100 MS/s)
            double sampleRate = 0;
            NIRfsgPlayback.RetrieveWaveformSampleRate(instrumentHandle, waveformName, out sampleRate);

            // ============================================
            // 3. CONFIGURE & START GENERATION
            // ============================================
            double centerFrequency = 5.18e9;  // 5.18 GHz (channel 36)
            double outputPower = -10.0;       // dBm

            rfsg.RF.Frequency = centerFrequency;
            rfsg.RF.PowerLevel = outputPower;
            rfsg.Arb.IQRate = sampleRate;

            // Create script for continuous generation
            string script =
                "script myScript\n" +
                "  repeat forever\n" +
                $"    generate {waveformName} marker0(0)\n" +
                "  end repeat\n" +
                "end script";

            rfsg.Arb.Scripting.SelectedScriptName = "myScript";
            rfsg.Arb.GenerationMode = RfsgWaveformGenerationMode.Script;  // REQUIRED for script playback

            rfsg.RF.OutputEnabled = true;
            rfsg.Initiate();
            System.Threading.Thread.Sleep(200);

            // ============================================
            // 4. INITIALIZE RFmx WLAN SESSION
            // ============================================
            instrSession = new RFmxInstrMX(resourceName, "");
            wlan = instrSession.GetWlanSignalConfiguration();  // Factory method - NOT new RFmxWlanMX()

            // ============================================
            // 5. CONFIGURE IQPowerEdge TRIGGER
            // ============================================
            // NOTE: This is a FLAT method on RFmxWlanMX - no Triggers property hierarchy!
            wlan.ConfigureIQPowerEdgeTrigger("",
                "0",                                              // triggerSource
                RFmxWlanMXIQPowerEdgeTriggerSlope.Rising,         // slope
                -20.0,                                            // level (dB relative to ref level)
                0.0,                                              // triggerDelay (s)
                RFmxWlanMXTriggerMinimumQuietTimeMode.Auto,       // quietTimeMode
                100e-6,                                           // quietTimeDuration (s)
                RFmxWlanMXIQPowerEdgeTriggerLevelType.Relative,   // levelType
                true);                                            // enableTrigger (bool, NOT an enum)

            // ============================================
            // 6. CONFIGURE MEASUREMENTS
            // ============================================
            wlan.ConfigureFrequency("", centerFrequency);
            wlan.ConfigureReferenceLevel("", outputPower + 3.0);
            wlan.ConfigureStandard("", RFmxWlanMXStandard.Standard802_11ax);
            wlan.ConfigureChannelBandwidth("", 80e6);

            wlan.SelectMeasurements("",
                RFmxWlanMXMeasurementTypes.Txp | RFmxWlanMXMeasurementTypes.OfdmModAcc,
                true);

            // TxP configuration
            wlan.Txp.Configuration.ConfigureAveraging("",
                RFmxWlanMXTxpAveragingEnabled.True, 10);
            wlan.Txp.Configuration.ConfigureMaximumMeasurementInterval("", 1e-3);

            // OfdmModAcc (EVM) configuration
            wlan.OfdmModAcc.Configuration.ConfigureAveraging("",
                RFmxWlanMXOfdmModAccAveragingEnabled.True, 10);
            wlan.OfdmModAcc.Configuration.ConfigureMeasurementLength("", 0, 16);

            // ============================================
            // 7. INITIATE & FETCH RESULTS
            // ============================================
            wlan.Initiate("", "");

            // Fetch TxP results
            double averagePowerMean = 0, peakPowerMaximum = 0;
            wlan.Txp.Results.FetchMeasurement("", 10.0, out averagePowerMean, out peakPowerMaximum);

            // Fetch EVM results
            double compositeRmsEvmMean = 0, compositeDataRmsEvmMean = 0, compositePilotRmsEvmMean = 0;
            wlan.OfdmModAcc.Results.FetchCompositeRmsEvm("", 10.0,
                out compositeRmsEvmMean, out compositeDataRmsEvmMean, out compositePilotRmsEvmMean);

            // Optional: frequency and clock error
            double frequencyErrorMean = 0, symbolClockErrorMean = 0;
            wlan.OfdmModAcc.Results.FetchFrequencyErrorMean("", 10.0, out frequencyErrorMean);
            wlan.OfdmModAcc.Results.FetchSymbolClockErrorMean("", 10.0, out symbolClockErrorMean);

            // Print results
            Console.WriteLine("\n=== TxP Results ===");
            Console.WriteLine($"Average Power Mean: {averagePowerMean:F2} dBm");
            Console.WriteLine($"Peak Power Maximum: {peakPowerMaximum:F2} dBm");
            Console.WriteLine("\n=== EVM Results ===");
            Console.WriteLine($"Composite RMS EVM Mean: {compositeRmsEvmMean:F3} dB");
            Console.WriteLine($"Data RMS EVM Mean:      {compositeDataRmsEvmMean:F3} dB");
            Console.WriteLine($"Pilot RMS EVM Mean:     {compositePilotRmsEvmMean:F3} dB");
            Console.WriteLine($"Frequency Error Mean:   {frequencyErrorMean / 1e3:F3} kHz");
            Console.WriteLine($"Symbol Clock Error Mean: {symbolClockErrorMean:F3} ppm");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
        }
        finally
        {
            // ============================================
            // 8. CLEANUP
            // ============================================
            if (wlan != null)
            {
                wlan.Dispose();
                wlan = null;
            }
            if (instrSession != null)
            {
                instrSession.Close();
                instrSession = null;
            }
            if (rfsg != null)
            {
                rfsg.Abort();
                rfsg.RF.OutputEnabled = false;
                rfsg.Close();
            }
        }
    }
}
```

---

## ConfigureIQPowerEdgeTrigger — Full Signature Reference

```csharp
// This is a FLAT method directly on RFmxWlanMX (and other RFmx personalities).
// There is NO nested Triggers.IQPowerEdgeTrigger property.
void ConfigureIQPowerEdgeTrigger(
    string selectorString,                              // "" for default
    string iqPowerEdgeTriggerSource,                    // "0" for channel 0
    RFmxWlanMXIQPowerEdgeTriggerSlope slope,            // Rising or Falling
    double iqPowerEdgeTriggerLevel,                     // dB (relative) or dBm (absolute)
    double triggerDelay,                                // seconds
    RFmxWlanMXTriggerMinimumQuietTimeMode quietMode,    // Auto or Manual
    double triggerMinimumQuietTimeDuration,             // seconds (e.g., 100e-6)
    RFmxWlanMXIQPowerEdgeTriggerLevelType levelType,    // Relative or Absolute
    bool enableTrigger                                  // true/false (NOT an enum)
);
```

---

## NIRfsgPlayback Handle Pattern

```csharp
// CORRECT: Two-step handle extraction
IntPtr instrumentHandle = rfsg.GetInstrumentHandle().DangerousGetHandle();
NIRfsgPlayback.ReadAndDownloadWaveformFromFile(instrumentHandle, filePath, waveformName);
NIRfsgPlayback.RetrieveWaveformSignalBandwidth(instrumentHandle, waveformName, out iqRate);

// WRONG (deprecated, generates CS0618 warning):
// IntPtr handle = rfsg.DangerousGetInstrumentHandle();

// WRONG (type mismatch - SafeHandle, not IntPtr):
// NIRfsgPlayback.ReadAndDownloadWaveformFromFile(rfsg.GetInstrumentHandle(), ...);
```

---

## Other Trigger Methods Available

```csharp
// Digital edge trigger (e.g., from marker or external)
wlan.ConfigureDigitalEdgeTrigger(string selectorString, string source,
    RFmxWlanMXDigitalEdgeTriggerEdge edge, double triggerDelay, bool enableTrigger);

// Software trigger
wlan.ConfigureSoftwareEdgeTrigger(string selectorString, double triggerDelay, bool enableTrigger);

// Disable triggering (free-run)
wlan.DisableTrigger(string selectorString);
```
                rfsg.Dispose();
                Console.WriteLine("RFSG: Signal generation stopped");
            }

            wlan?.Dispose();
            instrSession?.Dispose();
            Console.WriteLine("RFmx: Sessions closed");
        }
    }

    // Helper: Generate simple OFDM-like waveform for testing
    private static ComplexSingle[] GenerateSimpleOfdmWaveform(double iqRate)
    {
        int numSamples = (int)(iqRate * 0.001);  // 1 ms of data
        ComplexSingle[] waveform = new ComplexSingle[numSamples];
        Random rnd = new Random(42);

        // Generate simple random QPSK-like constellation
        float scale = 1.0f / (float)Math.Sqrt(2);
        for (int i = 0; i < numSamples; i++)
        {
            int sym = rnd.Next(4);
            float I = (sym & 1) == 0 ? scale : -scale;
            float Q = (sym & 2) == 0 ? scale : -scale;
            waveform[i] = new ComplexSingle(I, Q);
        }

        return waveform;
    }
}
```

---

## Workflow 2: LTE Signal Generation + ModAcc/ACP Measurement

Complete LTE downlink signal with EVM and adjacent channel power measurements.

```csharp
using NationalInstruments.RFmx.LTEMX;

public class LteGenerationMeasurement
{
    public static void MeasureLteFdd()
    {
        NIRfsg rfsg = null;
        RFmxInstrMX instrSession = null;
        RFmxLTEMX lte = null;

        try
        {
            // 1. Initialize RFSG
            string generatorResource = "PXI1Slot7";
            rfsg = new NIRfsg(generatorResource, false, false);

            // 2. Generate LTE FDD signal (10 MHz BW, 50 RBs)
            double centerFrequency = 1.95e9;  // Band 2 downlink
            double outputPower = -5.0;
            double iqRate = 30.72e6;  // LTE 10 MHz IQ rate

            // Load LTE waveform (PDSCH, 64QAM, full RB allocation)
            string waveformPath = @"C:\Path\To\LTE_FDD_10MHz_64QAM.tdms";
            rfsg.Arb.LoadWaveformFromFileF64(waveformPath, "lte_waveform");

            rfsg.RF.Frequency = centerFrequency;
            rfsg.RF.PowerLevel = outputPower;
            rfsg.Arb.IQRate = iqRate;

            string script = 
                "script lteScript\n" +
                "  repeat forever\n" +
                "    generate lte_waveform\n" +
                "  end repeat\n" +
                "end script";

            rfsg.Arb.Scripting.WriteScript(script);
            rfsg.Arb.Scripting.SelectedScriptName = "lteScript";
            rfsg.RF.OutputEnabled = true;
            rfsg.Initiate();

            Console.WriteLine("RFSG: Generating LTE FDD signal at 1.95 GHz");
            System.Threading.Thread.Sleep(100);

            // 3. Initialize RFmx
            string analyzerResource = "PXI1Slot4";
            instrSession = new RFmxInstrMX(analyzerResource, "");
            lte = new RFmxLTEMX(instrSession, "");

            // 4. Configure IQPowerEdge Trigger
            lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ModAcc | 
                                        RFmxLTEMXMeasurementTypes.Acp, 
                                        false);

            lte.Triggers.IQPowerEdgeTrigger.Configure("", 
                RFmxLTEMXIQPowerEdgeTriggerEnabled.True,
                -15.0,  // Trigger level
                RFmxLTEMXIQPowerEdgeTriggerSlope.Rising);

            Console.WriteLine("RFmx: Configured IQPowerEdge trigger");

            // 5. Configure LTE Measurement
            lte.ConfigureFrequency("", centerFrequency);
            lte.ConfigureReferenceLevel("", 0.0);
            lte.ComponentCarrier.ConfigureBandwidth("", 10e6);  // 10 MHz BW
            lte.ComponentCarrier.ConfigureCellID("", 0);

            // Configure ModAcc (EVM)
            lte.ModAcc.Configuration.ConfigureAveraging("", 
                RFmxLTEMXModAccAveragingEnabled.True, 10);
            lte.ModAcc.Configuration.ConfigureSynchronizationMode("", 
                RFmxLTEMXModAccSynchronizationMode.Frame);

            // Configure ACP
            lte.Acp.Configuration.ConfigureNumberOfOffsets("", 2);  // E-UTRA +/-1
            lte.Acp.Configuration.ConfigureAveraging("", 
                RFmxLTEMXAcpAveragingEnabled.True, 10, 
                RFmxLTEMXAcpAveragingType.Rms);

            Console.WriteLine("RFmx: Configured LTE measurements");

            // 6. Initiate and Measure
            lte.Initiate("", "");
            Console.WriteLine("RFmx: Measuring LTE signal...");

            // Fetch ModAcc results
            double compositeRmsEvm = 0, compositePeakEvm = 0;
            lte.ModAcc.Results.FetchCompositeEvm("", 10.0, 
                out compositeRmsEvm, out compositePeakEvm);

            double freqError = 0;
            lte.ModAcc.Results.FetchCarrierFrequencyLeakage("", 10.0, out freqError);

            Console.WriteLine($"\n=== LTE ModAcc Results ===");
            Console.WriteLine($"Composite RMS EVM: {compositeRmsEvm:F3} %");
            Console.WriteLine($"Composite Peak EVM: {compositePeakEvm:F3} %");
            Console.WriteLine($"Frequency Error: {freqError / 1e3:F3} kHz");

            // Fetch ACP results
            double[] lowerOffsetPower = new double[2];
            double[] upperOffsetPower = new double[2];
            double[] lowerRelativePower = new double[2];
            double[] upperRelativePower = new double[2];

            lte.Acp.Results.FetchOffsetMeasurementArray("", 10.0,
                ref lowerOffsetPower, ref upperOffsetPower,
                ref lowerRelativePower, ref upperRelativePower);

            Console.WriteLine($"\n=== LTE ACP Results ===");
            Console.WriteLine($"Lower E-UTRA: {lowerRelativePower[0]:F2} dBc");
            Console.WriteLine($"Upper E-UTRA: {upperRelativePower[0]:F2} dBc");

            // Pass/Fail (LTE EVM limit: 8% for 64QAM, ACP: -30 dBc)
            bool evmPass = compositeRmsEvm < 8.0;
            bool acpPass = lowerRelativePower[0] < -30.0 && upperRelativePower[0] < -30.0;
            Console.WriteLine($"\nEVM PASS/FAIL: {(evmPass ? "PASS" : "FAIL")}");
            Console.WriteLine($"ACP PASS/FAIL: {(acpPass ? "PASS" : "FAIL")}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
        }
        finally
        {
            // Cleanup
            if (rfsg != null)
            {
                rfsg.Abort();
                rfsg.RF.OutputEnabled = false;
                rfsg.Dispose();
            }
            lte?.Dispose();
            instrSession?.Dispose();
        }
    }
}
```

---

## Workflow 3: 5G NR Signal Generation + ModAcc Measurement

5G NR FR1 (sub-6 GHz) signal with EVM measurement.

```csharp
using NationalInstruments.RFmx.NRMX;

public class NrGenerationMeasurement
{
    public static void Measure5gNr()
    {
        NIRfsg rfsg = null;
        RFmxInstrMX instrSession = null;
        RFmxNRMX nr = null;

        try
        {
            // 1. Initialize RFSG
            rfsg = new NIRfsg("PXI1Slot7", false, false);

            // 2. Generate 5G NR signal (100 MHz BW, FR1)
            double centerFrequency = 3.5e9;  // n78 band (3.5 GHz)
            double outputPower = 0.0;
            double iqRate = 245.76e6;  // 100 MHz NR IQ rate

            string waveformPath = @"C:\Path\To\5GNR_100MHz_256QAM.tdms";
            rfsg.Arb.LoadWaveformFromFileF64(waveformPath, "nr_waveform");

            rfsg.RF.Frequency = centerFrequency;
            rfsg.RF.PowerLevel = outputPower;
            rfsg.Arb.IQRate = iqRate;

            string script = 
                "script nrScript\n" +
                "  repeat forever\n" +
                "    generate nr_waveform\n" +
                "  end repeat\n" +
                "end script";

            rfsg.Arb.Scripting.WriteScript(script);
            rfsg.Arb.Scripting.SelectedScriptName = "nrScript";
            rfsg.RF.OutputEnabled = true;
            rfsg.Initiate();

            Console.WriteLine("RFSG: Generating 5G NR signal at 3.5 GHz");
            System.Threading.Thread.Sleep(100);

            // 3. Initialize RFmx
            instrSession = new RFmxInstrMX("PXI1Slot4", "");
            nr = new RFmxNRMX(instrSession, "");

            // 4. Configure IQPowerEdge Trigger
            nr.SelectMeasurements("", RFmxNRMXMeasurementTypes.ModAcc, false);

            nr.Triggers.IQPowerEdgeTrigger.Configure("", 
                RFmxNRMXIQPowerEdgeTriggerEnabled.True,
                -10.0,
                RFmxNRMXIQPowerEdgeTriggerSlope.Rising);

            Console.WriteLine("RFmx: Configured IQPowerEdge trigger");

            // 5. Configure NR Measurement
            nr.ConfigureFrequency("", centerFrequency);
            nr.ConfigureReferenceLevel("", 5.0);
            nr.ComponentCarrier.ConfigureBandwidth("", 100e6);
            nr.ComponentCarrier.ConfigureSubcarrierSpacing("", 30e3);  // 30 kHz SCS

            nr.ModAcc.Configuration.ConfigureAveraging("", 
                RFmxNRMXModAccAveragingEnabled.True, 10);

            Console.WriteLine("RFmx: Configured 5G NR measurements");

            // 6. Initiate and Measure
            nr.Initiate("", "");

            double compositeRmsEvm = 0, compositePeakEvm = 0;
            nr.ModAcc.Results.FetchCompositeEvm("", 10.0, 
                out compositeRmsEvm, out compositePeakEvm);

            double freqError = 0;
            nr.ModAcc.Results.FetchCarrierFrequencyLeakage("", 10.0, out freqError);

            Console.WriteLine($"\n=== 5G NR ModAcc Results ===");
            Console.WriteLine($"Composite RMS EVM: {compositeRmsEvm:F3} %");
            Console.WriteLine($"Composite Peak EVM: {compositePeakEvm:F3} %");
            Console.WriteLine($"Frequency Error: {freqError / 1e3:F3} kHz");

            // Pass/Fail (5G NR 256QAM: 3.5% EVM limit)
            bool evmPass = compositeRmsEvm < 3.5;
            Console.WriteLine($"\nEVM PASS/FAIL (256QAM): {(evmPass ? "PASS" : "FAIL")}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
        }
        finally
        {
            if (rfsg != null)
            {
                rfsg.Abort();
                rfsg.RF.OutputEnabled = false;
                rfsg.Dispose();
            }
            nr?.Dispose();
            instrSession?.Dispose();
        }
    }
}
```

---

## Workflow 4: Bluetooth Signal Generation + TxP/ModAcc Measurement

Bluetooth LE signal with transmit power and modulation accuracy.

```csharp
using NationalInstruments.RFmx.BTMX;

public class BluetoothGenerationMeasurement
{
    public static void MeasureBluetoothLe()
    {
        NIRfsg rfsg = null;
        RFmxInstrMX instrSession = null;
        RFmxBTMX bt = null;

        try
        {
            // 1. Initialize RFSG
            rfsg = new NIRfsg("PXI1Slot7", false, false);

            // 2. Generate Bluetooth LE signal
            double centerFrequency = 2.402e9;  // BLE Channel 0
            double outputPower = -10.0;
            double iqRate = 4e6;  // 4 MS/s

            string waveformPath = @"C:\Path\To\BLE_1M_Phy.tdms";
            rfsg.Arb.LoadWaveformFromFileF64(waveformPath, "ble_waveform");

            rfsg.RF.Frequency = centerFrequency;
            rfsg.RF.PowerLevel = outputPower;
            rfsg.Arb.IQRate = iqRate;

            string script = 
                "script bleScript\n" +
                "  repeat forever\n" +
                "    generate ble_waveform\n" +
                "  end repeat\n" +
                "end script";

            rfsg.Arb.Scripting.WriteScript(script);
            rfsg.Arb.Scripting.SelectedScriptName = "bleScript";
            rfsg.RF.OutputEnabled = true;
            rfsg.Initiate();

            Console.WriteLine("RFSG: Generating Bluetooth LE signal at 2.402 GHz");
            System.Threading.Thread.Sleep(100);

            // 3. Initialize RFmx
            instrSession = new RFmxInstrMX("PXI1Slot4", "");
            bt = new RFmxBTMX(instrSession, "");

            // 4. Configure IQPowerEdge Trigger
            bt.SelectMeasurements("", RFmxBTMXMeasurementTypes.TxP | 
                                       RFmxBTMXMeasurementTypes.ModAcc, 
                                       false);

            bt.Triggers.IQPowerEdgeTrigger.Configure("", 
                RFmxBTMXIQPowerEdgeTriggerEnabled.True,
                -25.0,
                RFmxBTMXIQPowerEdgeTriggerSlope.Rising);

            Console.WriteLine("RFmx: Configured IQPowerEdge trigger");

            // 5. Configure BT Measurement
            bt.ConfigureFrequency("", centerFrequency);
            bt.ConfigureReferenceLevel("", 0.0);
            bt.ConfigureSignalType("", RFmxBTMXSignalType.Le);
            bt.ConfigurePayloadLength("", 37);  // LE advertising packet

            bt.TxP.Configuration.ConfigureAveraging("", 
                RFmxBTMXTxPAveragingEnabled.True, 10);

            bt.ModAcc.Configuration.ConfigureAveraging("", 
                RFmxBTMXModAccAveragingEnabled.True, 10);

            Console.WriteLine("RFmx: Configured Bluetooth LE measurements");

            // 6. Initiate and Measure
            bt.Initiate("", "");

            // Fetch TxP
            double avgPower = 0, peakPower = 0;
            bt.TxP.Results.FetchAveragePower("", 10.0, out avgPower, out peakPower);

            // Fetch ModAcc
            double deltaF1Avg = 0, deltaF2Avg = 0, deltaF2Max = 0;
            double freqDriftRate = 0, freqDeviation = 0;

            bt.ModAcc.Results.FetchDeltaF1Average("", 10.0, out deltaF1Avg);
            bt.ModAcc.Results.FetchDeltaF2Average("", 10.0, out deltaF2Avg);
            bt.ModAcc.Results.FetchDeltaF2Maximum("", 10.0, out deltaF2Max);

            Console.WriteLine($"\n=== Bluetooth LE TxP Results ===");
            Console.WriteLine($"Average Power: {avgPower:F2} dBm");
            Console.WriteLine($"Peak Power: {peakPower:F2} dBm");

            Console.WriteLine($"\n=== Bluetooth LE ModAcc Results ===");
            Console.WriteLine($"Delta F1 Average: {deltaF1Avg / 1e3:F3} kHz");
            Console.WriteLine($"Delta F2 Average: {deltaF2Avg / 1e3:F3} kHz");
            Console.WriteLine($"Delta F2 Maximum: {deltaF2Max / 1e3:F3} kHz");

            // Pass/Fail (BLE spec: 225 < ΔF1avg < 275 kHz, ΔF2max < 50 kHz)
            bool deltaF1Pass = deltaF1Avg > 225e3 && deltaF1Avg < 275e3;
            bool deltaF2Pass = Math.Abs(deltaF2Max) < 50e3;
            Console.WriteLine($"\nDelta F1 PASS/FAIL: {(deltaF1Pass ? "PASS" : "FAIL")}");
            Console.WriteLine($"Delta F2 PASS/FAIL: {(deltaF2Pass ? "PASS" : "FAIL")}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex.Message}");
        }
        finally
        {
            if (rfsg != null)
            {
                rfsg.Abort();
                rfsg.RF.OutputEnabled = false;
                rfsg.Dispose();
            }
            bt?.Dispose();
            instrSession?.Dispose();
        }
    }
}
```

---

## Key Patterns for Generation + Measurement

### 1. IQPowerEdge Trigger Configuration

**Always use IQPowerEdge triggering** for reliable signal acquisition:

```csharp
// Pattern for all RFmx personalities
measurement.Triggers.IQPowerEdgeTrigger.Configure(
    triggerSource: "",  // Empty string = auto
    enable: RFmxXXXIQPowerEdgeTriggerEnabled.True,
    level: -20.0,  // Set 5-10 dB below expected signal level
    slope: RFmxXXXIQPowerEdgeTriggerSlope.Rising
);
```

**Why IQPowerEdge?**
- Automatically triggers when signal power crosses threshold
- No external trigger routing required
- Works with pulsed and continuous signals
- Minimal preamble loss
- Robust against noise

### 2. Signal Settling Time

Always wait 50-100ms after starting RFSG generation before initiating measurements:

```csharp
rfsg.Initiate();
System.Threading.Thread.Sleep(100);  // Allow signal to stabilize
instrSession = new RFmxInstrMX(...);  // Then create analyzer session
```

### 3. Waveform Loading vs Generation

**Option A: Load pre-generated waveforms** (Recommended for standards compliance)
```csharp
rfsg.Arb.LoadWaveformFromFileF64(waveformPath, "waveform_name");
```

**Option B: Generate waveforms in code** (For simple test signals)
```csharp
ComplexSingle[] waveform = GenerateTestWaveform();
rfsg.Arb.WriteWaveformComplexF32("waveform_name", waveform);
```

### 4. Continuous vs Triggered Generation

**Continuous (most common for RFmx measurements):**
```csharp
string script = 
    "script myScript\n" +
    "  repeat forever\n" +
    "    generate waveform_name\n" +
    "  end repeat\n" +
    "end script";
```

**Triggered (for burst measurements):**
```csharp
rfsg.Triggers.StartTrigger.DigitalEdge.Source = 
    RfsgDigitalEdgeTriggerSource.PxiTrig0;
rfsg.Triggers.StartTrigger.DigitalEdge.Edge = 
    RfsgDigitalEdgeTriggerEdge.Rising;
```

### 5. Resource Cleanup

Always use try-finally to ensure RFSG output is disabled:

```csharp
try
{
    // Generation and measurement code
}
finally
{
    if (rfsg != null)
    {
        rfsg.Abort();              // Stop generation
        rfsg.RF.OutputEnabled = false;  // Disable RF output
        rfsg.Dispose();            // Close session
    }
    measurement?.Dispose();
    instrSession?.Dispose();
}
```

---

## Common Issues and Solutions

### Issue 1: "Trigger timeout" Error

**Cause**: IQPowerEdge trigger level too high or signal not reaching analyzer

**Solution**:
```csharp
// Lower trigger level (set 10 dB below expected signal)
measurement.Triggers.IQPowerEdgeTrigger.Configure("", 
    RFmxXXXIQPowerEdgeTriggerEnabled.True,
    -30.0,  // Lower threshold
    RFmxXXXIQPowerEdgeTriggerSlope.Rising);

// Increase timeout
measurement.Results.FetchMeasurement("", 30.0, ...);  // 30 second timeout
```

### Issue 2: Poor EVM Due to Timing

**Cause**: Insufficient signal settling time

**Solution**:
```csharp
rfsg.Initiate();
System.Threading.Thread.Sleep(200);  // Increase to 200ms
```

### Issue 3: Waveform File Not Found

**Cause**: Invalid waveform file path

**Solution**:
```csharp
if (!System.IO.File.Exists(waveformPath))
{
    throw new FileNotFoundException($"Waveform file not found: {waveformPath}");
}
rfsg.Arb.LoadWaveformFromFileF64(waveformPath, "waveform_name");
```

---

## Summary: One-Prompt Measurement Pattern

When a user requests a wireless signal measurement, follow this template:

1. **Parse request** → Identify standard (WLAN/LTE/NR/BT), frequency, bandwidth
2. **Initialize RFSG** → Create generator session
3. **Load/Generate waveform** → Use pre-gen file or simple test signal
4. **Configure RFSG** → Set frequency, power, IQ rate
5. **Start generation** → Enable output, initiate, wait 100ms
6. **Initialize RFmx** → Create analyzer session and personality
7. **Configure IQPowerEdge** → Set trigger ~10 dB below signal level
8. **Configure measurement** → Select measurements, set parameters
9. **Initiate & fetch** → Run measurement and retrieve results
10. **Cleanup** → Stop generation, disable output, dispose sessions

This pattern enables **"one-prompt measurement"** workflows where users can request:
- "Measure 802.11ac EVM at 5 GHz"
- "Test LTE 20 MHz signal ACP"
- "Generate and measure 5G NR at 3.5 GHz"

And get complete, working code that generates the signal and measures it.
