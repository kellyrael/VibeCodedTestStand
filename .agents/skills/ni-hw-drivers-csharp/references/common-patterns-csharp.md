# NI C# Drivers - Common Patterns & Best Practices

This document covers patterns shared across all NI modular instrument drivers in C#.

## Table of Contents
1. [Session Management](#session-management)
2. [Resource Discovery](#resource-discovery)
3. [Error Handling](#error-handling)
4. [Property Configuration](#property-configuration)
5. [Threading & UI Responsiveness](#threading--ui-responsiveness)
6. [Performance Optimization](#performance-optimization)
7. [Multi-Instrument Synchronization (TClock)](#multi-instrument-synchronization-tclock)

---

## Session Management

### Basic Session Lifecycle

```csharp
using NationalInstruments.ModularInstruments.NIDCPower;

// Constructor parameters (common across all drivers):
// - resourceName: Device identifier (e.g., "PXI1Slot2", "PXI1Slot2/0", "Dev1")
// - idQuery: Verify instrument identity (usually false for performance)
// - reset: Reset device to known state (usually false to preserve settings)

using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    // Session is open and ready
    // ... configure and measure ...
} // Automatically closed and disposed
```

### Session Reuse Pattern

For multiple measurements on the same instrument:

```csharp
public class InstrumentManager : IDisposable
{
    private NIDCPower _session;

    public void Initialize(string resourceName)
    {
        _session = new NIDCPower(resourceName, false, false);
        // One-time configuration here
    }

    public DCPowerMeasurement MakeMeasurement()
    {
        // Reuse existing session
        return _session.Outputs["0"].Measurement.Measure();
    }

    public void Dispose()
    {
        _session?.Dispose();
    }
}

// Usage
using (var manager = new InstrumentManager())
{
    manager.Initialize("PXI1Slot2/0");

    for (int i = 0; i < 100; i++)
    {
        var measurement = manager.MakeMeasurement();
        // Process...
    }
} // Session closed once at end
```

### Multi-Instrument Session Management

```csharp
public class TestSystem : IDisposable
{
    private NIDCPower _smu;
    private NIDmm _dmm;
    private NIScope _scope;
    private List<IDisposable> _sessions = new List<IDisposable>();

    public void Initialize()
    {
        _smu = new NIDCPower("PXI1Slot2/0", false, false);
        _sessions.Add(_smu);

        _dmm = new NIDmm("PXI1Slot3", false, false);
        _sessions.Add(_dmm);

        _scope = new NIScope("PXI1Slot4", false, false);
        _sessions.Add(_scope);
    }

    public void Dispose()
    {
        // Dispose in reverse order
        for (int i = _sessions.Count - 1; i >= 0; i--)
        {
            try
            {
                _sessions[i]?.Dispose();
            }
            catch (Exception ex)
            {
                // Log but continue disposing others
                Console.WriteLine($"Error disposing session: {ex.Message}");
            }
        }
        _sessions.Clear();
    }
}
```

---

## Resource Discovery

### Discover Devices by Driver Family

```csharp
using NationalInstruments.ModularInstruments.SystemServices.DeviceServices;

public static class DeviceDiscovery
{
    public static List<string> GetDevices(string driverName)
    {
        var devices = new List<string>();

        using (var system = new ModularInstrumentsSystem(driverName))
        {
            foreach (DeviceInfo device in system.DeviceCollection)
            {
                devices.Add(device.Name);
            }
        }

        return devices;
    }

    public static Dictionary<string, string> GetDeviceDetails(string driverName)
    {
        var deviceMap = new Dictionary<string, string>();

        using (var system = new ModularInstrumentsSystem(driverName))
        {
            foreach (DeviceInfo device in system.DeviceCollection)
            {
                deviceMap[device.Name] = $"{device.Model} (Serial: {device.SerialNumber})";
            }
        }

        return deviceMap;
    }
}

// Usage
var dcPowerDevices = DeviceDiscovery.GetDevices("NI-DCPower");
var rfsaDevices = DeviceDiscovery.GetDevices("NI-RFSA");

foreach (var device in dcPowerDevices)
{
    Console.WriteLine($"Found SMU: {device}");
}
```

### Populate UI Controls

```csharp
// Common pattern for WinForms/WPF
private void LoadDevices()
{
    resourceComboBox.Items.Clear();

    using (var system = new ModularInstrumentsSystem("NI-DCPower"))
    {
        foreach (DeviceInfo device in system.DeviceCollection)
        {
            // Add channel-specific names for multi-channel devices
            int channels = device.NumberOfChannels;
            if (channels > 1)
            {
                for (int i = 0; i < channels; i++)
                {
                    resourceComboBox.Items.Add($"{device.Name}/{i}");
                }
            }
            else
            {
                resourceComboBox.Items.Add(device.Name);
            }
        }
    }

    if (resourceComboBox.Items.Count > 0)
        resourceComboBox.SelectedIndex = 0;
}
```

---

## Error Handling

### Basic Try-Catch Pattern

```csharp
using NationalInstruments.ModularInstruments.NIDCPower;

try
{
    using (var session = new NIDCPower(resourceName, false, false))
    {
        session.Outputs[channel].Source.Voltage.VoltageLevel = voltageLevel;
        session.Outputs[channel].Control.Initiate();
        var measurement = session.Outputs[channel].Measurement.Measure();

        return measurement.Current;
    }
}
catch (NIDCPowerException ex)
{
    // NI-specific errors
    Console.WriteLine($"NI-DCPower Error: {ex.Message}");
    Console.WriteLine($"Error Code: {ex.ErrorCode}");
    throw;
}
catch (Exception ex)
{
    // Unexpected errors
    Console.WriteLine($"Unexpected error: {ex.Message}");
    throw;
}
```

### Centralized Error Handler

```csharp
public static class NiErrorHandler
{
    public static void HandleError(Exception ex, string context = "")
    {
        string message = $"Error during {context}\n";

        // Check for NI-specific exception types
        if (ex is NationalInstruments.ModularInstruments.NIDCPower.NIDCPowerException dcPowerEx)
        {
            message += $"NI-DCPower Error {dcPowerEx.ErrorCode}: {dcPowerEx.Message}";
        }
        else if (ex is NationalInstruments.ModularInstruments.NIDmm.NIDmmException dmmEx)
        {
            message += $"NI-DMM Error {dmmEx.ErrorCode}: {dmmEx.Message}";
        }
        else if (ex is NationalInstruments.ModularInstruments.NIRfsa.NIRfsaException rfsaEx)
        {
            message += $"NI-RFSA Error {rfsaEx.ErrorCode}: {rfsaEx.Message}";
        }
        else
        {
            message += $"Unexpected Error: {ex.Message}\n{ex.StackTrace}";
        }

        // Log and/or display
        Console.WriteLine(message);
        MessageBox.Show(message, "Instrument Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}

// Usage
try
{
    // Instrument code
}
catch (Exception ex)
{
    NiErrorHandler.HandleError(ex, "DC voltage measurement");
}
```

---

## Property Configuration

### Batch Configuration Pattern

Group related property sets before initiating:

```csharp
using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    var channel = session.Outputs["0"];

    // Configure all properties BEFORE initiating
    session.Source.Mode = DCPowerSourceMode.SinglePoint;
    channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
    channel.Source.Voltage.VoltageLevel = 5.0;
    channel.Source.Voltage.VoltageLevelRange = 6.0;
    channel.Source.Current.CurrentLimit = 0.5;
    channel.Source.Current.CurrentLimitRange = 0.6;
    channel.Source.SourceDelay = new PrecisionTimeSpan(0.001);  // 1ms

    // Optional: Explicit commit to validate settings
    channel.Control.Commit();

    // Now initiate
    channel.Control.Initiate();

    // Measure
    var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(1));
}
```

### Configuration Objects Pattern

```csharp
public class DcVoltageConfig
{
    public double VoltageLevel { get; set; }
    public double VoltageRange { get; set; }
    public double CurrentLimit { get; set; }
    public double CurrentRange { get; set; }
    public double SourceDelay { get; set; }

    public void ApplyTo(NIDCPowerChannel channel)
    {
        channel.Source.Voltage.VoltageLevel = VoltageLevel;
        channel.Source.Voltage.VoltageLevelRange = VoltageRange;
        channel.Source.Current.CurrentLimit = CurrentLimit;
        channel.Source.Current.CurrentLimitRange = CurrentRange;
        channel.Source.SourceDelay = new PrecisionTimeSpan(SourceDelay);
    }
}

// Usage
var config = new DcVoltageConfig
{
    VoltageLevel = 3.3,
    VoltageRange = 6.0,
    CurrentLimit = 0.5,
    CurrentRange = 0.6,
    SourceDelay = 0.001
};

using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    var channel = session.Outputs["0"];
    session.Source.Mode = DCPowerSourceMode.SinglePoint;
    channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
    config.ApplyTo(channel);
    channel.Control.Initiate();
}
```

---

## Threading & UI Responsiveness

### Background Worker Pattern (WinForms)

```csharp
using System.ComponentModel;

private BackgroundWorker _worker;

private void StartMeasurement()
{
    startButton.Enabled = false;
    stopButton.Enabled = true;

    _worker = new BackgroundWorker
    {
        WorkerReportsProgress = true,
        WorkerSupportsCancellation = true
    };

    _worker.DoWork += Worker_DoWork;
    _worker.ProgressChanged += Worker_ProgressChanged;
    _worker.RunWorkerCompleted += Worker_Completed;

    _worker.RunWorkerAsync();
}

private void Worker_DoWork(object sender, DoWorkEventArgs e)
{
    var worker = sender as BackgroundWorker;

    using (var session = new NIDCPower("PXI1Slot2/0", false, false))
    {
        var channel = session.Outputs["0"];

        // Configure...
        channel.Control.Initiate();

        for (int i = 0; i < 100; i++)
        {
            if (worker.CancellationPending)
            {
                e.Cancel = true;
                break;
            }

            var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(1));

            // Report progress to UI thread
            worker.ReportProgress(i, measurement);

            System.Threading.Thread.Sleep(100);
        }

        channel.Control.Abort();
    }
}

private void Worker_ProgressChanged(object sender, ProgressChangedEventArgs e)
{
    var measurement = (DCPowerMeasurement)e.UserState;
    voltageLabel.Text = $"{measurement.Voltage:F3} V";
    currentLabel.Text = $"{measurement.Current:F6} A";
}

private void Worker_Completed(object sender, RunWorkerCompletedEventArgs e)
{
    startButton.Enabled = true;
    stopButton.Enabled = false;

    if (e.Cancelled)
        MessageBox.Show("Measurement cancelled");
    else if (e.Error != null)
        NiErrorHandler.HandleError(e.Error, "background measurement");
}

private void StopMeasurement()
{
    _worker?.CancelAsync();
}
```

### Task-Based Async Pattern (.NET 4.5+)

```csharp
using System.Threading;
using System.Threading.Tasks;

private CancellationTokenSource _cts;

private async void StartMeasurementAsync()
{
    _cts = new CancellationTokenSource();

    try
    {
        await Task.Run(() => MeasurementLoop(_cts.Token));
    }
    catch (OperationCanceledException)
    {
        MessageBox.Show("Measurement cancelled");
    }
    catch (Exception ex)
    {
        NiErrorHandler.HandleError(ex, "async measurement");
    }
}

private void MeasurementLoop(CancellationToken token)
{
    using (var session = new NIDCPower("PXI1Slot2/0", false, false))
    {
        var channel = session.Outputs["0"];
        channel.Control.Initiate();

        while (!token.IsCancellationRequested)
        {
            var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(1));

            // Marshal back to UI thread
            this.Invoke((Action)(() =>
            {
                voltageLabel.Text = $"{measurement.Voltage:F3} V";
            }));

            Thread.Sleep(100);
        }

        channel.Control.Abort();
    }
}

private void StopMeasurementAsync()
{
    _cts?.Cancel();
}
```

---

## Performance Optimization

### 1. Minimize Session Creation

```csharp
// SLOW: Create session for every measurement
for (int i = 0; i < 1000; i++)
{
    using (var session = new NIDCPower("PXI1Slot2/0", false, false))
    {
        // Configure and measure
    }
}

// FAST: Reuse session
using (var session = new NIDCPower("PXI1Slot2/0", false, false))
{
    // Configure once
    session.Outputs["0"].Control.Initiate();

    for (int i = 0; i < 1000; i++)
    {
        var measurement = session.Outputs["0"].Measurement.Fetch(TimeSpan.FromSeconds(0.1));
    }
}
```

### 2. Pre-Allocate Arrays

```csharp
// SLOW: Let API allocate
var waveforms = scope.Channels["0"].Measurement.FetchInt16(1000, TimeSpan.FromSeconds(5));

// FAST: Pre-allocate
short[] buffer = new short[1000];
scope.Channels["0"].Measurement.FetchInt16Into(buffer, TimeSpan.FromSeconds(5));
```

### 3. Use Appropriate Timeouts

```csharp
// Too long: UI appears frozen
var measurement = channel.Measurement.Fetch(TimeSpan.FromSeconds(60));

// Too short: Spurious timeout errors
var measurement = channel.Measurement.Fetch(TimeSpan.FromMilliseconds(1));

// Appropriate: Based on measurement time + margin
double measurementTime = 0.1;  // 100ms aperture
double margin = 0.5;  // 500ms margin
var measurement = channel.Measurement.Fetch(
    TimeSpan.FromSeconds(measurementTime + margin));
```

### 4. Batch Operations

```csharp
// SLOW: Individual property sets with roundtrips
for (int i = 0; i < 4; i++)
{
    session.Outputs[$"{i}"].Source.Voltage.VoltageLevel = 5.0;
    session.Outputs[$"{i}"].Control.Initiate();
}

// FAST: Configure all, then initiate all
for (int i = 0; i < 4; i++)
{
    session.Outputs[$"{i}"].Source.Voltage.VoltageLevel = 5.0;
}

// Initiate all channels together
session.Outputs["0-3"].Control.Initiate();
```

### 5. Disable Unused Features

```csharp
// Default: All measurements enabled (slower)
var measurement = channel.Measurement.Measure();

// Optimized: Only measure what you need
var measurement = channel.Measurement.Measure(
    DCPowerMeasurementTypes.Voltage);  // Skip current measurement
```

---

## Summary of Best Practices

✅ **DO:**
- Always use `using` statements for IDisposable sessions
- Reuse sessions for multiple measurements
- Batch property configuration before initiating
- Use appropriate timeouts based on measurement duration
- Handle NI-specific exception types
- Pre-allocate buffers for waveform fetches
- Use background threads for long acquisitions

❌ **DON'T:**
- Create/destroy sessions repeatedly
- Set properties one-by-one with delays between
- Use infinite or very short timeouts
- Ignore compliance flags on power supplies
- Block the UI thread with long measurements
- Catch and silently swallow exceptions

---

## Multi-Instrument Synchronization (TClock)

Use **NI TClock** for sub-nanosecond sample-aligned synchronization across multiple modular instruments. TClock is **mandatory** for phase offset measurements between instruments.

### When to Use TClock

| Scenario | TClock Required? |
|---|---|
| Phase offset measurement between two VSTs | ✅ **Yes** — also need shared ref clock + shared LO |
| Coherent multi-channel IQ capture | ✅ **Yes** |
| Synchronized generation + acquisition | ✅ **Yes** |
| Single-instrument measurement | ❌ No |
| Multi-instrument, timing not critical | ❌ No — use PXI trigger lines instead |

### Three Levels of Synchronization for Phase Measurements

Phase offset measurements require **all three** levels working together:

1. **Shared Reference Clock** — Both instruments derive timing from PXI backplane 10 MHz. Without this, frequency drift makes phase measurements meaningless.
2. **Shared LO** — One instrument exports its Local Oscillator, the other imports it. Without this, independent LO phase noise corrupts phase offset values.
3. **TClock Synchronized Start** — Aligns the first IQ sample to sub-nanosecond precision across instruments.

### Quick Pattern

```csharp
using NationalInstruments.ModularInstruments;                              // ITClockSynchronizableDevice
using NationalInstruments.ModularInstruments.SystemServices.TimingServices; // TClock

// 1. Share reference clock
rfsa1.Configuration.ReferenceClock.Configure(RfsaReferenceClockSource.PxiClock, 10e6);
rfsa2.Configuration.ReferenceClock.Configure(RfsaReferenceClockSource.PxiClock, 10e6);

// 2. Share LO (RFSA1 exports, RFSA2 imports)
rfsa1.Configuration.SignalPath.LocalOscillator.LOExportEnabled = true;
double loFreq = rfsa1.Configuration.SignalPath.LocalOscillator.LOFrequency;  // Read actual LO freq
rfsa2.Configuration.SignalPath.LocalOscillator.LOSource = RfsaLOSource.LOIn;
rfsa2.Configuration.SignalPath.LocalOscillator.LOFrequency = loFreq;          // MUST set to match exporter

// 3. TClock synchronize and start
var tclock = new TClock(new ITClockSynchronizableDevice[] { rfsa1, rfsa2 });
tclock.ConfigureForHomogeneousTriggers();
tclock.Synchronize();
tclock.Initiate();  // Starts BOTH instruments simultaneously
```

**⚠️ CRITICAL**: When using TClock, **never** call `rfsa.Acquisition.IQ.Initiate()` on individual instruments. Always use `tclock.Initiate()` to start all devices together.

See [`rfsa-rfsg-csharp.md`](./rfsa-rfsg-csharp.md#ni-tclock--sub-nanosecond-multi-instrument-synchronization) for complete API reference, verified properties, and a full phase offset measurement example.
