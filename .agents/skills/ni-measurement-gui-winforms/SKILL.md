---
name: ni-measurement-gui-winforms
description: "Build professional Windows Forms measurement GUIs for NI hardware instrumentation projects. Covers UI design patterns, theming, async measurement execution, data visualization (charts, grids), error handling, results export, and multi-app RF test workflows. Use when creating test & measurement applications with .NET Framework WinForms."
argument-hint: "Describe the measurement type, hardware (RFSA, RFSG, DMM, Scope, etc.), and desired UI features (live updates, charts, export, etc.)"
user-invocable: true
---

# NI Measurement GUI — Windows Forms Skill

Build professional, production-ready measurement GUIs for National Instruments hardware using Windows Forms and .NET Framework 4.8.

## Trigger Phrases

- "Create a measurement GUI for [NI hardware]"
- "Build a Windows Forms UI for RF measurements"
- "How do I make a GUI for NI-SCOPE measurements?"
- "Design a measurement application UI"
- "Create a test GUI with charts and data grids"
- "Build a WinForms app for DMM measurements"
- "Make a professional-looking measurement interface"
- "Add data visualization to my measurement app"
- "Build a test dashboard"
- "Create an operator UI for RF test"

## What This Skill Covers

### UI Components
- Main form layout and design
- Dark theme implementation (UiTheme class)
- Control styling (buttons, text boxes, combo boxes, grids, charts)
- Status bar for errors and progress
- Tab-based navigation
- Data grids for results tables
- Charts for data visualization (waveform plots, bar charts)
- Log/console output windows

### Measurement Workflow
- Async measurement execution (non-blocking UI)
- Progress reporting and cancellation
- Error handling and display
- Results storage and export (CSV)
- Configuration persistence

### Multi-App RF Test Patterns
- Sequencer app (batch runs across matrix)
- Module runner app (single-point/manual EVM/TxP/SEM)
- Validation app (regression compare, tolerance checks, pass/fail)
- When to merge into one tabbed app vs. keep separate

### Best Practices
- Separate measurement logic from UI code
- Responsive UI — never freeze during measurements
- Thread-safe UI updates via `InvokeRequired` / `BeginInvoke`
- Consistent theming via centralized `UiTheme` class
- Proper resource management with `using` statements
- Input validation before starting measurements

### Runtime Safety Rules (GUI — must follow, violations cause crashes)
- **Never use `SplitContainer`** — `SplitterDistance` throws `InvalidOperationException` when set before the control has a real width (e.g. inside tab construction). Use `Dock=Left` fixed panel + `Dock=Fill` panel.
- **Never set `NumericUpDown.Value` before `Minimum`/`Maximum`** — default `Minimum` is 0, so negative values throw `ArgumentOutOfRangeException`. Always set `Minimum` → `Maximum` → `Value` in that order. Never use object initialisers for `NumericUpDown`.
- **Never set `FlatAppearance.BorderColor = Color.Transparent`** — throws `NotSupportedException`. Use an opaque colour matching the background.
- **Docking order matters**: add `Dock=Fill` controls to a panel *before* `Dock=Left`/`Dock=Right` controls, or the Fill control won't expand correctly.
- **Do not use `TabControl` with dark themes** — system chrome overrides OwnerDraw, making tab labels invisible. Use a hand-rolled button strip instead.

## Architecture

```
Project/
├── MainForm.cs                    ← Main GUI form
├── MainForm.Designer.cs           ← Auto-generated designer code
├── UiTheme.cs                     ← Centralized theme/styling
├── MeasurementModule.cs           ← Measurement logic (separate from UI)
└── ResultsExporter.cs             ← CSV/file export utilities
```

## References

Read these before generating code:

- `references/rf-test-gui-patterns.md` — Layout blueprints, multi-app split guidance, visual language rules, chart styling, theming, frequency-sweep selection, WinForms runtime pitfalls, and interaction design for RF/instrument operator UIs
