# NI-SWITCH C# API Reference

Complete reference for NI Switch Modules in C#.

## Namespace
```csharp
using NationalInstruments.ModularInstruments.NISwitch;
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;
```

## Session Class

```csharp
// Constructor
public NISwitch(string resourceName, string topology, bool simulate, bool resetDevice)

// Parameters:
// - resourceName: "PXI1Slot6", "Switch1", "Dev1", etc.
// - topology: Topology name (device-specific, e.g., "2737/4x64 Matrix")
// - simulate: false (set true for simulation mode)
// - resetDevice: false (recommended)
```

## Key Concepts

### Topology
The **topology** defines how the switch module is configured:
- **Matrix**: MxN crosspoint switch (rows and columns)
- **Multiplexer**: Many inputs to one output
- **Independent**: Individual relay control
- **Topology string must match device capability**

### Channel Names
Switch channels use specific naming conventions:
- **Matrix**: `"r0c0"` (row 0, column 0), `"r1c3"`, etc.
- **Multiplexer**: `"ch0"`, `"ch1"`, etc.
- **COM**: Common terminal - `"com0"`, `"com1"`

### Paths
A **path** is a connection between two channels:
```
"ch0->com0"  // Connect ch0 to com0
"r0c0->r0c1" // Connect row 0 col 0 to row 0 col 1
```

## Key Enumerations

### SwitchPathCapability
```csharp
SwitchPathCapability.Available          // Path can be connected
SwitchPathCapability.Exists             // Path exists in topology
SwitchPathCapability.ResourceInUse      // Path exists but resource in use
SwitchPathCapability.SourceConflict     // Source channel already connected
SwitchPathCapability.ChannelNotAvailable // Channel not available
```

### SwitchScanMode
```csharp
SwitchScanMode.None                     // No scanning
SwitchScanMode.BreakBeforeMake          // Open old before close new (default)
SwitchScanMode.BreakAfterMake          // Close new before open old (make-before-break)
```

### SwitchHandshakingInitiation
```csharp
SwitchHandshakingInitiation.Measurement // Wait for measurement instrument trigger
SwitchHandshakingInitiation.None        // No handshaking
```

## Property Hierarchy

### Path and Connection
```csharp
// Basic connection operations
session.Path.Connect(path, waitForDebounce);
session.Path.Disconnect(path);
session.Path.DisconnectAll();

// Query path state
bool isDebounced = session.Path.IsDebounced(path);
bool isConnected = session.Path.CanConnect(path) == SwitchPathCapability.Available;

// Settling time
session.Path.SetPath(path);              // Set path without waiting
session.Path.WaitForDebounce(maxTime);   // Wait for relays to settle
```

### Scanning
```csharp
// Scan list configuration
session.Scanning.ScanList                // Semicolon-separated list of paths
session.Scanning.ScanMode                // BreakBeforeMake or BreakAfterMake
session.Scanning.TriggerInput            // Trigger source for scan steps
session.Scanning.ScanDelay               // Delay between scan steps (seconds)

// Scan execution
session.Scanning.InitiateScan();
session.Scanning.WaitForScanComplete(timeout);
session.Scanning.Abort();
```

### Relay Control
```csharp
// Relay cycle count (for maintenance)
int cycleCount = session.GetRelayCount(relayName);

// Relay position
session.GetRelayPosition(relayName);     // Open or Closed
```

## Common Switch Topologies

### Matrix Switch (e.g., PXI-2532B, PXI-2535)
```
Topology: "2532/4x32 Matrix"
Channels: r0c0, r0c1, ..., r3c31 (4 rows × 32 columns)
Use case: Route any row to any column
```

### Multiplexer (e.g., PXI-2527, PXI-2529)
```
Topology: "2527/64-Channel Mux"
Channels: ch0-ch63, com0
Use case: Connect any ch# to com0
```

### High-Density Matrix (e.g., PXI-2535, PXI-2737)
```
Topology: "2535/4x136 Matrix"
Channels: r0c0, r0c1, ..., r3c135
Use case: Large crosspoint matrices for ATE systems
```

### RF Switch (e.g., PXIe-2737, PXIe-2738)
```
Topology: "2737/4x64 Matrix" (terminated/non-terminated)
Channels: r0c0, ..., r3c63
Use case: High-frequency signal routing (up to 4 GHz)
```

### General-Purpose Relay (e.g., PXI-2503, PXI-2510)
```
Topology: "2503/Independent"
Channels: ch0-ch11 (SPDT relays)
Use case: Independent relay control
```

## Common Workflows

### 1. Simple Connection (Multiplexer)

```csharp
using NationalInstruments.ModularInstruments.NISwitch;

// PXI-2527: 64-channel multiplexer
using (var sw = new NISwitch("PXI1Slot6", "2527/64-Channel Mux", false, false))
{
    // Connect channel 5 to COM
    string path = "ch5->com0";
    sw.Path.Connect(path, waitForDebounce: true);

    Console.WriteLine($"Connected {path}");

    // Perform measurement on com0
    System.Threading.Thread.Sleep(100);  // Simulate measurement

    // Disconnect
    sw.Path.Disconnect(path);
    Console.WriteLine($"Disconnected {path}");
}
```

### 2. Matrix Crosspoint Connection

```csharp
// PXI-2532B: 4×32 matrix
using (var sw = new NISwitch("PXI1Slot6", "2532/4x32 Matrix", false, false))
{
    // Connect row 0 to column 10
    string path = "r0c10";
    sw.Path.Connect(path, waitForDebounce: true);

    Console.WriteLine($"Connected row 0 to column 10");

    // Measure or perform test
    MeasureSignal();

    // Disconnect
    sw.Path.Disconnect(path);

    // Connect different path
    path = "r2c15";
    sw.Path.Connect(path, waitForDebounce: true);
    Console.WriteLine($"Connected row 2 to column 15");

    MeasureSignal();

    // Disconnect all at end
    sw.Path.DisconnectAll();
}
```

### 3. Sequential Channel Scanning (Multiplexer)

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2527/64-Channel Mux", false, false))
{
    // Scan through channels 0-9 sequentially
    for (int ch = 0; ch < 10; ch++)
    {
        string path = $"ch{ch}->com0";

        // Connect
        sw.Path.Connect(path, waitForDebounce: true);
        Console.WriteLine($"Measuring channel {ch}...");

        // Perform measurement
        double measurement = MeasureDMM();  // Example: DMM on com0
        Console.WriteLine($"  Result: {measurement:F6}");

        // Disconnect
        sw.Path.Disconnect(path);
    }
}
```

### 4. Matrix Row/Column Scanning

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2532/4x32 Matrix", false, false))
{
    // Test all connections on row 0
    for (int col = 0; col < 32; col++)
    {
        string path = $"r0c{col}";

        sw.Path.Connect(path, waitForDebounce: true);

        // Perform test (e.g., continuity, resistance)
        bool continuity = TestContinuity(col);
        Console.WriteLine($"r0c{col}: {(continuity ? "PASS" : "FAIL")}");

        sw.Path.Disconnect(path);
    }
}
```

### 5. Scan List (Automated Scanning)

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2527/64-Channel Mux", false, false))
{
    // Build scan list: channels 0, 5, 10, 15
    string scanList = "ch0->com0; ch5->com0; ch10->com0; ch15->com0";
    sw.Scanning.ScanList = scanList;

    // Configure scan parameters
    sw.Scanning.ScanMode = SwitchScanMode.BreakBeforeMake;  // Break-before-make
    sw.Scanning.ScanDelay = 0.01;                           // 10ms between steps

    Console.WriteLine("Starting scan...");

    // Initiate scan
    sw.Scanning.InitiateScan();

    // Wait for completion
    sw.Scanning.WaitForScanComplete(TimeSpan.FromSeconds(5));

    Console.WriteLine("Scan complete");
}
```

### 6. Triggered Scanning with DMM

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2527/64-Channel Mux", false, false))
using (var dmm = new NIDmm("PXI1Slot3", false, false))
{
    // Configure DMM for triggered measurements
    dmm.Measurement.Function = DmmFunction.DCVolts;
    dmm.Measurement.Range = 10.0;
    dmm.Trigger.TriggerSource = DmmTriggerSource.External;  // External trigger
    dmm.Trigger.SampleCount = 4;                            // 4 channels

    // Configure switch scan list
    sw.Scanning.ScanList = "ch0->com0; ch1->com0; ch2->com0; ch3->com0";
    sw.Scanning.ScanMode = SwitchScanMode.BreakBeforeMake;
    sw.Scanning.ScanDelay = 0.05;                           // 50ms settling

    // Configure switch to trigger DMM at each step
    sw.Scanning.TriggerInput = SwitchTriggerInput.External;
    sw.Scanning.ConfigureScanTrigger(triggerSource: "PXI_Trig0");

    // Start DMM acquisition
    dmm.Measurement.Initiate();

    // Start switch scan
    sw.Scanning.InitiateScan();

    // Wait for scan to complete
    sw.Scanning.WaitForScanComplete(TimeSpan.FromSeconds(10));

    // Fetch DMM results (one per channel)
    double[] measurements = dmm.Measurement.FetchMultiple(
        maxTime: TimeSpan.FromSeconds(1),
        arraySize: 4
    );

    for (int i = 0; i < measurements.Length; i++)
    {
        Console.WriteLine($"ch{i}: {measurements[i]:F6} V");
    }
}
```

### 7. Path Validation Before Connection

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2532/4x32 Matrix", false, false))
{
    string path = "r0c5";

    // Check if path can be connected
    SwitchPathCapability capability = sw.Path.CanConnect(path);

    switch (capability)
    {
        case SwitchPathCapability.Available:
            sw.Path.Connect(path, waitForDebounce: true);
            Console.WriteLine($"Connected {path}");
            break;

        case SwitchPathCapability.ResourceInUse:
            Console.WriteLine($"Cannot connect {path}: resource in use");
            break;

        case SwitchPathCapability.SourceConflict:
            Console.WriteLine($"Cannot connect {path}: source conflict");
            sw.Path.DisconnectAll();  // Clear conflicts
            sw.Path.Connect(path, waitForDebounce: true);
            break;

        default:
            Console.WriteLine($"Cannot connect {path}: {capability}");
            break;
    }
}
```

### 8. Multiple Simultaneous Connections (Matrix)

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2532/4x32 Matrix", false, false))
{
    // Connect multiple independent paths simultaneously
    // Each row can connect to ONE column at a time

    List<string> paths = new List<string>
    {
        "r0c5",   // Row 0 to column 5
        "r1c10",  // Row 1 to column 10
        "r2c15",  // Row 2 to column 15
        "r3c20"   // Row 3 to column 20
    };

    // Connect all paths
    foreach (string path in paths)
    {
        sw.Path.Connect(path, waitForDebounce: false);  // Fast connect
    }

    // Wait for all relays to settle
    sw.Path.WaitForDebounce(TimeSpan.FromMilliseconds(100));

    Console.WriteLine("All paths connected:");
    foreach (string path in paths)
    {
        Console.WriteLine($"  {path}");
    }

    // Perform parallel measurements on columns 5, 10, 15, 20
    PerformParallelMeasurements();

    // Disconnect all
    sw.Path.DisconnectAll();
}
```

### 9. RF Matrix Switching (Terminated)

```csharp
// PXIe-2737: 4×64 RF matrix with 50Ω termination
using (var sw = new NISwitch("PXI1Slot6", "2737/4x64 Matrix (50 Ohm)", false, false))
{
    // Connect RF source on row 0 to DUT input on column 10
    string txPath = "r0c10";
    sw.Path.Connect(txPath, waitForDebounce: true);

    // Connect DUT output on column 11 to RF analyzer on row 1
    string rxPath = "r1c11";
    sw.Path.Connect(rxPath, waitForDebounce: true);

    Console.WriteLine("RF paths configured:");
    Console.WriteLine($"  TX: {txPath}");
    Console.WriteLine($"  RX: {rxPath}");

    // Wait for relay settling (important for RF)
    System.Threading.Thread.Sleep(50);

    // Perform RF measurement
    PerformRFMeasurement();

    // Disconnect
    sw.Path.DisconnectAll();
}
```

### 10. Relay Cycle Counting (Maintenance)

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2532/4x32 Matrix", false, false))
{
    // Check relay cycle counts for maintenance
    List<string> relaysToCheck = new List<string> { "r0c0", "r0c1", "r1c0", "r1c1" };

    Console.WriteLine("Relay Cycle Counts:");
    foreach (string relay in relaysToCheck)
    {
        int cycleCount = sw.GetRelayCount(relay);
        Console.WriteLine($"  {relay}: {cycleCount} cycles");

        // Warn if approaching relay lifetime (typically 1-10 million cycles)
        if (cycleCount > 5000000)
        {
            Console.WriteLine($"    WARNING: Relay {relay} approaching end of life!");
        }
    }
}
```

### 11. Independent SPDT Relay Control

```csharp
// PXI-2503: 12 independent SPDT relays
using (var sw = new NISwitch("PXI1Slot6", "2503/Independent", false, false))
{
    // SPDT relays have NC (normally closed) and NO (normally open) positions

    // Close relay 0 (connect NC to COM)
    sw.Path.Connect("ch0->com0", waitForDebounce: true);
    Console.WriteLine("Relay 0: NC to COM");

    // Switch relay 0 to NO position
    sw.Path.Disconnect("ch0->com0");
    sw.Path.Connect("ch0->no0", waitForDebounce: true);
    Console.WriteLine("Relay 0: NO to COM");

    // Control multiple relays independently
    sw.Path.Connect("ch1->com1", waitForDebounce: false);
    sw.Path.Connect("ch2->no2", waitForDebounce: false);
    sw.Path.Connect("ch3->com3", waitForDebounce: false);

    sw.Path.WaitForDebounce(TimeSpan.FromMilliseconds(50));

    Console.WriteLine("Multiple relays configured");
}
```

### 12. Make-Before-Break Switching (Hot Switching)

```csharp
using (var sw = new NISwitch("PXI1Slot6", "2527/64-Channel Mux", false, false))
{
    // Make-before-break: close new connection before opening old
    // Useful for maintaining circuit continuity (e.g., power rails)

    // Initial connection
    sw.Path.Connect("ch0->com0", waitForDebounce: true);
    Console.WriteLine("Initial: ch0 connected");

    // Switch to ch1 using make-before-break
    sw.Scanning.ScanMode = SwitchScanMode.BreakAfterMake;  // Make-before-break

    // Disconnect ch0 and connect ch1 atomically
    sw.Path.Disconnect("ch0->com0");
    sw.Path.Connect("ch1->com0", waitForDebounce: true);

    Console.WriteLine("Switched to: ch1 connected (make-before-break)");

    // Note: Not all topologies support make-before-break
    // Check device specifications
}
```

---

## Debounce and Settling Time

### Relay Debounce
After connecting/disconnecting, relays need time to settle (typically 2-10ms):

```csharp
// FAST: Connect without waiting (for batch operations)
sw.Path.Connect(path, waitForDebounce: false);

// Then wait for all relays to settle
sw.Path.WaitForDebounce(TimeSpan.FromMilliseconds(100));

// SAFE: Wait for each connection (slower but simpler)
sw.Path.Connect(path, waitForDebounce: true);
```

### Scan Delay
For scan lists, add delay between steps for signal settling:

```csharp
sw.Scanning.ScanDelay = 0.05;  // 50ms delay between scan steps
```

---

## Path Naming Conventions

### Matrix Switches
```
"r0c0"     - Row 0, Column 0
"r2c15"    - Row 2, Column 15
```

### Multiplexers
```
"ch0->com0"   - Channel 0 to COM0
"ch15->com0"  - Channel 15 to COM0
```

### Independent Relays (SPDT)
```
"ch0->com0"   - NC (normally closed) position
"ch0->no0"    - NO (normally open) position
```

---

## Topology String Examples

| Device | Topology String |
|---|---|
| PXI-2527 | `"2527/64-Channel Mux"` |
| PXI-2529 | `"2529/2-Channel Mux"` or `"2529/Dual 1x4 Mux"` |
| PXI-2532B | `"2532/4x32 Matrix"` |
| PXI-2535 | `"2535/4x136 Matrix"` |
| PXI-2503 | `"2503/Independent"` |
| PXI-2510 | `"2510/Independent"` |
| PXIe-2737 | `"2737/4x64 Matrix (50 Ohm)"` or `"2737/4x64 Matrix (75 Ohm)"` |
| PXIe-2738 | `"2738/4x64 Matrix (50 Ohm)"` or `"2738/Dual 1x32 Mux (50 Ohm)"` |

**Important**: Topology string must **exactly match** device capability. Check MAX (Measurement & Automation Explorer) or device documentation.

---

## Performance Tips

1. **Batch connections** - Connect multiple paths with `waitForDebounce: false`, then call `WaitForDebounce()` once
2. **Scan lists** - For sequential switching, scan lists are faster than repeated Connect/Disconnect
3. **Minimize disconnect operations** - DisconnectAll() is faster than individual disconnects
4. **Reuse sessions** - Session creation is slow, keep sessions open
5. **Check relay cycles** - Monitor `GetRelayCount()` for maintenance planning

---

## Common Errors

### Error: Invalid Topology
```csharp
// WRONG: Topology doesn't match device
var sw = new NISwitch("PXI1Slot6", "Wrong/Topology", false, false);
// Error: Topology not supported

// CORRECT: Use exact topology from device documentation
var sw = new NISwitch("PXI1Slot6", "2532/4x32 Matrix", false, false);
```

### Error: Invalid Path
```csharp
// WRONG: Path doesn't exist in topology
sw.Path.Connect("r5c0", true);  // Matrix only has 4 rows (0-3)

// CORRECT: Use valid channel names
sw.Path.Connect("r3c31", true); // Valid for 4×32 matrix
```

### Error: Resource Conflict
```csharp
// WRONG: Try to connect row to two columns simultaneously
sw.Path.Connect("r0c5", true);
sw.Path.Connect("r0c10", true);  // ERROR: r0 already connected to c5

// CORRECT: Disconnect first, or check CanConnect()
sw.Path.Disconnect("r0c5");
sw.Path.Connect("r0c10", true);
```

---

## Relay Lifetime Considerations

| Relay Type | Typical Lifetime | Notes |
|---|---|---|
| Electromechanical (low power) | 1-10 million cycles | General-purpose switches |
| Electromechanical (high power) | 100k-1M cycles | Power switches (PXI-2510, etc.) |
| Reed relay | 100M-1B cycles | Fast, low power (PXI-2527, etc.) |
| Solid-state (FET) | Virtually unlimited | No wear, but limited voltage/current |

**Best practices:**
- Rotate usage across relays when possible
- Monitor cycle counts with `GetRelayCount()`
- Schedule maintenance before reaching 80% of rated life

---

## Hot Switching Ratings

**Hot switching**: Switching while current flows or voltage present

⚠️ **Check device specifications** - exceeding ratings damages relays:
- **Voltage rating**: Maximum voltage across open contacts
- **Current rating**: Maximum current through closed contacts
- **Power rating**: Maximum power (V × I)
- **Switching capacity**: Maximum voltage × current product during switching

```csharp
// Example: PXI-2527 reed relay ratings
// - Switching: 10VA (e.g., 10V × 1A or 5V × 2A)
// - Carry: 1A max, 30V max
// - Hot switch with care to stay within limits
```

---

## Supported Devices

### Matrix Switches
- **PXI-2530B** (4×128), **PXI-2531** (4×64), **PXI-2532B** (4×32)
- **PXI-2535** (4×136 high-density)
- **PXI-2564** (16×32 with CAN)
- **PXIe-2737** (4×64 RF, up to 4 GHz)
- **PXIe-2738** (4×64 or dual 1×32 RF)

### Multiplexers
- **PXI-2527** (64-channel, reed relay)
- **PXI-2529** (2-channel or dual 4-channel)
- **PXI-2593** (16-channel RF, up to 26.5 GHz)

### General-Purpose Relay
- **PXI-2503** (12 SPDT)
- **PXI-2510** (32-channel high-power)
- **PXI-2545/2546** (fault insertion, 5×8 or 8×16)

### High-Frequency/RF
- **PXIe-2737/2738** (4 GHz RF matrix/mux)
- **PXI-2593** (26.5 GHz RF mux)
- **PXI-2597** (6 GHz RF mux, 50Ω)

---

## See Also

- [Common Patterns](./common-patterns-csharp.md)
- [NI-DMM Reference](./nidmm-csharp.md) - Often used with switches for multi-channel measurements
- [Example: Switch + DMM Multi-Channel](../examples/niswitch-dmm-scan.cs)
- [Example: Matrix Test](../examples/niswitch-matrix-test.cs)
