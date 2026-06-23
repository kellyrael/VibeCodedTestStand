# NI VST Family Specifications

**Purpose**: Complete side-by-side specifications for NI PXIe Vector Signal Transceivers (VSTs), sourced directly from official NI specification documents. Use this reference to answer hardware comparison and selection questions.

> **⚠️ DATA COMPLETENESS RULE:** Every cell in the comparison table MUST contain a concrete numeric value or specification. NEVER use placeholder text such as "See spec document", "See charts", "Per-port", or "See constituent module specs". If a value is not available, state "Not specified" with a brief reason (e.g., "Not specified — multi-module system, varies by configuration"). When adding new instruments or rows, always populate every cell with actual data.

**Source Documents**:
- PXIe-5841 Specifications (377850C-01, March 2026)
- PXIe-5842 Specifications
- PXIe-5860 Specifications (379054E-01, May 2026)
- PXIe-5831 Specifications

---

## Full Comparison Table

| Specification | **PXIe-5841** | **PXIe-5842** | **PXIe-5860** | **PXIe-5831** |
|---|---|---|---|---|
| **Type** | 2nd-gen VST (entry-level) | 2nd-gen VST (wideband) | Next-gen VST | mmWave VST |
| **Frequency Range** | 9 kHz – 6 GHz | 30 MHz – 8/12/18/26.5 GHz (options) | 50 MHz – 8.5 GHz | IF: 5–21 GHz; TRX TX: 22.5–31.3 GHz & 37–44 GHz; TRX RX: 22.5–44 GHz |
| **Max Instantaneous BW** | 200 MHz or 1 GHz (options) | 500 MHz / 1 GHz / 2 GHz (options); 4 GHz personality available | 1 GHz | 1 GHz |
| **Channels** | 1 (single) | 1 (single) | 1 or 2 (single-channel & dual-channel variants) | 2 IF channels (IF IN/OUT 0, IF IN/OUT 1) + mmWave TRX ports (Direct and Switched) |
| **RF Output Max Power** | +18 dBm (120 MHz–4 GHz, ≤200 MHz BW); +15 dBm (4–6 GHz); +10 dBm (4–6 GHz at 1 GHz BW) | +19 to +20 dBm (0.6–8 GHz); +18 dBm (8–20 GHz); down to 0 dBm at 26.5 GHz | +20 dBm (50 MHz–2 GHz); +18 dBm (2–5 GHz); +17 dBm (5–7 GHz); +15 dBm (7–8.5 GHz) | IF: +12 dBm leveled (5–18 GHz); +8 dBm (18–21 GHz) |
| **RF Input Max Level** | +30 dBm CW RMS (120 MHz–6 GHz); +15 dBm (9 kHz–120 MHz) | +25 dBm (reference level range) | +25 dBm CW RMS (reference level range, +26 dBm with 0 dB headroom) | IF: +20 dBm (5–21 GHz); TRX Direct: +5 dBm (22.5–44 GHz); TRX Switched: 0 dBm (22.5–44 GHz) |
| **RF Input Abs. Amplitude Accuracy (typ)** | ±0.2 dB (120 MHz–6 GHz); ±0.35 dB (10–120 MHz) | ±0.20 to ±0.35 dB (varies by freq range up to 26.5 GHz) | ±0.25 dB (50 MHz–8.5 GHz) | IF: ±0.5 dB (5–21 GHz); TRX: ±1.0 dB (22.5–44 GHz) |
| **RF Input Relative Accuracy (typ)** | ±0.2 dB (120 MHz–6 GHz) | ±0.15 to ±0.25 dB (varies by freq) | ±0.15 dB (50 MHz–8.5 GHz) | IF: ±0.3 dB (5–21 GHz); TRX: ±0.5 dB (22.5–44 GHz) |
| **RF Output Relative Accuracy (typ)** | ±0.3 dB (120 MHz–6 GHz) | ±0.25 to ±0.4 dB (varies by freq up to 26.5 GHz) | ±0.2 dB (50 MHz–8.5 GHz) | IF: ±0.4 dB (5–21 GHz); TRX: ±0.8 dB (22.5–44 GHz) |
| **RF Input Analog Gain Range** | ≥50–65 dB (varies by freq) | 60 dB nominal (30 MHz–26.5 GHz) | 56 dB (50 MHz–8.5 GHz) | IF: 50 dB (5–21 GHz) |
| **RF Output Analog Gain Range** | 75 dB nominal (120 MHz–6 GHz) | 85 dB nominal | 67 dB | IF: 60 dB (5–21 GHz) |
| **Phase Noise (SSB, 20 kHz offset)** | -102 dBc/Hz (<3 GHz); -102 dBc/Hz (3–4 GHz); -96 dBc/Hz (4–6 GHz) — standalone PXIe-5841 | -123 dBc/Hz @900 MHz; -121 dBc/Hz @2.4 GHz; -115 dBc/Hz @5.5 GHz; -111 dBc/Hz @10 GHz; -106 dBc/Hz @18 GHz (interpolated from 10 kHz/100 kHz offset table below) | -105 dBc/Hz @1 GHz; -103 dBc/Hz @2.4 GHz; -99 dBc/Hz @5.8 GHz; -97 dBc/Hz @8.5 GHz (typ) | IF: -103 dBc/Hz (5–7.1 GHz); -97 dBc/Hz (7.1–14.2 GHz); -95 dBc/Hz (14.2–21 GHz). TRX (Onboard): -97 to -103 dBc/Hz (22.5–44 GHz) |
| **Phase Noise (with PXIe-5655, 10 kHz offset)** | -127 dBc/Hz @2.4 GHz (typ); -120.9 dBc/Hz @5.8 GHz (typ) | N/A (uses PXIe-5655 by default) | N/A (no external LO) | N/A |
| **Freq Settling Time** | <400 µs (typ, standalone); <200 µs (with PXIe-5655) | ≤250 µs (typ) | ≤150 µs (measured) | LO1 Onboard: PXIe-5653 lock time (0.85–17 ms depending on step size) + 0.75–1.6 ms settling; LO1 Secondary: 0.5–1.0 ms |
| **Tuning Resolution** | 888 nHz | 8.89 µHz | <1 µHz | 4.45 µHz |
| **LO Step Size** | Fractional: programmable (500 kHz default); Integer: 10–200 MHz | ≤1 Hz | N/A (fixed internal LO) | IF (LO2): 2–4 MHz; TRX Onboard (LO1): <1 Hz; TRX Secondary: 8 MHz |
| **Gain Resolution** | 1 dB nominal | 1 dB nominal | 1 dB nominal | 1 dB nominal (analog); <0.1 dB (digital) |
| **Input Amplitude Settling** | <0.5 dB: 40 µs; <0.1 dB: 70 µs (typ) | <0.5 dB: 35 µs; <0.1 dB: 60 µs (typ) | <0.5 dB: 11 µs; <0.1 dB: 27 µs (measured) | <0.5 dB: 50 µs; <0.1 dB: 100 µs (typ, IF path) |
| **Output Amplitude Settling** | <0.5 dB: 45 µs; <0.1 dB: 75 µs (typ) | <0.5 dB: 35 µs; <0.1 dB: 60 µs (typ) | <0.5 dB: 11 µs; <0.1 dB: 27 µs (measured) | <0.5 dB: 50 µs; <0.1 dB: 100 µs (typ, IF path) |
| **LO Configuration** | ✅ Supported (Onboard, fractional/integer modes) | ✅ Supported (via PXIe-5655) | ❌ Not supported (fixed internal LO — all LO property APIs throw error -1074135022) | ✅ LO1 (Onboard via PXIe-5653 / Secondary via PXIe-3622) + LO2 (Onboard via PXIe-3622) |
| **Physical Channel in Resource Name** | Not required (`""`) | Not required (`""`) | **Required** (`"5860/0"`) — error -1074097891 without it | Per instrument configuration |
| **Module Size** | 2U, 2 slots; 4.1 cm × 12.9 cm × 21.1 cm | Multi-module (PXIe-5842 + PXIe-5655 required) | 3U, 2 slots; 84 mm × 129 mm × 40.62 mm | Multi-module (PXIe-5820 + PXIe-3622 + PXIe-5653 + mmRH-5582) |
| **Weight** | 794 g (28.0 oz) | ~2.5 kg total (PXIe-5842 + PXIe-5655 combined) | 900 g (1.98 lbs) | ~5 kg total (PXIe-5820 + PXIe-3622 + PXIe-5653 + mmRH-5582 combined) |
| **Companion Modules** | Optional PXIe-5655 (improves phase noise, freq settling) | PXIe-5655 (required); optional PXIe-5633 (VNA) | Standalone (no companion needed); optional PXIe-5633 (VNA) | PXIe-5653, PXIe-3622, mmRH-5582 (all required) |
| **Internal Freq Ref Accuracy** | ±200 × 10⁻⁹ initial; ±1 × 10⁻⁶/yr aging; ±1 × 10⁻⁶ temp | ±60 × 10⁻⁹ initial (via PXIe-5655 OCXO); ±160 × 10⁻⁹/yr aging; ±30 × 10⁻⁹ temp (15–35°C) | ±200 × 10⁻⁹ initial; ±1 × 10⁻⁶/yr aging; ±1 × 10⁻⁶ temp | LO1 Onboard: ±50 × 10⁻⁹ initial, ±100 × 10⁻⁹/yr aging, ±50 × 10⁻⁹ temp |
| **Warm-up Time** | 30 minutes | 30 minutes | 30 minutes | 30 minutes |
| **Connector Types** | SMA (RF IN/OUT) | SMA (RF IN/OUT) | SMA (RF IN/OUT, REF, PFI) | SMA (IF IN/OUT on PXIe-3622); 2.4 mm or 1.85 mm (mmRH-5582 TRX ports) |
| **Key Use Cases** | Wi-Fi (802.11a/b/g/n/ac/ax), cellular (sub-6 GHz LTE/NR), Bluetooth, general RF test, IoT | Wideband 5G sub-6 GHz, 5G NR FR1, mmWave (with 54 GHz freq extension via PXIe-5563), VNA (with PXIe-5633), multi-standard | High-performance sub-9 GHz RF test, Wi-Fi 6E/7 (6 GHz band), improved dynamic range, fast frequency settling, dual-channel | mmWave 5G NR FR2, satellite communications, radar, beamforming test at 22.5–44 GHz |

---

## PXIe-5842 Bandwidth Details

The PXIe-5842 has the most flexible bandwidth options of any NI VST:

| Center Frequency | 500 MHz BW Option | 1 GHz BW Option | 2 GHz BW Option |
|---|---|---|---|
| 30 MHz to <1.75 GHz | Up to 500 MHz* | Up to 1 GHz† | Up to 1.97 GHz‡ |
| 1.75 GHz to 2 GHz | 500 MHz | 1 GHz | 1 GHz |
| >2 GHz to 5.8 GHz | 500 MHz | 1 GHz | 1.4 GHz |
| >5.8 GHz to 26.5 GHz | 500 MHz | 1 GHz | 2 GHz |

\* BW = min[500 MHz, 2 × min(CF - 30 MHz, 2 GHz - CF)]
† BW = min[1 GHz, 2 × min(CF - 30 MHz, 2 GHz - CF)]
‡ BW = 2 × min(CF - 30 MHz, 2 GHz - CF); max 1.97 GHz at CF = 1.015 GHz

A **4 GHz Bandwidth personality** is also available for the PXIe-5842.

---

## PXIe-5841 Bandwidth Details

| Center Frequency | 1 GHz BW Option | 200 MHz BW Option |
|---|---|---|
| 9 kHz to <120 MHz | <120 MHz (direct acquisition) | <120 MHz |
| 120 MHz to 410 MHz | 50 MHz | 50 MHz |
| >410 MHz to 650 MHz | 100 MHz | 100 MHz |
| >650 MHz to 1.3 GHz | 200 MHz | 200 MHz |
| >1.3 GHz to 2.2 GHz | 500 MHz | 200 MHz |
| >2.2 GHz to 6 GHz | 1 GHz | 200 MHz |

---

## PXIe-5842 Phase Noise (Typical, 0 dBm Reference Level)

| Center Freq | 100 Hz | 1 kHz | 10 kHz | 100 kHz | 1 MHz | 10 MHz |
|---|---|---|---|---|---|---|
| 900 MHz | -102 | -118 | -129 | -140 | -145 | -146 |
| 2.4 GHz | -93 | -117 | -127 | -134 | -143 | -144 |
| 5.5 GHz | -86 | -111 | -121 | -128 | -140 | -142 |
| 10 GHz | -81 | -107 | -117 | -124 | -136 | -140 |
| 18 GHz | -75 | -102 | -112 | -119 | -131 | -136 |

All values in dBc/Hz.

---

## PXIe-5842 Output Power Details (Maximum Bandwidth Mode)

| Center Frequency | Spec Max Level (dBm) | Max Attainable Power (dBm, nominal) |
|---|---|---|
| 30–200 MHz | 15 | 23 |
| >200 MHz – 600 MHz | 19 | 23 |
| >600 MHz – <1.75 GHz | 19 | 23 |
| 1.75–4 GHz | 19 | 25 |
| >4–6 GHz | 20 | 25 |
| >6–8 GHz | 20 | 23 |
| >8–12 GHz | 18 | 23 |
| >12–18 GHz | 18 | 22 |
| >18–20 GHz | 18 | 22 |
| >20–22 GHz | 15 | 20 |
| >22–24 GHz | 10 | 18 |
| >24–25 GHz | 8 | 15 |
| >25–26.5 GHz | 0 | 6 |

---

## PXIe-5831 Frequency Details

| Port | Frequency Range | Notes |
|---|---|---|
| IF IN/OUT 0, IF IN/OUT 1 | 5 GHz – 21 GHz | Intermediate frequency ports on PXIe-3622 |
| TRX Ports (Transmit) | 22.5–31.3 GHz, 37–44 GHz | Direct and Switched TRX ports on mmRH-5582 |
| TRX Ports (Receive) | 22.5–44 GHz | Continuous receive coverage |
| Frequency Bandwidth | 1 GHz | Within specified frequency ranges |

### PXIe-5831 LO Architecture

- **LO1**: Responsible for up/down conversion between IF and mmWave frequencies
  - **Onboard**: Source is PXIe-5653 (best phase noise, slower settling for large steps)
  - **Secondary**: Source is PXIe-3622 internal synthesizers (faster settling, worse phase noise)
- **LO2**: Internal to PXIe-3622, responsible for baseband ↔ IF conversion
  - Source is always PXIe-3622 internal synthesizers

---

## Key Takeaways — Hardware Selection Guide

- **PXIe-5841**: Entry-level VST for sub-6 GHz work. Lowest cost, adequate for most Wi-Fi and cellular testing. Choose this for basic RF test needs where 200 MHz or 1 GHz bandwidth is sufficient.

- **PXIe-5842**: Widest frequency range (up to 26.5 GHz with options, 54 GHz with frequency extension) and highest bandwidth options (up to 4 GHz). Best for wideband 5G NR FR1, multi-standard testing, and applications requiring VNA capability (with PXIe-5633).

- **PXIe-5860**: Next-gen architecture with best-in-class frequency settling (150 µs), improved amplitude accuracy, simplified single-module design (no PXIe-5655 needed), and multi-channel capability. **No LO configuration APIs** — all LO property accesses throw errors. Must use `"5860/0"` resource name format.

- **PXIe-5831**: Purpose-built for mmWave frequencies (22.5–44 GHz) with IF ports at 5–21 GHz. Multi-module system (PXIe-5820 + PXIe-3622 + PXIe-5653 + mmRH-5582) designed for 5G NR FR2, satellite comms, and radar applications. Supports both Direct and Switched TRX port configurations.

### Quick Selection Matrix

| Application | Recommended VST |
|---|---|
| Wi-Fi 5/6 (802.11ac/ax, ≤160 MHz BW) | PXIe-5841 (1 GHz BW option) or PXIe-5860 |
| Wi-Fi 6E/7 (6 GHz band) | PXIe-5860 (covers to 8.5 GHz) |
| Wi-Fi 7 (320 MHz BW) | PXIe-5841 (1 GHz BW), PXIe-5842, or PXIe-5860 |
| LTE / 4G (sub-6 GHz) | PXIe-5841 or PXIe-5860 |
| 5G NR FR1 (sub-6 GHz, ≤400 MHz BW) | PXIe-5842 (1 GHz BW option) or PXIe-5860 |
| 5G NR FR1 wideband (>1 GHz BW) | PXIe-5842 (2 GHz BW option) |
| 5G NR FR2 (mmWave, 24–44 GHz) | PXIe-5831 |
| Bluetooth / IoT (sub-6 GHz, narrow BW) | PXIe-5841 (200 MHz BW option) |
| VNA / S-parameter measurements | PXIe-5842 + PXIe-5633 or PXIe-5860 + PXIe-5633 |
| Radar / EW (mmWave) | PXIe-5831 |
| Satellite comms (Ka-band) | PXIe-5831 |
| Fast frequency hopping / scanning | PXIe-5860 (150 µs settling) |
| Dual-channel / MIMO testing | PXIe-5860 (dual-channel variant) |
| Maximum output power (sub-6 GHz) | PXIe-5842 (up to +25 dBm attainable) |

---

## Programming Differences Summary

For detailed C# code patterns, see the `ni-hw-drivers-csharp` skill and `references/pxie-5860-vst.md`.

| Aspect | PXIe-5841 | PXIe-5842 | PXIe-5860 | PXIe-5831 |
|---|---|---|---|---|
| NIRfsg Constructor | `new NIRfsg("5841", true, false, "")` | `new NIRfsg("5842", true, false, "")` | `new NIRfsg("5860/0", true, false, "")` | Per instrument config |
| RFmxInstrMX Constructor | `new RFmxInstrMX("5841", "")` | `new RFmxInstrMX("5842", "")` | `new RFmxInstrMX("5860/0", "")` | Per instrument config |
| LO Source Configuration | ✅ Set via `rfsg.RF.LocalOscillator.Source` | ✅ Set via `rfsg.RF.LocalOscillator.Source` | ❌ Skip all LO config (throws error) | ✅ LO1 + LO2 configurable |
| Physical Channel | Not required | Not required | **Required** (append `/0`) | Per channel config |
| Runtime Detection | `rfsg.Identity.InstrumentModel.Contains("5841")` | `.Contains("5842")` | `.Contains("5860")` | `.Contains("5831")` |
