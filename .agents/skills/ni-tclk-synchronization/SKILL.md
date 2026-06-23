---
name: ni-tclk-synchronization
description: >
  Synchronize multiple NI modular instruments for phase coherent signal
  generation or acquisition using NI-TClk, reference clock sharing, and LO
  daisy-chaining. Use when the user asks about synchronizing VSTs, phase
  coherent generation, multi-instrument timing, TClk, sharing LOs, reference
  clocks, time-aligned acquisition, starting multiple generators
  simultaneously, or calibrating RF paths for phase alignment. Covers
  PXIe-5841/5842 VSTs and other NI modular instruments that support TClk.
argument-hint: >
  Describe the number and type of instruments to synchronize (e.g., "2 PXIe-5841
  VSTs"), the synchronization goal (phase coherent generation, time-aligned
  acquisition), and any phase/time offset or RF path calibration requirements.
user-invocable: true
---

# NI-TClk Synchronization

Synchronize multiple NI modular instruments for phase coherent signal generation
or time-aligned acquisition. Covers reference clock sharing, LO daisy-chaining,
LO frequency propagation, NI-TClk sample clock alignment, per-channel
phase/time offset control, and interferometric RF path calibration.

## CRITICAL: Read This First

**Before generating any multi-instrument synchronization code**, read
[`references/TCLK-SYNC-GUIDE.md`](references/TCLK-SYNC-GUIDE.md) for complete
patterns and API corrections:

- **MUST use .NET Framework 4.8** (same as all NI C# drivers)
- **Reference Clock**: All instruments must share `PxiClock` (10 MHz backplane)
- **LO Daisy Chain**: First VST exports LO (`LOOutEnabled = true`, `Source = Onboard`), subsequent VSTs receive (`Source = LOIn`)
- **LO Frequency**: After `RF.Configure()` on the LO-source VST, read `RF.LocalOscillator.Frequency` and set it on all receiving VSTs before their `RF.Configure()`
- **TClk**: Use `NITClk` constructor with `ITClkSessionReference[]`, then `ConfigureForHomogeneousTriggers()` -> `Synchronize()` -> `Initiate()`
- **Phase Offset**: Use `rfsg.RF.PhaseOffset` (degrees) per instrument
- **Time Delay**: Use `rfsg.DeviceEvents.SampleClockDelay` (seconds) per instrument
- **Do NOT call `rfsg.Initiate()` directly** - TClk manages initiation for all sessions
- **RF Path Calibration**: Use interferometric combiner method (two-pass null search) to calibrate different RF paths to the DUT

## Why This Skill Exists

Multi-instrument synchronization requires precise ordering of reference clock,
LO, LO frequency, TClk, and offset configuration. LLMs frequently get the
ordering wrong, use incorrect API calls, skip LO frequency propagation, or miss
critical steps like disabling automatic SG/SA shared LO. This skill provides
validated patterns from real PXIe-5841 VST testing.

## Supported Instruments

| Instrument | TClk Support | LO Sharing | Notes |
|---|---|---|---|
| PXIe-5841 VST | Yes | LO In/Out | Primary target |
| PXIe-5842 VST | Yes | LO In/Out | Primary target |
| PXIe-5840 VST | Yes | LO In/Out | Older VST |
| NI-RFSG (any) | Yes | Varies | Check hardware spec |
| NI-RFSA (any) | Yes | Varies | For synchronized acquisition |
| NI-SCOPE | Yes | N/A | Time-aligned digitizing |