# NI-DMM C# API Reference

Complete reference for Digital Multimeters (NI-DMM) in C#.

## Namespace
```csharp
using NationalInstruments.ModularInstruments.NIDmm;
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## Session Class

```csharp
// Constructor
public NIDmm(string resourceName, bool idQuery, bool resetDevice)

// Parameters:
// - resourceName: "PXI1Slot3", "DMM1", "Dev1", etc.
// - idQuery: false (recommended)
// - resetDevice: false (recommended)
```

## Key Enumerations

### DmmFunction (Measurement Function)
```csharp
DmmFunction.DCVolts              // DC voltage
DmmFunction.ACVolts              // AC voltage (RMS)
DmmFunction.DCCurrent            // DC current
DmmFunction.ACCurrent            // AC current (RMS)
DmmFunction.TwoWireResistance    // 2-wire resistance
DmmFunction.FourWireResistance   // 4-wire resistance
DmmFunction.Frequency            // Frequency
DmmFunction.Period               // Period
DmmFunction.Temperature          // Temperature (requires transducer type)
DmmFunction.Diode                // Diode test
DmmFunction.Capacitance          // Capacitance
DmmFunction.Inductance           // Inductance
```

### DmmApertureTimeUnits
```csharp
DmmApertureTimeUnits.Seconds            // Aperture in seconds
DmmApertureTimeUnits.PowerLineCycles    // Aperture in PLCs (e.g., 1 PLC = 16.67ms @ 60Hz)
```

### DmmTriggerSource
```csharp
DmmTriggerSource.Immediate       // No trigger, measure immediately
DmmTriggerSource.External        // External trigger pin
DmmTriggerSource.SoftwareTrigger // Software trigger via SendSoftwareTrigger()
DmmTriggerSource.Interval        // Time-based triggering
```

### DmmTransducerType (for Temperature)
```csharp
DmmTransducerType.Thermocouple   // Thermocouple (specify type)
DmmTransducerType.Thermistor     // Thermistor
DmmTransducerType.TwoWireRtd     // 2-wire RTD
DmmTransducerType.FourWireRtd    // 4-wire RTD
```

## Property Hierarchy

### Measurement Configuration
```csharp
// Function and range
session.Measurement.Function                  // DmmFunction enum
session.Measurement.Range                     // Measurement range (auto = -1)
session.Measurement.AutoRange                 // Auto-ranging enabled/disabled

// Aperture time (integration time)
session.Measurement.ApertureTime              // Aperture time value
session.Measurement.ApertureTimeUnits         // Seconds or PowerLineCycles

// Resolution
session.Measurement.DigitsOfResolution        // Digits (3.5 to 8.5)
session.Measurement.ResolutionAbsolute        // Absolute resolution

// Input impedance
session.Measurement.InputResistance           // Input impedance (Ω), 10M default

// Temperature-specific
session.Measurement.TransducerType            // Thermocouple, RTD, etc.
session.Measurement.ThermocoupleType          // J, K, T, E, R, S, B, N types
session.Measurement.TemperatureRtdType        // Pt3750, Pt3851, Pt3916, Pt3920, etc.
session.Measurement.TemperatureRtdResistance  // RTD resistance at 0°C (e.g., 100Ω)
```

### Triggering
```csharp
session.Trigger.TriggerSource                 // Immediate, External, Software, Interval
session.Trigger.TriggerDelay                  // Delay after trigger (seconds)
session.Trigger.SampleInterval                // Time between samples (Interval mode)
session.Trigger.SampleCount                   // Number of samples to acquire
```

## Common Workflows

### 1. Simple DC Voltage Measurement

```csharp
using NationalInstruments.ModularInstruments.NIDmm;

using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure DC voltage measurement
    dmm.Measurement.Function = DmmFunction.DCVolts;
    dmm.Measurement.Range = 10.0;                // 10V range
    dmm.Measurement.ResolutionAbsolute = 0.0001; // 100µV resolution

    // Perform measurement
    double voltage = dmm.Measurement.Read(TimeSpan.FromSeconds(1));

    Console.WriteLine($"DC Voltage: {voltage:F6} V");
}
```

### 2. AC Voltage Measurement (RMS)

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure AC voltage (RMS)
    dmm.Measurement.Function = DmmFunction.ACVolts;
    dmm.Measurement.Range = 10.0;
    dmm.Measurement.ResolutionAbsolute = 0.001;  // 1mV resolution

    // AC measurements often need more integration time
    dmm.Measurement.ApertureTime = 0.1;          // 100ms
    dmm.Measurement.ApertureTimeUnits = DmmApertureTimeUnits.Seconds;

    double acVoltage = dmm.Measurement.Read(TimeSpan.FromSeconds(2));

    Console.WriteLine($"AC Voltage (RMS): {acVoltage:F6} V");
}
```

### 3. 4-Wire Resistance Measurement

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure 4-wire resistance (Kelvin measurement)
    dmm.Measurement.Function = DmmFunction.FourWireResistance;
    dmm.Measurement.Range = 1000.0;              // 1kΩ range
    dmm.Measurement.ResolutionAbsolute = 0.001;  // 1mΩ resolution

    // 4-wire for accurate low-resistance measurement
    double resistance = dmm.Measurement.Read(TimeSpan.FromSeconds(1));

    Console.WriteLine($"4-Wire Resistance: {resistance:F6} Ω");
}
```

### 4. High-Accuracy Measurement (Long Aperture)

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // High-accuracy DC voltage
    dmm.Measurement.Function = DmmFunction.DCVolts;
    dmm.Measurement.Range = 10.0;
    dmm.Measurement.DigitsOfResolution = 7.5;    // 7.5 digits (high accuracy)

    // Long aperture time for noise rejection
    dmm.Measurement.ApertureTime = 10;           // 10 PLCs (167ms @ 60Hz)
    dmm.Measurement.ApertureTimeUnits = DmmApertureTimeUnits.PowerLineCycles;

    // Multiple readings for statistics
    int numReadings = 10;
    List<double> readings = new List<double>();

    for (int i = 0; i < numReadings; i++)
    {
        double reading = dmm.Measurement.Read(TimeSpan.FromSeconds(5));
        readings.Add(reading);
        Console.WriteLine($"Reading {i + 1}: {reading:F8} V");
    }

    double average = readings.Average();
    double stdDev = Math.Sqrt(readings.Average(x => Math.Pow(x - average, 2)));

    Console.WriteLine($"\nAverage: {average:F8} V");
    Console.WriteLine($"Std Dev: {stdDev * 1e6:F3} µV");
}
```

### 5. Multi-Point Acquisition (Triggered)

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure measurement
    dmm.Measurement.Function = DmmFunction.DCVolts;
    dmm.Measurement.Range = 10.0;
    dmm.Measurement.ResolutionAbsolute = 0.001;

    // Configure triggered acquisition
    dmm.Trigger.TriggerSource = DmmTriggerSource.Immediate;
    dmm.Trigger.SampleCount = 100;               // 100 samples
    dmm.Trigger.TriggerDelay = 0.001;            // 1ms delay after trigger

    // Read multiple samples
    double[] readings = dmm.Measurement.ReadMultiPoint(
        maxTime: TimeSpan.FromSeconds(10),
        arraySize: 100
    );

    Console.WriteLine($"Acquired {readings.Length} samples");
    Console.WriteLine($"Average: {readings.Average():F6} V");
    Console.WriteLine($"Min: {readings.Min():F6} V");
    Console.WriteLine($"Max: {readings.Max():F6} V");

    // Plot or save data
    SaveToFile(readings);
}
```

### 6. Timed Interval Acquisition

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure measurement
    dmm.Measurement.Function = DmmFunction.DCVolts;
    dmm.Measurement.Range = 10.0;

    // Time-based sampling
    dmm.Trigger.TriggerSource = DmmTriggerSource.Interval;
    dmm.Trigger.SampleInterval = 0.1;            // 100ms between samples (10 Hz)
    dmm.Trigger.SampleCount = 1000;              // 1000 samples (100 seconds total)

    Console.WriteLine("Acquiring 1000 samples at 10 Hz (100 seconds)...");

    double[] readings = dmm.Measurement.ReadMultiPoint(
        maxTime: TimeSpan.FromSeconds(120),      // 120s timeout
        arraySize: 1000
    );

    Console.WriteLine("Acquisition complete");

    // Analyze data
    PlotTimeSeries(readings, sampleRate: 10.0);
}
```

### 7. Temperature Measurement (Thermocouple)

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure thermocouple temperature measurement
    dmm.Measurement.Function = DmmFunction.Temperature;
    dmm.Measurement.TransducerType = DmmTransducerType.Thermocouple;
    dmm.Measurement.ThermocoupleType = DmmThermocoupleType.K;  // Type K (Chromel-Alumel)

    // Optional: Configure cold junction compensation
    dmm.Measurement.ThermocoupleReferenceJunctionType = 
        DmmThermocoupleReferenceJunctionType.Fixed;
    dmm.Measurement.FixedReferenceJunction = 25.0;   // 25°C reference

    double temperature = dmm.Measurement.Read(TimeSpan.FromSeconds(2));

    Console.WriteLine($"Temperature (Type K): {temperature:F2} °C");
}
```

### 8. Temperature Measurement (RTD)

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure 4-wire RTD temperature measurement
    dmm.Measurement.Function = DmmFunction.Temperature;
    dmm.Measurement.TransducerType = DmmTransducerType.FourWireRtd;
    dmm.Measurement.TemperatureRtdType = DmmRtdType.Pt3851;      // Pt100 (α=0.003851)
    dmm.Measurement.TemperatureRtdResistance = 100.0;             // 100Ω @ 0°C

    // RTD measurements are high accuracy
    dmm.Measurement.ApertureTime = 5;                             // 5 PLCs
    dmm.Measurement.ApertureTimeUnits = DmmApertureTimeUnits.PowerLineCycles;

    double temperature = dmm.Measurement.Read(TimeSpan.FromSeconds(2));

    Console.WriteLine($"Temperature (RTD): {temperature:F3} °C");
}
```

### 9. Frequency Measurement

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure frequency measurement
    dmm.Measurement.Function = DmmFunction.Frequency;
    dmm.Measurement.Range = 10.0;                // Voltage range for trigger level
    dmm.Measurement.FrequencyVoltageRange = 10.0;

    // Aperture time determines measurement accuracy
    dmm.Measurement.ApertureTime = 0.1;          // 100ms gate time
    dmm.Measurement.ApertureTimeUnits = DmmApertureTimeUnits.Seconds;

    double frequency = dmm.Measurement.Read(TimeSpan.FromSeconds(2));

    Console.WriteLine($"Frequency: {frequency:F3} Hz");
}
```

### 10. Capacitance Measurement

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure capacitance measurement
    dmm.Measurement.Function = DmmFunction.Capacitance;
    dmm.Measurement.AutoRange = -1;              // Auto-ranging

    double capacitance = dmm.Measurement.Read(TimeSpan.FromSeconds(2));

    // Convert to convenient units
    if (capacitance < 1e-9)
        Console.WriteLine($"Capacitance: {capacitance * 1e12:F3} pF");
    else if (capacitance < 1e-6)
        Console.WriteLine($"Capacitance: {capacitance * 1e9:F3} nF");
    else if (capacitance < 1e-3)
        Console.WriteLine($"Capacitance: {capacitance * 1e6:F3} µF");
    else
        Console.WriteLine($"Capacitance: {capacitance * 1e3:F3} mF");
}
```

### 11. Diode Test

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure diode test
    dmm.Measurement.Function = DmmFunction.Diode;

    // Diode test returns forward voltage drop
    double forwardVoltage = dmm.Measurement.Read(TimeSpan.FromSeconds(1));

    Console.WriteLine($"Diode Forward Voltage: {forwardVoltage:F3} V");

    // Typical values:
    // Silicon diode: ~0.6-0.7V
    // LED: ~1.8-3.3V (varies by color)
    // Shorted: ~0V
    // Open circuit: Over-range indication

    if (forwardVoltage < 0.3)
        Console.WriteLine("Status: Shorted");
    else if (forwardVoltage > 3.5)
        Console.WriteLine("Status: Open or reverse biased");
    else
        Console.WriteLine("Status: Normal diode");
}
```

### 12. Auto-Ranging Example

```csharp
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure with auto-ranging
    dmm.Measurement.Function = DmmFunction.DCVolts;
    dmm.Measurement.AutoRange = -1;              // Enable auto-range
    dmm.Measurement.ResolutionAbsolute = 0.001;

    // First measurement may be slower (auto-ranging)
    double voltage1 = dmm.Measurement.Read(TimeSpan.FromSeconds(5));
    Console.WriteLine($"Measurement 1: {voltage1:F6} V");

    // Subsequent measurements faster (range cached)
    double voltage2 = dmm.Measurement.Read(TimeSpan.FromSeconds(1));
    Console.WriteLine($"Measurement 2: {voltage2:F6} V");

    // Check what range was selected
    double actualRange = dmm.Measurement.Range;
    Console.WriteLine($"Selected range: {actualRange:F3} V");
}
```

---

## Aperture Time Guidelines

**Power Line Cycles (PLCs)** - Best for DC measurements, rejects line frequency noise:
- **0.02 PLC**: Fast (333µs @ 60Hz), low accuracy
- **0.2 PLC**: Medium speed, moderate accuracy
- **1 PLC**: Good compromise (16.67ms @ 60Hz)
- **10 PLC**: High accuracy, slower (167ms @ 60Hz)
- **100 PLC**: Maximum accuracy (1.67s @ 60Hz)

**Seconds** - Best for AC measurements or frequency/period:
- Match to signal characteristics
- Longer aperture = better noise rejection, slower

```csharp
// Example: Choose aperture based on accuracy requirements
if (highSpeedRequired)
{
    dmm.Measurement.ApertureTime = 0.02;
    dmm.Measurement.ApertureTimeUnits = DmmApertureTimeUnits.PowerLineCycles;
}
else if (highAccuracyRequired)
{
    dmm.Measurement.ApertureTime = 100;
    dmm.Measurement.ApertureTimeUnits = DmmApertureTimeUnits.PowerLineCycles;
}
```

---

## Resolution vs Range Trade-off

Higher resolution on smaller range provides better measurement:

```csharp
// GOOD: Match range to expected voltage
dmm.Measurement.Range = 1.0;                 // 1V range for 0.5V signal
dmm.Measurement.ResolutionAbsolute = 0.00001; // 10µV resolution

// LESS OPTIMAL: Over-range
dmm.Measurement.Range = 100.0;               // 100V range for 0.5V signal
dmm.Measurement.ResolutionAbsolute = 0.001;   // Only 1mV resolution
```

---

## Multi-Point Efficiency

For multiple measurements, use `ReadMultiPoint()` instead of repeated `Read()`:

```csharp
// SLOW: Multiple Read() calls (overhead per call)
for (int i = 0; i < 100; i++)
{
    double value = dmm.Measurement.Read(TimeSpan.FromSeconds(1));
    data[i] = value;
}

// FAST: Single ReadMultiPoint() call
dmm.Trigger.SampleCount = 100;
double[] data = dmm.Measurement.ReadMultiPoint(
    TimeSpan.FromSeconds(10), 100);
```

---

## Input Impedance Considerations

Default input impedance is 10 MΩ (high impedance mode):

```csharp
// High impedance (default): 10 MΩ - minimal loading on DUT
dmm.Measurement.InputResistance = 10e6;

// Low impedance: ~10 kΩ - for noisy environments or high-source-impedance
dmm.Measurement.InputResistance = 10e3;  // If supported by DMM
```

---

## Common Errors

### Error: Over-range
```csharp
// Symptom: Reading returns +9.9E+37 (over-range indicator)

// WRONG: Range too small for signal
dmm.Measurement.Range = 1.0;     // 1V range
// ... measuring 5V signal -> over-range!

// CORRECT: Use appropriate range or auto-range
dmm.Measurement.Range = 10.0;    // 10V range
// OR
dmm.Measurement.AutoRange = -1;  // Auto-range
```

### Error: Timeout
```csharp
// WRONG: Timeout shorter than measurement time
dmm.Measurement.ApertureTime = 100;  // 100 PLCs = 1.67s
double reading = dmm.Measurement.Read(TimeSpan.FromSeconds(1));  // Only 1s timeout!

// CORRECT: Timeout >> measurement time
double reading = dmm.Measurement.Read(TimeSpan.FromSeconds(5));  // 5s timeout
```

---

## Performance Tips

1. **Reuse sessions** - Session creation is slow
2. **Use ReadMultiPoint()** - For multiple measurements, much faster than repeated Read()
3. **Manual ranging** - Auto-range is slow on first measurement
4. **Appropriate aperture time** - Balance speed vs accuracy
5. **Cache range after auto-range** - Read `dmm.Measurement.Range` and reuse

---

## Typical Aperture Time Settings

| Measurement Type | Aperture Time | Notes |
|---|---|---|
| Fast DC voltage | 0.02-0.2 PLC | Fast, moderate accuracy |
| Standard DC voltage | 1 PLC | Good balance |
| High-accuracy DC voltage | 10-100 PLC | Slow, high accuracy |
| AC voltage (50/60 Hz) | 0.1-1 second | Match to signal period |
| Resistance | 1-10 PLC | Similar to DC voltage |
| Temperature (thermocouple) | 1-5 PLC | Settling time important |
| Temperature (RTD) | 5-10 PLC | Higher accuracy |
| Frequency/Period | 0.1-1 second | Gate time determines accuracy |

---

## Supported Devices

- PXI-4065 (6½-digit DMM)
- PXI-4070/4071/4072 (6½-digit FlexDMM)
- PXIe-4080/4081/4082 (7½/8½-digit DMM)
- PXI-4130 series (with DMM capability)
- And many others - check NI website

---

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [NI-DCPower Reference](./nidcpower-csharp.md)
- [Example: Multi-Channel DMM](../examples/nidmm-multi-channel.cs)
- [Example: Temperature Logging](../examples/nidmm-temperature-log.cs)
