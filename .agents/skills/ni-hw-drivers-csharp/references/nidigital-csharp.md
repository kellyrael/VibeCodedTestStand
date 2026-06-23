# NI-DIGITAL C# API Reference

Complete reference for NI Digital Pattern Instruments in C#.

## Namespace
```csharp
using NationalInstruments.ModularInstruments.NIDigital;
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## Session Class

```csharp
// Constructor
public NIDigital(string resourceName, bool idQuery, bool resetDevice)

// Parameters:
// - resourceName: "PXI1Slot8", "Digital1", "Dev1", etc.
// - idQuery: false (recommended)
// - resetDevice: false (recommended)
```

## Key Concepts

### Channels and Pin Groups
- **Channels**: Individual instrument pins (e.g., "0", "1", "2")
- **Pin Groups**: Logical grouping of pins (e.g., "DataBus", "ControlLines")
- **Site**: Test site number for multi-DUT testing

### Pattern Execution
Digital pattern instruments execute **patterns** that define:
- Source data (drive values)
- Capture data (compare/measure values)
- Timing (when to drive/capture)
- Looping and conditional branching

### Timing and Sequencing
- **Timing sets**: Define edge placement (drive/compare events)
- **Source/Capture delay**: Fine-tune when data is driven/captured
- **Period**: Time for one pattern cycle

## Key Enumerations

### DigitalPinState
```csharp
DigitalPinState.Zero                    // Drive/expect logic 0
DigitalPinState.One                     // Drive/expect logic 1
DigitalPinState.X                       // Don't care (for capture)
DigitalPinState.L                       // Compare to logic low
DigitalPinState.H                       // Compare to logic high
DigitalPinState.M                       // Midband (for capture window)
DigitalPinState.V                       // Valid data (for comparison)
```

### TriggerType
```csharp
DigitalTriggerType.None                 // No trigger
DigitalTriggerType.DigitalEdge          // Digital edge trigger
DigitalTriggerType.Software             // Software trigger
```

### SelectedFunction
```csharp
DigitalSelectedFunction.Digital         // Digital pattern mode
DigitalSelectedFunction.PPMU            // Programmable power supply mode
DigitalSelectedFunction.Off             // Pin disconnected
```

### PPMUOutputFunction
```csharp
DigitalPpmuOutputFunction.DCVoltage     // Source voltage
DigitalPpmuOutputFunction.DCCurrent     // Source current
```

## Property Hierarchy

### Channel Configuration
```csharp
// Pin/channel selection
session.PinAndChannelMap.GetPinSet("DataBus");        // Get pins in group

// Selected function
session.Channels["0"].SelectedFunction                // Digital, PPMU, or Off

// Digital levels (voltage thresholds)
session.Channels["DataBus"].ConfigureVoltageLevels(
    vil: 0.5,                                         // Input low
    vih: 2.0,                                         // Input high
    vol: 0.4,                                         // Output low
    voh: 2.4,                                         // Output high
    vterm: 1.5);                                      // Termination voltage
```

### Timing Configuration
```csharp
// Timing sets
session.Timing.ConfigurePatternBurstTimingSets(
    timingSetName: "ts0",
    period: 10e-9,                                    // 10ns period (100 MHz)
    driveFormat: DigitalDriveFormat.NR,               // Non-return (NRZ)
    sourceDataEdge: 0e-9,                             // Drive at 0ns
    captureDataEdge: 5e-9);                           // Capture at 5ns
```

### Pattern Configuration
```csharp
// Load pattern from file
session.PatternControl.LoadPattern("C:\\Patterns\\mypattern.digipat");

// Burst pattern
session.PatternControl.BurstPattern(
    startLabel: "start",                              // Start label in pattern
    selectDigitalFunction: true,                      // Enable digital pins
    waitUntilDone: true,                              // Block until complete
    timeout: 10.0);                                   // 10 second timeout
```

### PPMU (Programmable Power Management Unit)
```csharp
// Configure PPMU for DC voltage sourcing
session.Channels["VDD"].Ppmu.OutputFunction = DigitalPpmuOutputFunction.DCVoltage;
session.Channels["VDD"].Ppmu.VoltageLevel = 3.3;     // 3.3V
session.Channels["VDD"].Ppmu.CurrentLimit = 0.1;     // 100mA limit

// Enable PPMU output
session.Channels["VDD"].Ppmu.Source();
```

## Common Workflows

### 1. Basic Static Pattern (Bit-Bang)

```csharp
using NationalInstruments.ModularInstruments.NIDigital;

using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    // Configure channels as pin group
    string pins = "0,1,2,3";  // 4-bit bus

    // Set to digital mode
    digital.Channels[pins].SelectedFunction = DigitalSelectedFunction.Digital;

    // Configure voltage levels (TTL/CMOS)
    digital.Channels[pins].ConfigureVoltageLevels(
        vil: 0.8,     // Input low < 0.8V
        vih: 2.0,     // Input high > 2.0V
        vol: 0.4,     // Output low < 0.4V
        voh: 2.4,     // Output high > 2.4V
        vterm: 1.5    // Termination at 1.5V
    );

    // Write static pattern (bit-bang)
    DigitalPinState[] pattern = new DigitalPinState[]
    {
        DigitalPinState.Zero,   // Pin 0 = 0
        DigitalPinState.One,    // Pin 1 = 1
        DigitalPinState.One,    // Pin 2 = 1
        DigitalPinState.Zero    // Pin 3 = 0
    };

    digital.Channels[pins].WriteStatic(pattern);
    Console.WriteLine("Static pattern written: 0110");

    System.Threading.Thread.Sleep(100);

    // Read back
    DigitalPinState[] readback = digital.Channels[pins].ReadStatic();
    Console.Write("Readback: ");
    foreach (var state in readback)
    {
        Console.Write(state == DigitalPinState.One ? "1" : "0");
    }
    Console.WriteLine();
}
```

### 2. Simple Pattern Burst

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string pins = "0,1,2,3,4,5,6,7";  // 8-bit data bus

    // Configure pins
    digital.Channels[pins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[pins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Configure timing: 100 MHz (10ns period)
    digital.Timing.ConfigurePatternBurstTimingSets(
        timingSetName: "ts_100MHz",
        period: 10e-9,
        driveFormat: DigitalDriveFormat.NR,
        sourceDataEdge: 0e-9,
        captureDataEdge: 5e-9
    );

    // Load pattern from file
    string patternFile = "C:\\Patterns\\counter_pattern.digipat";
    digital.PatternControl.LoadPattern(patternFile);

    // Burst pattern
    Console.WriteLine("Running pattern...");
    digital.PatternControl.BurstPattern(
        startLabel: "main",
        selectDigitalFunction: true,
        waitUntilDone: true,
        timeout: 5.0
    );

    Console.WriteLine("Pattern complete");
}
```

### 3. Pattern with Capture and Compare

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string outputPins = "0,1,2,3";     // Drive pins
    string inputPins = "4,5,6,7";      // Capture pins

    // Configure drive pins
    digital.Channels[outputPins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[outputPins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Configure capture pins
    digital.Channels[inputPins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[inputPins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Configure timing
    digital.Timing.ConfigurePatternBurstTimingSets(
        timingSetName: "ts0",
        period: 20e-9,           // 50 MHz
        driveFormat: DigitalDriveFormat.NR,
        sourceDataEdge: 0e-9,
        captureDataEdge: 10e-9   // Capture at midpoint
    );

    // Load pattern with capture
    digital.PatternControl.LoadPattern("C:\\Patterns\\loopback_test.digipat");

    // Burst pattern
    digital.PatternControl.BurstPattern("start", true, true, 10.0);

    // Get pass/fail results
    bool[] sitePass = digital.PatternControl.GetSitePassFail();

    for (int site = 0; site < sitePass.Length; site++)
    {
        Console.WriteLine($"Site {site}: {(sitePass[site] ? "PASS" : "FAIL")}");
    }

    // Get failure count per pin
    long[] failureCount = digital.PatternControl.GetFailCount(inputPins);
    for (int i = 0; i < failureCount.Length; i++)
    {
        Console.WriteLine($"Pin {i}: {failureCount[i]} failures");
    }
}
```

### 4. PPMU Voltage Sourcing (Power Supply)

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string powerPins = "VDD,VDDIO";

    // Configure VDD as PPMU voltage source
    digital.Channels["VDD"].SelectedFunction = DigitalSelectedFunction.PPMU;
    digital.Channels["VDD"].Ppmu.OutputFunction = DigitalPpmuOutputFunction.DCVoltage;
    digital.Channels["VDD"].Ppmu.VoltageLevel = 3.3;        // 3.3V
    digital.Channels["VDD"].Ppmu.CurrentLimit = 0.5;        // 500mA limit

    // Configure VDDIO
    digital.Channels["VDDIO"].SelectedFunction = DigitalSelectedFunction.PPMU;
    digital.Channels["VDDIO"].Ppmu.OutputFunction = DigitalPpmuOutputFunction.DCVoltage;
    digital.Channels["VDDIO"].Ppmu.VoltageLevel = 1.8;      // 1.8V
    digital.Channels["VDDIO"].Ppmu.CurrentLimit = 0.2;      // 200mA limit

    // Enable PPMU outputs
    digital.Channels[powerPins].Ppmu.Source();
    Console.WriteLine("Power supplies enabled: VDD=3.3V, VDDIO=1.8V");

    // Wait for DUT power-up
    System.Threading.Thread.Sleep(100);

    // Measure current consumption
    double[] currentMeasurements = digital.Channels[powerPins].Ppmu.MeasureCurrent();
    Console.WriteLine($"VDD current: {currentMeasurements[0] * 1000:F3} mA");
    Console.WriteLine($"VDDIO current: {currentMeasurements[1] * 1000:F3} mA");

    // Perform tests...

    // Disable outputs
    digital.Channels[powerPins].SelectedFunction = DigitalSelectedFunction.Off;
}
```

### 5. PPMU Current Measurement (Leakage Test)

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string pinUnderTest = "0";

    // Configure PPMU for voltage sourcing
    digital.Channels[pinUnderTest].SelectedFunction = DigitalSelectedFunction.PPMU;
    digital.Channels[pinUnderTest].Ppmu.OutputFunction = DigitalPpmuOutputFunction.DCVoltage;
    digital.Channels[pinUnderTest].Ppmu.VoltageLevel = 5.0;      // Apply 5V
    digital.Channels[pinUnderTest].Ppmu.CurrentLimit = 0.001;    // 1mA limit (safety)

    // Source voltage
    digital.Channels[pinUnderTest].Ppmu.Source();
    System.Threading.Thread.Sleep(10);  // Settling time

    // Measure leakage current
    double[] leakageCurrent = digital.Channels[pinUnderTest].Ppmu.MeasureCurrent();
    double leakageUa = leakageCurrent[0] * 1e6;  // Convert to µA

    Console.WriteLine($"Leakage current @ 5V: {leakageUa:F3} µA");

    // Check against specification
    double maxLeakageUa = 10.0;  // 10µA max
    if (Math.Abs(leakageUa) < maxLeakageUa)
    {
        Console.WriteLine("PASS: Leakage within spec");
    }
    else
    {
        Console.WriteLine("FAIL: Excessive leakage");
    }

    // Cleanup
    digital.Channels[pinUnderTest].SelectedFunction = DigitalSelectedFunction.Off;
}
```

### 6. Multi-Site Testing (Parallel DUT)

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    // Configure for 2 sites (2 DUTs in parallel)
    int numSites = 2;

    // Site 0: Pins 0-7
    // Site 1: Pins 8-15

    string allPins = "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15";

    // Configure pins
    digital.Channels[allPins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[allPins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Configure timing
    digital.Timing.ConfigurePatternBurstTimingSets("ts0", 10e-9, 
        DigitalDriveFormat.NR, 0e-9, 5e-9);

    // Load pattern
    digital.PatternControl.LoadPattern("C:\\Patterns\\dut_test.digipat");

    // Burst pattern (all sites in parallel)
    digital.PatternControl.BurstPattern("start", true, true, 10.0);

    // Get per-site results
    bool[] sitePass = digital.PatternControl.GetSitePassFail();

    for (int site = 0; site < numSites; site++)
    {
        Console.WriteLine($"DUT {site}: {(sitePass[site] ? "PASS" : "FAIL")}");
    }

    // Get history RAM (capture data per site)
    foreach (int site in Enumerable.Range(0, numSites))
    {
        uint[][] historyData = digital.PatternControl.FetchHistoryRAMCycleInformation(
            site: site,
            sampleIndex: 0,
            samplesToRead: 100
        );

        Console.WriteLine($"Site {site} captured {historyData[0].Length} cycles");
    }
}
```

### 7. Frequency Measurement

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string clockPin = "0";

    // Configure pin for frequency measurement
    digital.Channels[clockPin].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[clockPin].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Measure frequency
    double[] frequencies = digital.Channels[clockPin].Frequency.MeasureFrequency(
        numberOfSamples: 10                    // Average over 10 samples
    );

    double avgFrequency = frequencies[0];
    Console.WriteLine($"Measured frequency: {avgFrequency / 1e6:F3} MHz");

    // Check against specification
    double nominalFrequency = 100e6;           // 100 MHz nominal
    double tolerance = 0.01;                   // ±1%

    double error = Math.Abs(avgFrequency - nominalFrequency) / nominalFrequency;

    if (error < tolerance)
    {
        Console.WriteLine($"PASS: Frequency within {tolerance * 100}%");
    }
    else
    {
        Console.WriteLine($"FAIL: Frequency error {error * 100:F2}%");
    }
}
```

### 8. Timing Set Configuration (Multiple Rates)

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string pins = "0,1,2,3,4,5,6,7";

    digital.Channels[pins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[pins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Create multiple timing sets for different speeds

    // High-speed: 200 MHz (5ns period)
    digital.Timing.ConfigurePatternBurstTimingSets(
        timingSetName: "ts_200MHz",
        period: 5e-9,
        driveFormat: DigitalDriveFormat.NR,
        sourceDataEdge: 0e-9,
        captureDataEdge: 2.5e-9
    );

    // Medium-speed: 100 MHz (10ns period)
    digital.Timing.ConfigurePatternBurstTimingSets(
        timingSetName: "ts_100MHz",
        period: 10e-9,
        driveFormat: DigitalDriveFormat.NR,
        sourceDataEdge: 0e-9,
        captureDataEdge: 5e-9
    );

    // Low-speed: 10 MHz (100ns period)
    digital.Timing.ConfigurePatternBurstTimingSets(
        timingSetName: "ts_10MHz",
        period: 100e-9,
        driveFormat: DigitalDriveFormat.NR,
        sourceDataEdge: 0e-9,
        captureDataEdge: 50e-9
    );

    Console.WriteLine("Timing sets configured: 200MHz, 100MHz, 10MHz");

    // Pattern can switch between timing sets dynamically
    // (specified in .digipat file)
}
```

### 9. Dynamic Drive Pattern (Source Waveform)

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string dataPins = "0,1,2,3,4,5,6,7";  // 8-bit bus

    digital.Channels[dataPins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[dataPins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Configure timing
    digital.Timing.ConfigurePatternBurstTimingSets("ts0", 100e-9, 
        DigitalDriveFormat.NR, 0e-9, 50e-9);  // 10 MHz

    // Create source waveform data (counter 0x00 to 0xFF)
    uint numVectors = 256;
    uint[] sourceData = new uint[numVectors];
    for (uint i = 0; i < numVectors; i++)
    {
        sourceData[i] = i;  // 0, 1, 2, ..., 255
    }

    // Write source waveform
    digital.SourceWaveforms.CreateSourceWaveformU32(
        waveformName: "counter_waveform",
        waveformData: sourceData
    );

    Console.WriteLine("Source waveform created: 0x00 to 0xFF");

    // Pattern would reference this waveform by name
    // burst pattern <waveform_name>
}
```

### 10. Conditional Pattern Execution

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string pins = "0,1,2,3,4,5,6,7";

    digital.Channels[pins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[pins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);
    digital.Timing.ConfigurePatternBurstTimingSets("ts0", 10e-9, 
        DigitalDriveFormat.NR, 0e-9, 5e-9);

    // Load pattern with conditional logic
    string patternFile = "C:\\Patterns\\conditional_test.digipat";
    digital.PatternControl.LoadPattern(patternFile);

    // Pattern contains conditional jumps:
    // if (pattern_pass) goto pass_label
    // else goto fail_label

    // Set conditional flags before burst
    digital.PatternControl.SetConditional(
        conditionalName: "enable_fast_test",
        value: true
    );

    // Burst pattern
    digital.PatternControl.BurstPattern("start", true, true, 10.0);

    // Check which path was taken
    string endLabel = digital.PatternControl.GetPatternPinIndexList();
    Console.WriteLine($"Pattern ended at: {endLabel}");
}
```

### 11. TDR (Time Domain Reflectometry) Cable Test

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    string pinsToTest = "0,1,2,3";

    // Configure pins
    digital.Channels[pinsToTest].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[pinsToTest].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Perform TDR measurement
    foreach (string pin in pinsToTest.Split(','))
    {
        // Apply step function and measure reflection
        double cableLength = digital.Channels[pin].Tdr.MeasureCableLength();

        Console.WriteLine($"Pin {pin}: Cable length = {cableLength:F3} meters");

        // Detect opens/shorts
        if (cableLength < 0.1)
        {
            Console.WriteLine($"  WARNING: Possible short on pin {pin}");
        }
        else if (cableLength > 10.0)
        {
            Console.WriteLine($"  WARNING: Possible open on pin {pin}");
        }
    }
}
```

### 12. Pattern Pin Mapping (Multi-DUT with Different Pinouts)

```csharp
using (var digital = new NIDigital("PXI1Slot8", false, false))
{
    // Two DUTs with different pin mappings
    // Site 0: Standard pinout
    // Site 1: Rotated pinout

    // Define pin map for site 0
    Dictionary<string, string> site0Map = new Dictionary<string, string>
    {
        { "DATA0", "0" },
        { "DATA1", "1" },
        { "DATA2", "2" },
        { "DATA3", "3" },
        { "CLK", "4" },
        { "CS", "5" }
    };

    // Define pin map for site 1 (different physical pins)
    Dictionary<string, string> site1Map = new Dictionary<string, string>
    {
        { "DATA0", "8" },
        { "DATA1", "9" },
        { "DATA2", "10" },
        { "DATA3", "11" },
        { "CLK", "12" },
        { "CS", "13" }
    };

    // Configure pin groups (logical names)
    digital.PinAndChannelMap.CreatePinGroup("DATA_SITE0", "0,1,2,3");
    digital.PinAndChannelMap.CreatePinGroup("DATA_SITE1", "8,9,10,11");

    // Configure all pins
    string allPins = "0,1,2,3,4,5,8,9,10,11,12,13";
    digital.Channels[allPins].SelectedFunction = DigitalSelectedFunction.Digital;
    digital.Channels[allPins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

    // Pattern uses logical names (DATA0, DATA1, etc.)
    // Pin map translates to physical channels per site

    Console.WriteLine("Multi-site pin mapping configured");
}
```

---

## Pattern File Format (.digipat)

Basic structure of a digital pattern file:

```
file_format_version 1.0;

// Pin definitions
pinmap DATA[0:7] { 0, 1, 2, 3, 4, 5, 6, 7 };
pinmap CLK { 8 };

// Timing set
timing ts0
{
    period 10ns;
    source 0ns;
    capture 5ns;
}

// Vector table
pattern main
{
    //        DATA      CLK
    vector    00000000  0;
    vector    11111111  1;
    vector    10101010  0;
    vector    01010101  1;
    repeat 100;
    halt;
}
```

---

## Voltage Levels Guidelines

### Common Logic Families

| Logic Family | VIL | VIH | VOL | VOH | Vterm |
|---|---|---|---|---|---|
| **TTL** | 0.8V | 2.0V | 0.4V | 2.4V | 1.5V |
| **3.3V CMOS** | 0.8V | 2.0V | 0.4V | 2.4V | 1.65V |
| **2.5V CMOS** | 0.7V | 1.7V | 0.4V | 2.0V | 1.25V |
| **1.8V CMOS** | 0.45V | 1.17V | 0.45V | 1.35V | 0.9V |
| **LVDS** | - | - | - | - | 1.2V |

```csharp
// TTL levels
digital.Channels[pins].ConfigureVoltageLevels(0.8, 2.0, 0.4, 2.4, 1.5);

// 1.8V CMOS
digital.Channels[pins].ConfigureVoltageLevels(0.45, 1.17, 0.45, 1.35, 0.9);
```

---

## Timing Edge Placement

```csharp
// Period: Total time for one pattern cycle
// SourceDataEdge: When to drive data (typically 0 or near 0)
// CaptureDataEdge: When to sample input (typically mid-period)

digital.Timing.ConfigurePatternBurstTimingSets(
    timingSetName: "ts0",
    period: 20e-9,            // 20ns = 50 MHz
    driveFormat: DigitalDriveFormat.NR,
    sourceDataEdge: 2e-9,     // Drive at 2ns
    captureDataEdge: 12e-9    // Capture at 12ns (setup/hold margin)
);
```

**Timing diagram:**
```
        _______________           _______________
       |               |         |               |
_______|               |_________|               |________
       ^               ^         ^
       0ns             10ns      20ns
         ^              ^
      Source(2ns)    Capture(12ns)
```

---

## Performance Tips

1. **Parallel testing** - Use multi-site for higher throughput
2. **Optimize pattern** - Minimize vector count, use loops
3. **Reuse timing sets** - Don't create unnecessarily
4. **History RAM** - Capture only when needed (consumes memory)
5. **PPMU settling** - Allow time after PPMU source/measurement changes

---

## Common Errors

### Error: Timing Violation
```csharp
// WRONG: Capture edge too early (setup time violation)
digital.Timing.ConfigurePatternBurstTimingSets("ts0", 10e-9, 
    DigitalDriveFormat.NR, 0e-9, 1e-9);  // Only 1ns setup time!

// CORRECT: Capture near mid-period
digital.Timing.ConfigurePatternBurstTimingSets("ts0", 10e-9, 
    DigitalDriveFormat.NR, 0e-9, 5e-9);  // 5ns setup time
```

### Error: PPMU Over-Current
```csharp
// WRONG: Current limit too low
digital.Channels["VDD"].Ppmu.CurrentLimit = 0.001;  // Only 1mA
// ... DUT draws 50mA -> over-current trip

// CORRECT: Set appropriate limit
digital.Channels["VDD"].Ppmu.CurrentLimit = 0.1;    // 100mA
```

### Error: Pattern Not Found
```csharp
// WRONG: Start label doesn't exist in pattern
digital.PatternControl.BurstPattern("wrong_label", true, true, 10.0);
// Error: Label not found

// CORRECT: Use valid label from .digipat file
digital.PatternControl.BurstPattern("main", true, true, 10.0);
```

---

## Typical Applications

### 1. Memory Test (SRAM/DRAM)
- Generate address/data patterns
- Write/read cycles with timing control
- Algorithmic test patterns (March, checkerboard)

### 2. SPI/I2C/UART Protocol Test
- Clock generation with precise timing
- Data capture and comparison
- Protocol-specific patterns

### 3. Digital IC Functional Test
- Power supply via PPMU
- Functional vectors for logic verification
- Parametric tests (leakage, continuity)

### 4. FPGA/ASIC Production Test
- High-speed pattern execution (up to 200 MHz)
- Multi-site parallel testing
- Scan chain testing

---

## Supported Devices

### High-Speed Digital
- **PXIe-6570** (1 GB/s, 32 channels, up to 200 MHz)
- **PXIe-6571** (2 GB/s, 32 channels, up to 200 MHz)

### High-Pin-Count Digital
- **PXIe-6556/6557** (High-power, 32 channels, 100 MHz)
- **PXIe-6555** (Low-power, 32 channels, 100 MHz)

### Digital Waveform
- **PXIe-6535/6536/6537** (32-bit, up to 100 MHz, low-cost)

**Key specs:**
- **Pin count**: 16-32 channels per module (expandable with multiple modules)
- **Data rate**: 10-200 MHz pattern execution
- **PPMU**: Programmable per-pin power (±6V, up to 32mA source, 2mA measure)
- **Memory**: Pattern and capture memory (varies by device)

---

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [NI-DCPower Reference](./nidcpower-csharp.md) - For higher-power sourcing/measurement
- [Example: Digital Pattern Test](../examples/nidigital-pattern-test.cs)
- [Example: PPMU Parametrics](../examples/nidigital-ppmu-parametrics.cs)
