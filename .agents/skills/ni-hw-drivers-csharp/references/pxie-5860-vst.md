# PXIe-5860 VST — Hardware-Specific Patterns

**Purpose**: Documents PXIe-5860-specific differences from PXIe-5841/5842 VSTs discovered during integration. These are **runtime errors** that compile successfully but fail on hardware.

---

## Key Differences: PXIe-5860 vs PXIe-5841/5842

| Aspect | PXIe-5841/5842 | PXIe-5860 |
|---|---|---|
| Physical channel | Not required (`""`) | **Required** (`"0"`) |
| LO configuration (all properties) | ✅ Supported | ❌ **None supported** |
| NIRfsg constructor | `new NIRfsg("5841", true, false, "")` | `new NIRfsg("5860/0", true, false, "")` |
| RFmxInstrMX constructor | `new RFmxInstrMX("5841", "")` | `new RFmxInstrMX("5860/0", "")` |

---

## Error #1: Physical Channel Not Specified

**Error**: `ModularInstruments.NIRfsg: Physical channel not specified. Error code: -1074097891`

**Cause**: PXIe-5860 is a multi-channel VST. Unlike 5841/5842 which default to channel 0, the 5860 requires the channel to be explicitly specified in the **resource name** (not the option string).

❌ **WRONG** (passes channel in option string — causes option parse error):
```csharp
rfsg = new NIRfsg("5860", true, false, "0");  // "0" is option string, not channel!
```

❌ **WRONG** (no channel specified — causes -1074097891):
```csharp
rfsg = new NIRfsg("5860", true, false, "");
```

✅ **CORRECT** (channel in resource name):
```csharp
rfsg = new NIRfsg("5860/0", true, false, "");
instrSession = new RFmxInstrMX("5860/0", "");
```

**Pattern — try/catch to handle channel requirement, then query model**:
```csharp
string rfsgResource = vstResource;
NIRfsg rfsg;
try
{
    rfsg = new NIRfsg(rfsgResource, true, false, "");
}
catch (Exception ex) when (ex.Message.Contains("Physical channel not specified"))
{
    rfsgResource = vstResource + "/0";
    rfsg = new NIRfsg(rfsgResource, true, false, "");
}
string instrumentModel = rfsg.Identity.InstrumentModel;
bool is5860 = instrumentModel.Contains("5860");

// Use rfsgResource for RFmx session too
instrSession = new RFmxInstrMX(rfsgResource, "");
```

---

## Error #2: LO Configuration Not Supported

**Error**: `IVI: (Hex 0xBFFA0012) Attribute or property not supported. Error code: -1074135022`

**Cause**: PXIe-5860 uses a fixed internal LO architecture. **None of the LO-related properties or methods are supported** — this includes any RFSG LO source settings, RFmx/RFSA LO source settings, and SG/SA shared LO configuration. Any attempt to set any LO property will throw error `-1074135022`.

❌ **WRONG** (crashes on 5860 — all LO APIs fail):
```csharp
rfsg.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;
instrSession.SetLOSource("", "Onboard");
instrSession.SetAutomaticSGSASharedLO("", RFmxInstrMXAutomaticSGSASharedLO.Disabled);
```

✅ **CORRECT** (skip all LO configuration for 5860):
```csharp
if (!is5860)
{
    rfsg.RF.LocalOscillator.Source = RfsgLocalOscillatorSource.Onboard;
    instrSession.SetLOSource("", "Onboard");
    instrSession.SetAutomaticSGSASharedLO("", RFmxInstrMXAutomaticSGSASharedLO.Disabled);
}
```

---

## Detecting PXIe-5860 at Runtime

**Always use the instrument's model name** (from `rfsg.Identity.InstrumentModel`) to identify the hardware — never rely on the resource name or alias string, as users can assign arbitrary aliases.

Since creating an NIRfsg session on a PXIe-5860 without a physical channel fails immediately, use a try/catch pattern to detect and retry:

```csharp
string rfsgResource = vstResource;
NIRfsg rfsg;
try
{
    rfsg = new NIRfsg(rfsgResource, true, false, "");
}
catch (Exception ex) when (ex.Message.Contains("Physical channel not specified") || ex.Message.Contains("-1074097891"))
{
    // PXIe-5860 requires physical channel in resource name
    rfsgResource = vstResource + "/0";
    rfsg = new NIRfsg(rfsgResource, true, false, "");
}

// Now query the actual model to drive feature gating
string instrumentModel = rfsg.Identity.InstrumentModel;
bool is5860 = instrumentModel.Contains("5860");
```

**Why not check the alias/resource string?** Users can assign any alias (e.g., `"MyVST"`, `"RF_DUT1"`) via NI MAX. Only `Identity.InstrumentModel` reliably identifies the hardware.

---

## Summary of Unsupported Features on PXIe-5860

| Category | Supported on 5841/5842 | Supported on 5860 |
|---|---|---|
| LO configuration (all properties and methods) | ✅ | ❌ Skip entirely |
| Physical channel auto-detection | Defaults to single channel | Must specify `/0` in resource name |

---

## GUI Considerations

When building GUIs that support multiple VST models:
- LO Configuration controls (RFSG LO Source, RFmx LO Source, SG/SA Shared LO) should be **disabled or hidden** when PXIe-5860 is selected.
- Alternatively, skip applying those settings at runtime when the resource contains "5860".
- The VST Resource field should accept either `5860` (auto-appends `/0`) or `5860/0` (used as-is).
