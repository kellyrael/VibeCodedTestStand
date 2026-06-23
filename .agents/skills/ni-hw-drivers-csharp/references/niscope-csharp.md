# NI-SCOPE C# API Reference

Complete reference for NI Digitizers and Oscilloscopes (NI-SCOPE) in C#.

## Namespace
```csharp
using NationalInstruments.ModularInstruments.NIScope;
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## Session Class

```csharp
// Constructor
public NIScope(string resourceName, bool idQuery, bool resetDevice)

// Parameters:
// - resourceName: "PXI1Slot5", "SCOPE1", "Dev1", etc.
// - idQuery: false (recommended)
// - resetDevice: false (recommended)
```

## Key Enumerations

### Acquisition Type
```csharp
ScopeAcquisitionType.Normal              // Normal acquisition
ScopeAcquisitionType.Flexres             // Flexible resolution (averaging for higher resolution)
ScopeAcquisitionType.DDC                 // Digital downconversion
```

### Vertical Coupling
```csharp
ScopeVerticalCoupling.AC                 // AC coupling (blocks DC)
ScopeVerticalCoupling.DC                 // DC coupling (full bandwidth)
ScopeVerticalCoupling.Ground             // Ground (0V reference)
```

### Trigger Type
```csharp
ScopeTriggerType.Edge                    // Edge trigger
ScopeTriggerType.Hysteresis              // Hysteresis trigger (noise rejection)
ScopeTriggerType.Digital                 // Digital pattern trigger
ScopeTriggerType.Window                  // Window trigger
ScopeTriggerType.Software                // Software trigger
ScopeTriggerType.Immediate               // No trigger (free-run)
```

### Trigger Slope
```csharp
ScopeTriggerSlope.Positive               // Rising edge
ScopeTriggerSlope.Negative               // Falling edge
```

### Trigger Coupling
```csharp
ScopeTriggerCoupling.AC                  // AC coupled (blocks DC)
ScopeTriggerCoupling.DC                  // DC coupled
ScopeTriggerCoupling.HFReject            // High-frequency reject
ScopeTriggerCoupling.LFReject            // Low-frequency reject
```

### Reference Position
```csharp
ScopeReferencePosition.Start             // Trigger at start (0%)
ScopeReferencePosition.Center            // Trigger at center (50%)
ScopeReferencePosition.End               // Trigger at end (100%)
```

## Property Hierarchy

### Acquisition Configuration
```csharp
// Channels
session.Channels["0"]                          // Access channel 0
session.Channels["0,1"]                        // Multiple channels

// Vertical (voltage) settings
session.Channels["0"].Configure(range: 10.0,   // Voltage range (±5V)
                                offset: 0.0,   // DC offset
                                coupling: ScopeVerticalCoupling.DC,
                                probeAttenuation: 1.0,
                                enabled: true);

// Horizontal (timing) settings
session.Acquisition.ConfigureHorizontalTiming(
    sampleRate: 100e6,                         // 100 MS/s
    numberOfPointsPerRecord: 10000,            // 10k samples
    referencePosition: 50.0,                   // Trigger at 50% (center)
    numberOfRecords: 1,                        // Single acquisition
    enforceRealtime: true);
```

### Triggering
```csharp
// Edge trigger
session.Trigger.ConfigureTriggerEdge(
    triggerSource: "0",                        // Channel 0 as trigger source
    level: 0.0,                                // 0V trigger level
    triggerCoupling: ScopeTriggerCoupling.DC,
    slope: ScopeTriggerSlope.Positive,
    triggerHoldoff: 0.0,                       // No holdoff
    triggerDelay: 0.0);                        // No delay
```

## Common Workflows

### 1. Simple Single-Shot Acquisition

```csharp
using NationalInstruments.ModularInstruments.NIScope;

using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel 0
    scope.Channels["0"].Configure(
        range: 10.0,                           // ±5V
        offset: 0.0,
        coupling: ScopeVerticalCoupling.DC,
        probeAttenuation: 1.0,
        enabled: true
    );

    // Configure horizontal timing
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,                     // 100 MS/s
        numberOfPointsPerRecord: 10000,        // 10k samples = 100µs
        referencePosition: 50.0,               // Trigger at center
        numberOfRecords: 1,
        enforceRealtime: true
    );

    // Configure edge trigger on channel 0
    scope.Trigger.ConfigureTriggerEdge(
        triggerSource: "0",
        level: 0.0,                            // 0V threshold
        triggerCoupling: ScopeTriggerCoupling.DC,
        slope: ScopeTriggerSlope.Positive,     // Rising edge
        triggerHoldoff: 0.0,
        triggerDelay: 0.0
    );

    // Initiate acquisition
    scope.Measurement.Initiate();

    // Fetch waveform
    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5)
    );

    Console.WriteLine($"Acquired {waveforms[0].SampleCount} samples");

    // Convert to voltages
    double[] voltages = new double[waveforms[0].SampleCount];
    for (int i = 0; i < waveforms[0].SampleCount; i++)
    {
        voltages[i] = waveforms[0].GetScaledValue(i);
    }

    // Analyze
    double vMax = voltages.Max();
    double vMin = voltages.Min();
    double vPkPk = vMax - vMin;

    Console.WriteLine($"Vmax: {vMax:F3} V");
    Console.WriteLine($"Vmin: {vMin:F3} V");
    Console.WriteLine($"Vpp: {vPkPk:F3} V");
}
```

### 2. Continuous Acquisition (Multi-Record)

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);

    // Configure for multiple records
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,
        numberOfPointsPerRecord: 1000,         // 1k samples per record
        referencePosition: 50.0,
        numberOfRecords: 100,                  // 100 acquisitions
        enforceRealtime: true
    );

    // Edge trigger
    scope.Trigger.ConfigureTriggerEdge("0", 0.0, ScopeTriggerCoupling.DC, 
                                      ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    // Fetch all records
    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(10)
    );

    Console.WriteLine($"Acquired {waveforms.Length} records");

    // Process each record
    for (int record = 0; record < waveforms.Length; record++)
    {
        double[] voltages = new double[waveforms[record].SampleCount];
        for (int i = 0; i < waveforms[record].SampleCount; i++)
        {
            voltages[i] = waveforms[record].GetScaledValue(i);
        }

        double vPkPk = voltages.Max() - voltages.Min();
        Console.WriteLine($"Record {record}: Vpp = {vPkPk:F3} V");
    }
}
```

### 3. Multi-Channel Acquisition

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channels 0 and 1
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);
    scope.Channels["1"].Configure(5.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);

    // Configure timing
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,
        numberOfPointsPerRecord: 10000,
        referencePosition: 50.0,
        numberOfRecords: 1,
        enforceRealtime: true
    );

    // Trigger on channel 0
    scope.Trigger.ConfigureTriggerEdge("0", 0.0, ScopeTriggerCoupling.DC, 
                                      ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    // Fetch both channels
    ScopeWaveform<short>[] waveforms0 = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5));
    ScopeWaveform<short>[] waveforms1 = scope.Channels["1"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5));

    Console.WriteLine($"CH0: {waveforms0[0].SampleCount} samples");
    Console.WriteLine($"CH1: {waveforms1[0].SampleCount} samples");

    // Analyze phase relationship, etc.
    AnalyzePhase(waveforms0[0], waveforms1[0]);
}
```

### 4. High-Speed Streaming (Fetch Available)

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);

    // Configure for continuous acquisition
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,
        numberOfPointsPerRecord: 1000000,      // 1M samples (10ms @ 100MS/s)
        referencePosition: 0.0,                // Start immediately
        numberOfRecords: -1,                   // Continuous
        enforceRealtime: true
    );

    // Immediate trigger (free-run)
    scope.Trigger.Type = ScopeTriggerType.Immediate;

    scope.Measurement.Initiate();

    // Continuous fetch loop
    int totalSamples = 0;
    DateTime startTime = DateTime.Now;

    while (totalSamples < 10000000)  // Acquire 10M samples
    {
        // Fetch available data (non-blocking when data ready)
        ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchArrayInt16(
            numberOfSamples: 100000,           // Fetch 100k at a time
            timeout: TimeSpan.FromSeconds(1)
        );

        totalSamples += waveforms[0].SampleCount;

        // Process data in real-time
        ProcessWaveformData(waveforms[0]);

        Console.Write($"\rAcquired: {totalSamples / 1e6:F2} M samples");
    }

    scope.Measurement.Abort();

    TimeSpan elapsed = DateTime.Now - startTime;
    Console.WriteLine($"\nTotal time: {elapsed.TotalSeconds:F2} s");
    Console.WriteLine($"Throughput: {totalSamples / elapsed.TotalSeconds / 1e6:F2} MS/s");
}
```

### 5. Flexible Resolution (Averaging)

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);

    // Enable Flexible Resolution (increases effective resolution via averaging)
    scope.Acquisition.Type = ScopeAcquisitionType.Flexres;
    scope.Acquisition.FlexResolutionConfig.Enabled = true;
    scope.Acquisition.FlexResolutionConfig.NumberOfAverages = 16;  // 16x averaging

    // Configure timing
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,
        numberOfPointsPerRecord: 10000,
        referencePosition: 50.0,
        numberOfRecords: 1,
        enforceRealtime: true
    );

    // Trigger
    scope.Trigger.ConfigureTriggerEdge("0", 0.0, ScopeTriggerCoupling.DC, 
                                      ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    // Fetch averaged waveform (higher resolution, lower noise)
    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5));

    Console.WriteLine("Flexible Resolution Acquisition Complete");
    Console.WriteLine($"Effective resolution increased by ~{Math.Log(16, 2):F1} bits");
}
```

### 6. AC Coupling with High-Frequency Signal

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel with AC coupling (removes DC offset)
    scope.Channels["0"].Configure(
        range: 1.0,                            // ±500mV (for small AC signal)
        offset: 0.0,
        coupling: ScopeVerticalCoupling.AC,    // AC coupling
        probeAttenuation: 1.0,
        enabled: true
    );

    // High sample rate for high-frequency signal
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 1e9,                       // 1 GS/s (for 100 MHz signal)
        numberOfPointsPerRecord: 10000,
        referencePosition: 50.0,
        numberOfRecords: 1,
        enforceRealtime: true
    );

    // Trigger
    scope.Trigger.ConfigureTriggerEdge("0", 0.0, 
        ScopeTriggerCoupling.HFReject,         // Reject high-freq noise on trigger
        ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5));

    // Measure frequency via zero crossings
    double frequency = MeasureFrequency(waveforms[0]);
    Console.WriteLine($"Measured Frequency: {frequency / 1e6:F3} MHz");
}
```

### 7. External Trigger with Delay

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);

    // Configure timing
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,
        numberOfPointsPerRecord: 10000,
        referencePosition: 20.0,               // Trigger at 20% (see pre-trigger)
        numberOfRecords: 1,
        enforceRealtime: true
    );

    // External trigger with delay
    scope.Trigger.ConfigureTriggerEdge(
        triggerSource: "VAL_RTSI_0",           // External trigger (RTSI or PFI)
        level: 2.0,                            // TTL threshold
        triggerCoupling: ScopeTriggerCoupling.DC,
        slope: ScopeTriggerSlope.Positive,
        triggerHoldoff: 0.0,
        triggerDelay: 0.001                    // 1ms delay after trigger
    );

    scope.Measurement.Initiate();

    Console.WriteLine("Waiting for external trigger...");

    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(30)      // Long timeout for manual trigger
    );

    Console.WriteLine("Triggered and acquired");
}
```

### 8. Waveform Measurements (Built-in)

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure and acquire (as before)
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.DC, 1.0, true);
    scope.Acquisition.ConfigureHorizontalTiming(100e6, 10000, 50.0, 1, true);
    scope.Trigger.ConfigureTriggerEdge("0", 0.0, ScopeTriggerCoupling.DC, 
                                      ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5));

    // Use built-in measurement functions
    ScopeWaveformMeasurement measurement = new ScopeWaveformMeasurement();

    double vPeakToPeak = measurement.MeasureWaveform(
        waveforms[0], 
        ScopeWaveformMeasurementFunction.VoltagePeakToPeak);

    double frequency = measurement.MeasureWaveform(
        waveforms[0], 
        ScopeWaveformMeasurementFunction.Frequency);

    double vRms = measurement.MeasureWaveform(
        waveforms[0], 
        ScopeWaveformMeasurementFunction.VoltageRms);

    Console.WriteLine($"Vpp: {vPeakToPeak:F3} V");
    Console.WriteLine($"Frequency: {frequency / 1e3:F3} kHz");
    Console.WriteLine($"Vrms: {vRms:F3} V");
}
```

### 9. Probe Compensation (10X Probe)

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure for 10X probe
    scope.Channels["0"].Configure(
        range: 100.0,                          // ±50V range (with 10X probe)
        offset: 0.0,
        coupling: ScopeVerticalCoupling.DC,
        probeAttenuation: 10.0,                // 10X probe
        enabled: true
    );

    // Timing
    scope.Acquisition.ConfigureHorizontalTiming(100e6, 10000, 50.0, 1, true);

    // Trigger
    scope.Trigger.ConfigureTriggerEdge("0", 5.0,  // 5V trigger (actual voltage)
        ScopeTriggerCoupling.DC, ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
        timeout: TimeSpan.FromSeconds(5));

    // GetScaledValue() automatically accounts for probe attenuation
    double actualVoltage = waveforms[0].GetScaledValue(0);
    Console.WriteLine($"Actual voltage: {actualVoltage:F3} V (compensated for 10X probe)");
}
```

### 10. Digital Downconversion (DDC) for Narrow Band Analysis

```csharp
using (var scope = new NIScope("PXI1Slot5", false, false))
{
    // Configure channel
    scope.Channels["0"].Configure(10.0, 0.0, ScopeVerticalCoupling.AC, 1.0, true);

    // Enable DDC (if supported by hardware, e.g., PXIe-5164)
    scope.Acquisition.Type = ScopeAcquisitionType.DDC;

    // Configure DDC parameters
    scope.Acquisition.DDCConfig.CenterFrequency = 10e6;        // 10 MHz center
    scope.Acquisition.DDCConfig.DataDecimation = 16;           // Decimate by 16
    scope.Acquisition.DDCConfig.Q = 0.7;                       // Filter Q

    // Timing (effective rate is base rate / decimation)
    scope.Acquisition.ConfigureHorizontalTiming(
        sampleRate: 100e6,                     // Base rate
        numberOfPointsPerRecord: 10000,        // After decimation
        referencePosition: 50.0,
        numberOfRecords: 1,
        enforceRealtime: true
    );

    // Trigger
    scope.Trigger.ConfigureTriggerEdge("0", 0.0, ScopeTriggerCoupling.DC, 
                                      ScopeTriggerSlope.Positive, 0.0, 0.0);

    scope.Measurement.Initiate();

    // Fetch IQ data (DDC outputs complex samples)
    ScopeWaveform<ComplexInt16>[] waveforms = scope.Channels["0"].Measurement.FetchComplexInt16(
        timeout: TimeSpan.FromSeconds(5));

    Console.WriteLine("DDC IQ Data Acquired");
    Console.WriteLine($"Samples: {waveforms[0].SampleCount}");
}
```

---

## Waveform Scaling

NI-SCOPE returns raw ADC codes (Int16). Convert to voltages:

```csharp
ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(...);

// Method 1: Use GetScaledValue() (accounts for gain, offset, probe)
double voltage = waveforms[0].GetScaledValue(sampleIndex);

// Method 2: Manual scaling using waveform properties
double gainVoltsPerCode = waveforms[0].Gain;
double offsetVolts = waveforms[0].Offset;
short adcCode = waveforms[0].GetRawData()[sampleIndex];
double voltage = adcCode * gainVoltsPerCode + offsetVolts;
```

---

## Time Axis Reconstruction

```csharp
ScopeWaveform<short> waveform = waveforms[0];

// Get timing information
double dt = waveform.PrecisionTiming.SampleInterval.FractionalSeconds;  // Sample period
double t0 = waveform.PrecisionTiming.SampleOffsetTime.FractionalSeconds; // Start time

// Build time array
double[] time = new double[waveform.SampleCount];
for (int i = 0; i < waveform.SampleCount; i++)
{
    time[i] = t0 + i * dt;
}

Console.WriteLine($"Sample rate: {1.0 / dt / 1e6:F3} MS/s");
Console.WriteLine($"Time span: {time.Last() - time.First():F6} s");
```

---

## Reference Position Explanation

**Reference Position** determines where the trigger occurs in the record:
- **0%**: Trigger at start (all data is post-trigger)
- **50%**: Trigger at center (50% pre-trigger, 50% post-trigger)
- **100%**: Trigger at end (all data is pre-trigger)

```csharp
// Example: See what happened 1ms BEFORE trigger
scope.Acquisition.ConfigureHorizontalTiming(
    sampleRate: 100e6,
    numberOfPointsPerRecord: 100000,     // 1ms total @ 100MS/s
    referencePosition: 100.0,            // Trigger at END (100%)
    numberOfRecords: 1,
    enforceRealtime: true
);
// Result: All 1ms of captured data is PRE-trigger
```

---

## Performance Optimization

### Memory Allocation
```csharp
// Pre-allocate arrays for repeated acquisitions
double[] voltageBuffer = new double[10000];

for (int i = 0; i < 1000; i++)
{
    scope.Measurement.Initiate();
    ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(...);

    // Reuse pre-allocated buffer
    for (int j = 0; j < waveforms[0].SampleCount; j++)
    {
        voltageBuffer[j] = waveforms[0].GetScaledValue(j);
    }

    ProcessData(voltageBuffer);
}
```

### Minimize Data Transfer
```csharp
// If only need measurements, not full waveform:
// Option 1: Use built-in measurement functions (faster)
double vpp = measurement.MeasureWaveform(waveform, 
    ScopeWaveformMeasurementFunction.VoltagePeakToPeak);

// Option 2: Reduce sample count if full waveform not needed
scope.Acquisition.ConfigureHorizontalTiming(
    sampleRate: 100e6,
    numberOfPointsPerRecord: 1000,       // Fewer samples = faster transfer
    referencePosition: 50.0,
    numberOfRecords: 1,
    enforceRealtime: true
);
```

---

## Common Errors

### Error: Acquisition Not Complete
```csharp
// WRONG: Timeout too short for acquisition
scope.Acquisition.ConfigureHorizontalTiming(100e6, 100000000, 50.0, 1, true);  // 1 second
scope.Measurement.Initiate();
ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
    TimeSpan.FromSeconds(0.5));  // Only 0.5s timeout!

// CORRECT: Timeout > acquisition time
ScopeWaveform<short>[] waveforms = scope.Channels["0"].Measurement.FetchInt16(
    TimeSpan.FromSeconds(2));    // 2s timeout for 1s acquisition
```

### Error: Over-range / Clipping
```csharp
// Symptom: Waveform flat-topped (ADC saturated)

// WRONG: Range too small for signal
scope.Channels["0"].Configure(1.0, 0.0, ...);  // ±500mV range for 5V signal

// CORRECT: Increase range
scope.Channels["0"].Configure(10.0, 0.0, ...); // ±5V range
```

---

## Typical Sample Rates

| Application | Sample Rate | Notes |
|---|---|---|
| Audio signals | 100 kS/s | 50 kHz bandwidth |
| Power electronics | 1-10 MS/s | kHz switching frequencies |
| General digital signals | 100 MS/s | Up to ~20 MHz bandwidth |
| High-speed serial | 500 MS/s - 1 GS/s | 100+ MHz signals |
| RF/microwave | 1-5 GS/s | GHz signals (if supported) |

**Rule of thumb**: Sample at ≥5× highest frequency in signal (Nyquist + margin)

---

## Supported Devices

- **PXI-5122/5124**: 100 MS/s, 14-bit
- **PXIe-5160/5162**: 1-2.5 GS/s, 10-bit
- **PXIe-5170/5171**: 250 MS/s, 14-bit
- **PXIe-5172**: 250 MS/s, 16-bit (high resolution)
- **PXIe-5164**: 1 GS/s with DDC capability
- **PXIe-5185/5186**: 12.5-25 GS/s (ultra-high-speed)
- **PXIe-5842 VST**: RF vector signal transceiver (includes scope capability)

---

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [NI-DMM Reference](./nidmm-csharp.md)
- [Example: Waveform Analysis](../examples/niscope-waveform-analysis.cs)
- [Example: Continuous Acquisition](../examples/niscope-continuous.cs)
