# Skills Update: One-Prompt RF Measurement Capability

**Date**: 2026-04-28  
**Goal**: Enable users to request RF measurements with a single prompt and receive complete, working code that generates the signal and measures it.

---

## What Was Added

### 1. New Reference File: `rfmx-generation-measurement-workflows.md`

**Location**: `.agents/skills/ni-hw-drivers-csharp/references/rfmx-generation-measurement-workflows.md`

**Purpose**: Comprehensive guide for complete RF test automation workflows that combine signal generation with measurements.

**Contents**:
- **4 Complete Workflow Examples**:
  1. **WLAN (802.11ac)** - EVM and TxP measurement
  2. **LTE FDD** - ModAcc and ACP measurement
  3. **5G NR** - ModAcc measurement
  4. **Bluetooth LE** - TxP and ModAcc measurement

- **Standard Pattern** (all workflows follow this):
  1. Initialize RFSG (signal generator)
  2. Generate signal (load/create waveform, configure frequency/power)
  3. Initialize RFmx (analyzer)
  4. **Configure IQPowerEdge trigger** (default, automatic triggering)
  5. Configure measurement (select measurements, parameters)
  6. Initiate & measure (fetch results)
  7. Cleanup (stop generation, dispose sessions)

- **IQPowerEdge Triggering** (default for all workflows):
  - Automatic triggering when signal power crosses threshold
  - No external trigger routing needed
  - Works with pulsed and continuous signals
  - Minimal preamble loss
  - Set trigger level ~10 dB below expected signal

- **Key Patterns Documented**:
  - Signal settling time (100ms after generation start)
  - Waveform loading vs in-code generation
  - Continuous vs triggered generation
  - Resource cleanup with try-finally
  - Common issues and solutions

---

## What Was Changed

### 2. Updated `SKILL.md`

**Changes**:
- **Updated description** to emphasize generation + measurement workflows
- **Added prominent reference** to new workflows file with ⭐ marker
- **Added guidance note**: "For RF measurements: When users request wireless signal measurements (WLAN/LTE/5G/BT), always read `rfmx-generation-measurement-workflows.md` first"
- **Listed workflow capabilities**: Signal generation, IQPowerEdge triggering, measurements, pass/fail, cleanup

**New description**:
> "Generate complete, production-ready C# code for NI modular instrument drivers with automatic signal generation. Specializes in complete RF test workflows: generate wireless signals with RFSG → trigger with IQPowerEdge → measure with RFmx. Automatically includes RFSG signal generation for all RF measurement requests."

---

## How This Achieves "One-Prompt Measurement"

### Before This Update

**User request**: "Measure 802.11ac EVM at 5 GHz"

**LLM would generate**: 
- RFmx measurement code only
- User would need to provide external signal source
- Manual trigger configuration required
- Incomplete workflow

### After This Update

**User request**: "Measure 802.11ac EVM at 5 GHz"

**LLM will generate**:
1. ✅ RFSG initialization and signal generation
2. ✅ Waveform loading (with file path guidance)
3. ✅ IQPowerEdge automatic triggering configuration
4. ✅ RFmx WLAN measurement configuration
5. ✅ Complete measurement execution
6. ✅ Pass/Fail validation against spec limits
7. ✅ Proper resource cleanup

**Result**: Complete, executable code that:
- Generates the 802.11ac signal internally
- Automatically triggers on the signal
- Performs EVM measurement
- Validates results
- Cleans up all resources

---

## Example Prompts That Now Work

Users can now request measurements with simple prompts like:

1. **"Measure 802.11ac EVM"**
   - Generates complete WLAN generation + measurement code
   - Includes IQPowerEdge triggering
   - EVM, frequency error, clock error results
   - Pass/Fail against 802.11ac spec

2. **"Test LTE 20 MHz signal ACP"**
   - Generates LTE FDD signal (20 MHz)
   - Configures ACP measurement
   - Fetches E-UTRA adjacent channel power
   - Validates against -30 dBc limit

3. **"Generate and measure 5G NR at 3.5 GHz"**
   - Creates 5G NR FR1 signal
   - 100 MHz bandwidth
   - ModAcc EVM measurement
   - Pass/Fail against 256QAM limit (3.5%)

4. **"Measure Bluetooth LE transmit power"**
   - Generates BLE advertising packet
   - TxP and ModAcc measurements
   - Delta F1/F2 modulation accuracy
   - Spec compliance validation

---

## Key Features

### 1. **IQPowerEdge Triggering by Default**
Every generated workflow uses IQPowerEdge triggering:
```csharp
measurement.Triggers.IQPowerEdgeTrigger.Configure("", 
    RFmxXXXIQPowerEdgeTriggerEnabled.True,
    -20.0,  // Trigger level
    RFmxXXXIQPowerEdgeTriggerSlope.Rising);
```

**Benefits**:
- No external trigger wiring
- Automatic acquisition start
- Reliable with bursted signals
- Simple configuration

### 2. **Complete Signal Generation**
Every workflow includes RFSG setup:
```csharp
rfsg = new NIRfsg("PXI1Slot7", false, false);
rfsg.Arb.LoadWaveformFromFileF64(waveformPath, "waveform_name");
rfsg.RF.Frequency = centerFrequency;
rfsg.RF.PowerLevel = outputPower;
rfsg.Arb.IQRate = iqRate;
rfsg.RF.OutputEnabled = true;
rfsg.Initiate();
```

### 3. **Pass/Fail Validation**
Every example includes spec limits and validation:
```csharp
bool evmPass = compositeRmsEvm < -32.0;  // 802.11ac 256-QAM limit
Console.WriteLine($"EVM PASS/FAIL: {(evmPass ? "PASS" : "FAIL")}");
```

### 4. **Proper Resource Management**
All examples use try-finally for cleanup:
```csharp
finally
{
    if (rfsg != null)
    {
        rfsg.Abort();
        rfsg.RF.OutputEnabled = false;
        rfsg.Dispose();
    }
    measurement?.Dispose();
    instrSession?.Dispose();
}
```

---

## Technical Patterns Documented

### Workflow Structure
1. **Initialize RFSG** → Create generator session
2. **Load waveform** → From file or generate in-code
3. **Configure RFSG** → Frequency, power, IQ rate
4. **Start generation** → Enable output, initiate, settle 100ms
5. **Initialize RFmx** → Create analyzer and personality sessions
6. **Configure trigger** → IQPowerEdge at -10 to -20 dBm
7. **Configure measurement** → Select measurement types, averaging
8. **Measure** → Initiate, fetch results
9. **Validate** → Compare against spec limits
10. **Cleanup** → Stop generation, disable output, dispose

### Triggering Best Practices
- **Default**: IQPowerEdge triggering
- **Trigger level**: Set 5-10 dB below expected signal level
- **Trigger slope**: Rising (most common)
- **Timeout**: 10-30 seconds for fetch operations

### Signal Settling
- Always wait 50-100ms after `rfsg.Initiate()` before starting measurements
- Allows signal to stabilize
- Prevents false triggers or measurement errors

---

## Files Modified

```
.agents/skills/ni-hw-drivers-csharp/
├── SKILL.md                                          [MODIFIED]
│   └── Updated description, added workflow reference
└── references/
    └── rfmx-generation-measurement-workflows.md     [NEW]
        ├── 4 complete workflow examples
        ├── IQPowerEdge trigger patterns
        ├── RFSG generation patterns
        ├── Pass/fail validation
        └── Troubleshooting guide
```

---

## Usage by LLM

When a user requests an RF measurement:

1. **LLM reads** `rfmx-generation-measurement-workflows.md` first
2. **LLM identifies** the wireless standard (WLAN/LTE/NR/BT)
3. **LLM selects** the appropriate workflow example
4. **LLM adapts** the example to user's specific parameters (frequency, bandwidth, etc.)
5. **LLM generates** complete code with:
   - RFSG signal generation
   - IQPowerEdge triggering
   - RFmx measurements
   - Pass/fail validation
   - Resource cleanup

**Result**: User gets production-ready, executable code from a single prompt.

---

## Benefits

### For Users
- **One-prompt measurements**: "Measure 802.11ac EVM" → complete code
- **No external signal source needed**: RFSG generates test signal
- **Automatic triggering**: IQPowerEdge handles timing
- **Spec compliance built-in**: Pass/fail validation included
- **Production-ready code**: Proper error handling and cleanup

### For Test Automation
- **Repeatable**: Same code generates consistent results
- **Self-contained**: No external equipment dependencies
- **Fast development**: Complete workflows in seconds
- **Validated patterns**: Based on NI best practices
- **Easy to customize**: Clear structure, well-commented

---

## Next Steps

This update enables the "one-prompt measurement" goal. Future enhancements could include:

1. **More wireless standards**: Add GSM, WCDMA, CDMA2k examples
2. **Multi-carrier scenarios**: CA (carrier aggregation) patterns
3. **Loopback testing**: VST TX+RX patterns
4. **Waveform generation**: In-code OFDM/QPSK generation functions
5. **TestStand integration**: Sequence step generation
6. **Data logging**: Auto-publish results to MDS

---

## Commit Details

**Commit**: `7f81205`  
**Message**: "Add complete RF generation+measurement workflows with IQPowerEdge triggering"

**Files Changed**:
- `.agents/skills/ni-hw-drivers-csharp/SKILL.md` (modified)
- `.agents/skills/ni-hw-drivers-csharp/references/rfmx-generation-measurement-workflows.md` (new, 783 lines)

**Push**: Successfully pushed to `origin/main`
