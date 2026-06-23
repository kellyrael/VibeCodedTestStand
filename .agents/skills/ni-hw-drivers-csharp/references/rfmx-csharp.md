# RFmx C# API Reference

Complete reference for NI RFmx measurement personalities in C#. RFmx provides pre-configured measurements for wireless standards and RF analysis.

## Namespaces
```csharp
using NationalInstruments.RFmx.InstrMX;          // Hardware session
using NationalInstruments.RFmx.SpecAnMX;         // Spectrum analysis
using NationalInstruments.RFmx.LTEMX;            // LTE measurements
using NationalInstruments.RFmx.NRMX;             // 5G NR measurements
using NationalInstruments.RFmx.WLANMX;           // WLAN (Wi-Fi) measurements
using NationalInstruments.RFmx.BTMX;             // Bluetooth measurements
using NationalInstruments.RFmx.GSMMX;            // GSM measurements
using NationalInstruments.RFmx.WCDMAMX;          // WCDMA measurements
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## Architecture: Two-Session Pattern

RFmx uses a **two-session architecture**:
1. **Instrument session** (`RFmxInstrMX`) - Controls hardware
2. **Measurement session** (personality-specific) - Configures and executes measurements

```csharp
// Step 1: Create instrument session (hardware control)
var instrSession = new RFmxInstrMX("PXI1Slot4", "");

// Step 2: Create measurement personality session
var specAn = new RFmxSpecAnMX(instrSession, "");

// Both sessions must remain open during measurements
```

## RFmxInstrMX (Instrument Session)

### Constructor
```csharp
public RFmxInstrMX(string resourceName, string optionString)

// Parameters:
// - resourceName: "PXI1Slot4", "VST_5842", "Dev1", etc.
// - optionString: "" (empty) or "Simulate=1" for simulation
```

### Key Properties
```csharp
// Frequency reference
instrSession.FrequencyReference.Source      // OnboardClock, RefIn, PxiClock
instrSession.FrequencyReference.Frequency   // Reference frequency (Hz)

// Configuration utilities
instrSession.ConfigureFrequencyReference(source, frequency);
```

## Common Measurement Personalities

---

## 1. RFmxSpecAnMX (Spectrum Analyzer)

General-purpose spectrum analysis measurements.

### Common Measurements
- Spectrum (FFT)
- Adjacent Channel Power (ACP)
- Channel Power
- Occupied Bandwidth (OBW)
- Spurious Emissions
- Harmonics

### Basic Spectrum Measurement

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.SpecAnMX;

using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var specAn = new RFmxSpecAnMX(instrSession, ""))
{
    // Configure frequency and reference level
    specAn.ConfigureFrequency("", 2.45e9);          // 2.45 GHz
    specAn.ConfigureReferenceLevel("", 0.0);         // 0 dBm
    specAn.ConfigureExternalAttenuation("", 0.0);    // No external atten

    // Configure spectrum measurement
    specAn.Spectrum.Configuration.ConfigureSpan("", 100e6);     // 100 MHz span
    specAn.Spectrum.Configuration.ConfigureRbwFilter("", 
        RFmxSpecAnMXSpectrumRbwAutoBandwidth.False, 100e3,      // 100 kHz RBW
        RFmxSpecAnMXSpectrumRbwFilterType.Gaussian);
    specAn.Spectrum.Configuration.ConfigureAveraging("", 
        RFmxSpecAnMXSpectrumAveragingEnabled.True, 10,          // Average 10 sweeps
        RFmxSpecAnMXSpectrumAveragingType.Rms);

    // Initiate measurement
    specAn.Initiate("", "");

    // Fetch spectrum data
    double[] spectrum = null;
    SpecAnMXSpectrumTrace spectrumTrace = null;
    specAn.Spectrum.Results.FetchSpectrum("", 10.0, 
        ref spectrum, ref spectrumTrace);

    Console.WriteLine($"Spectrum points: {spectrum.Length}");
    Console.WriteLine($"Start frequency: {spectrumTrace.X0 / 1e9:F6} GHz");
    Console.WriteLine($"Frequency step: {spectrumTrace.DeltaX / 1e3:F3} kHz");

    // Find peak
    int peakIndex = Array.IndexOf(spectrum, spectrum.Max());
    double peakFreq = spectrumTrace.X0 + peakIndex * spectrumTrace.DeltaX;
    Console.WriteLine($"Peak: {spectrum[peakIndex]:F2} dBm at {peakFreq / 1e9:F6} GHz");
}
```

### Channel Power Measurement

```csharp
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var specAn = new RFmxSpecAnMX(instrSession, ""))
{
    specAn.ConfigureFrequency("", 2.45e9);
    specAn.ConfigureReferenceLevel("", 0.0);

    // Configure channel power
    specAn.CHP.Configuration.ConfigureMeasurementInterval("", 20e6);  // 20 MHz channel
    specAn.CHP.Configuration.ConfigureRbwFilter("", 
        RFmxSpecAnMXCHPRbwAutoBandwidth.False, 100e3,
        RFmxSpecAnMXCHPRbwFilterType.Gaussian);
    specAn.CHP.Configuration.ConfigureAveraging("", 
        RFmxSpecAnMXCHPAveragingEnabled.True, 10, 
        RFmxSpecAnMXCHPAveragingType.Rms);

    specAn.Initiate("", "");

    // Fetch channel power
    double channelPower = 0;
    double peakPower = 0;
    specAn.CHP.Results.FetchMeasurement("", 10.0, 
        ref channelPower, ref peakPower);

    Console.WriteLine($"Channel Power: {channelPower:F2} dBm");
    Console.WriteLine($"Peak Power: {peakPower:F2} dBm");
}
```

### Adjacent Channel Power (ACP)

```csharp
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var specAn = new RFmxSpecAnMX(instrSession, ""))
{
    specAn.ConfigureFrequency("", 2.45e9);
    specAn.ConfigureReferenceLevel("", 10.0);

    // Configure ACP
    specAn.ACP.Configuration.ConfigureNumberOfCarriers("", 1);
    specAn.ACP.Configuration.ConfigureCarrierBandwidth("", "", 20e6);  // 20 MHz carrier

    // Configure offset channels (±1 channel)
    specAn.ACP.Configuration.ConfigureNumberOfOffsets("", 2);  // Lower and upper
    specAn.ACP.Configuration.ConfigureOffsetFrequency("", "", 0, 25e6);   // +25 MHz
    specAn.ACP.Configuration.ConfigureOffsetFrequency("", "", 1, -25e6);  // -25 MHz
    specAn.ACP.Configuration.ConfigureOffsetBandwidth("", "", 0, 20e6);
    specAn.ACP.Configuration.ConfigureOffsetBandwidth("", "", 1, 20e6);

    specAn.ACP.Configuration.ConfigureAveraging("", 
        RFmxSpecAnMXACPAveragingEnabled.True, 10, 
        RFmxSpecAnMXACPAveragingType.Rms);

    specAn.Initiate("", "");

    // Fetch ACP results
    double carrierPower = 0;
    double[] lowerOffsetPower = new double[2];
    double[] upperOffsetPower = new double[2];

    specAn.ACP.Results.FetchCarrierMeasurement("", 10.0, 0, ref carrierPower);
    specAn.ACP.Results.FetchOffsetMeasurementArray("", 10.0, 
        ref lowerOffsetPower, ref upperOffsetPower);

    Console.WriteLine($"Carrier Power: {carrierPower:F2} dBm");
    Console.WriteLine($"Lower Adjacent: {lowerOffsetPower[0]:F2} dBm ({lowerOffsetPower[0] - carrierPower:F2} dBc)");
    Console.WriteLine($"Upper Adjacent: {upperOffsetPower[0]:F2} dBm ({upperOffsetPower[0] - carrierPower:F2} dBc)");
}
```

---

## 2. RFmxLTEMX (LTE Measurements)

LTE (4G) signal measurements and analysis.

### Common Measurements
- ModAcc (EVM, frequency error, IQ offset)
- ACP (Adjacent channel power)
- SEM (Spectrum emission mask)
- PAVT (Power vs time)

### LTE ModAcc (EVM) Measurement

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.LTEMX;

using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var lte = new RFmxLTEMX(instrSession, ""))
{
    // Configure standard parameters
    lte.ConfigureFrequency("", 2.14e9);                          // Band 1 DL
    lte.ConfigureReferenceLevel("", 0.0);
    lte.ConfigureExternalAttenuation("", 0.0);

    // Configure LTE signal
    lte.ComponentCarrier.SetBandwidth("", 20e6);                  // 20 MHz BW
    lte.ComponentCarrier.SetCellID("", 0);

    // Downlink configuration
    lte.SetDownlinkTestModel("", RFmxLTEMXDownlinkTestModel.TM1_1);
    lte.SetLinkDirection("", RFmxLTEMXLinkDirection.Downlink);

    // Configure ModAcc
    lte.ModAcc.Configuration.ConfigureAveraging("", 
        RFmxLTEMXModAccAveragingEnabled.True, 10);

    // Select measurements
    lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ModAcc, false);

    // Initiate
    lte.Initiate("", "");

    // Fetch ModAcc results
    double compositeRmsEvm = 0;
    double compositePeakEvm = 0;
    double frequencyError = 0;

    lte.ModAcc.Results.FetchCompositeEVM("", 10.0, 
        ref compositeRmsEvm, ref compositePeakEvm);
    lte.ModAcc.Results.FetchFrequencyError("", 10.0, ref frequencyError);

    Console.WriteLine($"RMS EVM: {compositeRmsEvm:F3} %");
    Console.WriteLine($"Peak EVM: {compositePeakEvm:F3} %");
    Console.WriteLine($"Frequency Error: {frequencyError:F3} Hz");

    // Check against limits
    if (compositeRmsEvm < 8.0)  // 8% limit for 64QAM
    {
        Console.WriteLine("PASS: EVM within spec");
    }
    else
    {
        Console.WriteLine("FAIL: EVM exceeds spec");
    }
}
```

### LTE ACP Measurement

```csharp
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var lte = new RFmxLTEMX(instrSession, ""))
{
    lte.ConfigureFrequency("", 2.14e9);
    lte.ConfigureReferenceLevel("", 10.0);
    lte.ComponentCarrier.SetBandwidth("", 20e6);
    lte.SetLinkDirection("", RFmxLTEMXLinkDirection.Downlink);

    // Configure ACP for LTE (uses E-UTRA offsets)
    lte.ACP.Configuration.ConfigureMeasurementMethod("", 
        RFmxLTEMXACPMeasurementMethod.Normal);
    lte.ACP.Configuration.ConfigureAveraging("", 
        RFmxLTEMXACPAveragingEnabled.True, 10);

    lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ACP, false);
    lte.Initiate("", "");

    // Fetch E-UTRA ACP results
    double[] lowerRelativePower = null;
    double[] upperRelativePower = null;
    double[] lowerAbsolutePower = null;
    double[] upperAbsolutePower = null;

    lte.ACP.Results.FetchOffsetMeasurementArray("", 10.0, 
        ref lowerRelativePower, ref upperRelativePower,
        ref lowerAbsolutePower, ref upperAbsolutePower);

    Console.WriteLine("E-UTRA ACP Results:");
    for (int i = 0; i < lowerRelativePower.Length; i++)
    {
        Console.WriteLine($"  Offset {i}: Lower={lowerRelativePower[i]:F2} dBc, Upper={upperRelativePower[i]:F2} dBc");
    }
}
```

---

## 3. RFmxNRMX (5G NR Measurements)

5G New Radio signal measurements.

### 5G NR ModAcc (EVM) Measurement

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.NRMX;

using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var nr = new RFmxNRMX(instrSession, ""))
{
    // Configure 5G NR signal
    nr.ConfigureFrequency("", 3.5e9);                    // n78 band (3.5 GHz)
    nr.ConfigureReferenceLevel("", 0.0);

    // Configure component carrier
    nr.ComponentCarrier.SetBandwidth("", 100e6);         // 100 MHz BW
    nr.ComponentCarrier.SetCellID("", 0);
    nr.SetFrequencyRange("", RFmxNRMXFrequencyRange.Range1);  // FR1 (< 6 GHz)

    // Downlink configuration
    nr.SetLinkDirection("", RFmxNRMXLinkDirection.Downlink);

    // Configure PDSCH (Physical Downlink Shared Channel)
    nr.ComponentCarrier.SetPuschTransformPrecodingEnabled("", 
        RFmxNRMXComponentCarrierPuschTransformPrecodingEnabled.False);

    // ModAcc configuration
    nr.ModAcc.Configuration.ConfigureAveraging("", 
        RFmxNRMXModAccAveragingEnabled.True, 10, 
        RFmxNRMXModAccAveragingType.Rms);

    nr.SelectMeasurements("", RFmxNRMXMeasurementTypes.ModAcc, false);
    nr.Initiate("", "");

    // Fetch results
    double compositeRmsEvm = 0;
    double compositePeakEvm = 0;
    double frequencyError = 0;

    nr.ModAcc.Results.FetchCompositeEVM("", 10.0, 
        ref compositeRmsEvm, ref compositePeakEvm);
    nr.ModAcc.Results.FetchFrequencyError("", 10.0, ref frequencyError);

    Console.WriteLine("5G NR ModAcc Results:");
    Console.WriteLine($"  RMS EVM: {compositeRmsEvm:F3} %");
    Console.WriteLine($"  Peak EVM: {compositePeakEvm:F3} %");
    Console.WriteLine($"  Frequency Error: {frequencyError / 1e3:F3} kHz");
}
```

---

## 4. RFmxWLANMX (Wi-Fi Measurements)

WLAN (802.11a/b/g/n/ac/ax) measurements.

### WLAN OFDM ModAcc (802.11ac Example)

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.WLANMX;

using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var wlan = new RFmxWLANMX(instrSession, ""))
{
    // Configure for 802.11ac
    wlan.ConfigureFrequency("", 5.18e9);                 // Channel 36 (5 GHz)
    wlan.ConfigureReferenceLevel("", 0.0);

    // Configure standard and channel bandwidth
    wlan.ConfigureStandard("", RFmxWLANMXStandard.Standard802_11ac);
    wlan.ConfigureChannelBandwidth("", 80e6);            // 80 MHz channel

    // Configure OFDM ModAcc
    wlan.OFDM ModAcc.Configuration.ConfigureAveraging("", 
        RFmxWLANMXOFDMModAccAveragingEnabled.True, 10);
    wlan.OFDMModAcc.Configuration.ConfigureMeasurementLength("", 16);  // 16 symbols

    wlan.SelectMeasurements("", RFmxWLANMXMeasurementTypes.OFDMModAcc, false);
    wlan.Initiate("", "");

    // Fetch OFDM ModAcc results
    double compositeRmsEvmMean = 0;
    double compositeDataRmsEvmMean = 0;
    double compositePilotRmsEvmMean = 0;

    wlan.OFDMModAcc.Results.FetchCompositeRMSEVMMean("", 10.0, 
        ref compositeRmsEvmMean, ref compositeDataRmsEvmMean, 
        ref compositePilotRmsEvmMean);

    // Fetch additional results
    double frequencyErrorMean = 0;
    double symbolClockErrorMean = 0;
    wlan.OFDMModAcc.Results.FetchFrequencyErrorMean("", 10.0, ref frequencyErrorMean);
    wlan.OFDMModAcc.Results.FetchSymbolClockErrorMean("", 10.0, ref symbolClockErrorMean);

    Console.WriteLine("802.11ac OFDM ModAcc Results:");
    Console.WriteLine($"  Composite RMS EVM: {compositeRmsEvmMean:F3} dB");
    Console.WriteLine($"  Data RMS EVM: {compositeDataRmsEvmMean:F3} dB");
    Console.WriteLine($"  Pilot RMS EVM: {compositePilotRmsEvmMean:F3} dB");
    Console.WriteLine($"  Frequency Error: {frequencyErrorMean / 1e3:F3} kHz");
    Console.WriteLine($"  Symbol Clock Error: {symbolClockErrorMean:F3} ppm");
}
```

### WLAN TxP (Transmit Power) Measurement

```csharp
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var wlan = new RFmxWLANMX(instrSession, ""))
{
    wlan.ConfigureFrequency("", 2.437e9);                // Channel 6 (2.4 GHz)
    wlan.ConfigureReferenceLevel("", 10.0);
    wlan.ConfigureStandard("", RFmxWLANMXStandard.Standard802_11n);
    wlan.ConfigureChannelBandwidth("", 20e6);

    // Configure TxP
    wlan.TxP.Configuration.ConfigureAveraging("", 
        RFmxWLANMXTxPAveragingEnabled.True, 10);
    wlan.TxP.Configuration.ConfigureMaximumMeasurementInterval("", 0.001);  // 1 ms

    wlan.SelectMeasurements("", RFmxWLANMXMeasurementTypes.TxP, false);
    wlan.Initiate("", "");

    // Fetch transmit power
    double averagePowerMean = 0;
    double peakPowerMaximum = 0;

    wlan.TxP.Results.FetchAveragePowerMean("", 10.0, ref averagePowerMean);
    wlan.TxP.Results.FetchPeakPowerMaximum("", 10.0, ref peakPowerMaximum);

    Console.WriteLine($"Average Power: {averagePowerMean:F2} dBm");
    Console.WriteLine($"Peak Power: {peakPowerMaximum:F2} dBm");
}
```

---

## 5. RFmxBTMX (Bluetooth Measurements)

Bluetooth (Classic and LE) measurements.

### Bluetooth LE ModAcc

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.BTMX;

using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var bt = new RFmxBTMX(instrSession, ""))
{
    // Configure for Bluetooth LE
    bt.ConfigureFrequency("", 2.402e9);                  // Channel 0
    bt.ConfigureReferenceLevel("", 0.0);
    bt.ConfigureStandard("", RFmxBTMXStandard.LE);

    // Configure LE parameters
    bt.ConfigurePayloadLength("", 37);                    // LE advertising packet
    bt.ConfigurePayloadType("", RFmxBTMXPayloadType.PRBS9);

    // ModAcc configuration
    bt.ModAcc.Configuration.ConfigureAveraging("", 
        RFmxBTMXModAccAveragingEnabled.True, 100);       // Average 100 packets

    bt.SelectMeasurements("", RFmxBTMXMeasurementTypes.ModAcc, false);
    bt.Initiate("", "");

    // Fetch Bluetooth LE ModAcc results
    double deltaF1Average = 0;
    double deltaF2Max = 0;
    double deltaF2Average = 0;
    double frequencyError = 0;
    double frequencyDrift = 0;

    bt.ModAcc.Results.FetchDeltaF1Average("", 10.0, ref deltaF1Average);
    bt.ModAcc.Results.FetchDeltaF2Maximum("", 10.0, ref deltaF2Max);
    bt.ModAcc.Results.FetchFrequencyError("", 10.0, ref frequencyError);
    bt.ModAcc.Results.FetchFrequencyDrift("", 10.0, ref frequencyDrift);

    Console.WriteLine("Bluetooth LE ModAcc Results:");
    Console.WriteLine($"  ΔF1 Average: {deltaF1Average / 1e3:F3} kHz");
    Console.WriteLine($"  ΔF2 Max: {deltaF2Max / 1e3:F3} kHz");
    Console.WriteLine($"  Frequency Error: {frequencyError / 1e3:F3} kHz");
    Console.WriteLine($"  Frequency Drift: {frequencyDrift / 1e3:F3} kHz");

    // Bluetooth LE spec limits
    bool passF1 = (deltaF1Average >= 225e3 && deltaF1Average <= 275e3);
    bool passF2 = (deltaF2Max >= 185e3 && deltaF2Max <= 315e3);

    Console.WriteLine($"  ΔF1 spec (225-275 kHz): {(passF1 ? "PASS" : "FAIL")}");
    Console.WriteLine($"  ΔF2 spec (185-315 kHz): {(passF2 ? "PASS" : "FAIL")}");
}
```

---

## Multi-Signal and Multi-Measurement Patterns

### Parallel Measurements (Multiple Measurement Types)

```csharp
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var lte = new RFmxLTEMX(instrSession, ""))
{
    // Configure signal
    lte.ConfigureFrequency("", 2.14e9);
    lte.ConfigureReferenceLevel("", 0.0);
    lte.ComponentCarrier.SetBandwidth("", 20e6);
    lte.SetLinkDirection("", RFmxLTEMXLinkDirection.Downlink);

    // Select multiple measurements (bitwise OR)
    lte.SelectMeasurements("", 
        RFmxLTEMXMeasurementTypes.ModAcc | 
        RFmxLTEMXMeasurementTypes.ACP | 
        RFmxLTEMXMeasurementTypes.CHP, 
        false);

    // Single initiate runs all selected measurements
    lte.Initiate("", "");

    // Fetch each measurement's results independently

    // ModAcc
    double rmsEvm = 0, peakEvm = 0;
    lte.ModAcc.Results.FetchCompositeEVM("", 10.0, ref rmsEvm, ref peakEvm);
    Console.WriteLine($"ModAcc - RMS EVM: {rmsEvm:F3}%");

    // ACP
    double[] lowerAcp = null, upperAcp = null, lowerAbs = null, upperAbs = null;
    lte.ACP.Results.FetchOffsetMeasurementArray("", 10.0, 
        ref lowerAcp, ref upperAcp, ref lowerAbs, ref upperAbs);
    Console.WriteLine($"ACP - Lower: {lowerAcp[0]:F2} dBc");

    // CHP
    double chPower = 0;
    lte.CHP.Results.FetchMeasurement("", 10.0, ref chPower);
    Console.WriteLine($"CHP: {chPower:F2} dBm");
}
```

### Sequential Signal Analysis (Multi-Standard)

```csharp
// Measure both LTE and 5G NR on same hardware
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
{
    // LTE measurement
    using (var lte = new RFmxLTEMX(instrSession, ""))
    {
        lte.ConfigureFrequency("", 2.14e9);
        lte.ConfigureReferenceLevel("", 0.0);
        lte.ComponentCarrier.SetBandwidth("", 20e6);
        lte.SetLinkDirection("", RFmxLTEMXLinkDirection.Downlink);

        lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ModAcc, false);
        lte.Initiate("", "");

        double lteEvm = 0, temp = 0;
        lte.ModAcc.Results.FetchCompositeEVM("", 10.0, ref lteEvm, ref temp);
        Console.WriteLine($"LTE EVM: {lteEvm:F3}%");
    }

    // 5G NR measurement (reuse instrument session)
    using (var nr = new RFmxNRMX(instrSession, ""))
    {
        nr.ConfigureFrequency("", 3.5e9);
        nr.ConfigureReferenceLevel("", 0.0);
        nr.ComponentCarrier.SetBandwidth("", 100e6);
        nr.SetLinkDirection("", RFmxNRMXLinkDirection.Downlink);

        nr.SelectMeasurements("", RFmxNRMXMeasurementTypes.ModAcc, false);
        nr.Initiate("", "");

        double nrEvm = 0, temp = 0;
        nr.ModAcc.Results.FetchCompositeEVM("", 10.0, ref nrEvm, ref temp);
        Console.WriteLine($"5G NR EVM: {nrEvm:F3}%");
    }
}
```

---

## Common Patterns

### Reusable Configuration

```csharp
// Configure once, measure many times
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var lte = new RFmxLTEMX(instrSession, ""))
{
    // One-time configuration
    lte.ConfigureFrequency("", 2.14e9);
    lte.ConfigureReferenceLevel("", 0.0);
    lte.ComponentCarrier.SetBandwidth("", 20e6);
    lte.SetLinkDirection("", RFmxLTEMXLinkDirection.Downlink);
    lte.ModAcc.Configuration.ConfigureAveraging("", 
        RFmxLTEMXModAccAveragingEnabled.True, 10);
    lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ModAcc, false);

    // Repeated measurements (fast loop)
    for (int i = 0; i < 100; i++)
    {
        lte.Initiate("", "");

        double rmsEvm = 0, peakEvm = 0;
        lte.ModAcc.Results.FetchCompositeEVM("", 10.0, ref rmsEvm, ref peakEvm);

        Console.WriteLine($"Iteration {i}: EVM={rmsEvm:F3}%");

        // Optional: brief delay between measurements
        System.Threading.Thread.Sleep(10);
    }
}
```

### Error Handling

```csharp
using (var instrSession = new RFmxInstrMX("PXI1Slot4", ""))
using (var lte = new RFmxLTEMX(instrSession, ""))
{
    try
    {
        lte.ConfigureFrequency("", 2.14e9);
        lte.ComponentCarrier.SetBandwidth("", 20e6);
        lte.SelectMeasurements("", RFmxLTEMXMeasurementTypes.ModAcc, false);

        lte.Initiate("", "");

        double rmsEvm = 0, peakEvm = 0;
        lte.ModAcc.Results.FetchCompositeEVM("", 10.0, ref rmsEvm, ref peakEvm);

        Console.WriteLine($"EVM: {rmsEvm:F3}%");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"RFmx Error: {ex.Message}");

        // Optionally reset to known state
        lte.ResetToDefault("");
    }
}
```

---

## Performance Tips

1. **Reuse instrument sessions** - Create once, use for multiple measurements
2. **Select multiple measurements** - RFmx can run many in one acquisition
3. **Appropriate averaging** - Balance speed vs accuracy (10-100 averages typical)
4. **Pre-configure everything** - Set all parameters before Initiate()
5. **Use ResetToDefault() sparingly** - Only when necessary (slow operation)

## Common Errors

### Error: Signal Not Found
```csharp
// WRONG: Reference level too low, signal below noise floor
lte.ConfigureReferenceLevel("", -40.0);  // Too low!

// CORRECT: Reference level near expected signal power
lte.ConfigureReferenceLevel("", 0.0);    // Adjust to actual signal
```

### Error: Timeout on Fetch
```csharp
// WRONG: Timeout too short for averaging count
lte.ModAcc.Configuration.ConfigureAveraging("", true, 1000);  // 1000 averages
lte.ModAcc.Results.FetchCompositeEVM("", 1.0, ref evm, ref peakEvm);  // Only 1s timeout

// CORRECT: Timeout >> measurement time
lte.ModAcc.Results.FetchCompositeEVM("", 60.0, ref evm, ref peakEvm);  // 60s timeout
```

## Supported Personalities

- **RFmxSpecAnMX**: Spectrum, ACP, CHP, OBW, SEM, Harmonics, Spurious
- **RFmxLTEMX**: LTE FDD/TDD, all bandwidths, ModAcc, ACP, SEM, PAVT
- **RFmxNRMX**: 5G NR FR1/FR2, ModAcc, ACP, SEM, TxP
- **RFmxWLANMX**: 802.11 a/b/g/n/ac/ax, ModAcc, TxP, SEM
- **RFmxBTMX**: Bluetooth Classic/LE, ModAcc, ACP, TxP
- **RFmxGSMMX**: GSM/EDGE, ModAcc, ORFS, TxP
- **RFmxWCDMAMX**: WCDMA/HSPA, ModAcc, ACP, SEM
- **RFmxPulseMX**: Pulse radar, timing, power
- **RFmxDemodMX**: AM/FM analog demodulation

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [RFSA/RFSG Reference](./rfsa-rfsg-csharp.md)
- [RFmx Generation + Measurement Workflows](./rfmx-generation-measurement-workflows.md) — complete LTE, 5G NR, and multi-standard worked examples
