# RF Test GUI Patterns

Design rules and layout blueprints for building consistent RF/instrument automation operator UIs.

---

## Baseline UI Stack

- **Framework:** C# WinForms (.NET Framework 4.8)
- **Target style:** Standard Windows light/grey theme — `SystemColors.Control` background, system GroupBox borders, native control rendering
- **App pattern:** Desktop-first, keyboard/mouse friendly, low-friction for test engineers
- **Reference appearance:** NI WLAN Power Sweep tool style — GroupBox sections, inline label+control rows, flat blue primary buttons, dark log console, dark chart plot areas

---

## Preferred App Split

For larger projects, keep three focused GUI surfaces:

1. **Sequencer app** — Batch runs across matrix (standards × bands × bandwidths)
2. **Module runner app** — Single-point/manual EVM/TxP/SEM or equivalent
3. **Validation app** — Regression compare, tolerance checks, pass/fail report

If scope is small, merge into one app with a standard `TabControl` (works correctly on light themes).

---

## Visual Language

Apply these consistently:

- **Font family:** `Segoe UI`, 9pt default
- **Form/panel background:** `SystemColors.Control` (light grey) — do NOT use a custom dark background
- **Section grouping:** Use `GroupBox` with a descriptive `Text` title — do not simulate sections with custom panels
- **Input controls:** `TextBox` for free-text, `NumericUpDown` for numeric values (power, frequency, averaging, attenuation), `ComboBox` (DropDownList) for fixed-choice fields (standard, bandwidth)
- **Waveform file:** `TextBox` + `Button("Browse...")` side by side
- **Main actions** (`Run`, `Start Sweep`) as flat blue primary buttons (BackColor=`Color.FromArgb(0,120,215)`, ForeColor=White, FlatStyle=Flat, BorderSize=0)
- **Secondary actions** (`Stop`, `Export CSV`) as standard grey system buttons
- **Progress bar:** standard `ProgressBar` below the action buttons; set `ForeColor=Color.Lime` for green fill (Vista+)
- **Log console:** `RichTextBox` with dark background (`Color.FromArgb(20,20,20)`) and light monospace text (`Consolas 8.5pt`) — keeping the log dark improves readability in both light and dark environments
- **Status strip:** `StatusStrip` with colour-coded `ToolStripStatusLabel` dot: Idle=Gray, Running=Blue, Pass=Green, Fail=Red

---

## Layout Blueprint

Use a `SplitContainer` (or `TableLayoutPanel`) to divide the form into:

```
┌────────────────────────────┬──────────────────────────────────────────────┐
│  LEFT (~400-480 px)        │  RIGHT (fills remaining)                     │
│                            │                                              │
│  GroupBox: Hardware Config │  GroupBox: Sweep Results / Measurement Results│
│  GroupBox: Waveform Config │    ┌────────────────────────────────────────┐│
│  GroupBox: Meas Config     │    │  Chart 1 (e.g. EVM vs Power)           ││
│  ─────────────────────     │    ├────────────────────────────────────────┤│
│  [Run]  [Stop]  [Export]   │    │  Chart 2 (e.g. TxP vs Power)           ││
│  ▓▓▓▓▓▓▓▓▓▓ ProgressBar   │    ├────────────────────────────────────────┤│
│  ┌──── Log ─────────────┐  │    │  DataGridView (results table)           ││
│  │ dark RichTextBox     │  │    └────────────────────────────────────────┘│
│  └──────────────────────┘  │                                              │
└────────────────────────────┴──────────────────────────────────────────────┘
```

Keep resize behavior stable:
- **Do NOT use `SplitContainer`** — `SplitterDistance` is validated against the control's pixel width at assignment time; the width is 0 during construction/tab-building, so any value throws `InvalidOperationException`.
- Use a plain two-panel pattern instead:

```csharp
// Right panel first (Fill), then left panel (Left) — docking order matters
var rightPanel = new Panel { Dock = DockStyle.Fill };
page.Controls.Add(rightPanel);
var leftPanel  = new Panel { Dock = DockStyle.Left, Width = 480 };
page.Controls.Add(leftPanel);
```

- Left panel: fixed `Width`, `AutoScroll = true` so GroupBoxes are reachable at small heights
- Right panel: `Dock = Fill`; charts and grids scale with the window

---

## Chart Style

Charts sit on a light-grey form but use a **dark plot area** for contrast:

```csharp
var area = new ChartArea("main")
{
    BackColor   = Color.FromArgb(30, 30, 30),  // dark plot area
    BorderColor = Color.FromArgb(80, 80, 80)
};
```

- **Preferred chart type:** `SeriesChartType.Line` with `BorderWidth = 2` and markers (`MarkerStyle.Circle`, `MarkerSize = 6`) — NOT column/bar charts
- **Primary series colour:** `Color.FromArgb(255, 165, 0)` (NI orange), line chart
- **Secondary series:** `Color.FromArgb(0, 180, 255)` (blue) for avg power, `Color.FromArgb(255, 80, 80)` (red) for peak
- Use distinct `MarkerStyle` per series (`Circle`, `Triangle`, `Square`) to differentiate visually
- **Reference/ideal series:** dashed cyan or white
- Axis labels, grid lines, and title text in light grey (`Color.FromArgb(180,180,180)`)
- Chart `BackColor` = `SystemColors.Control` to match the form

```csharp
// ✅ CORRECT — line chart with markers (preferred)
var series = new Series("EVM") {
    ChartType = SeriesChartType.Line,
    Color = Color.FromArgb(255, 165, 0),
    BorderWidth = 2,
    MarkerStyle = MarkerStyle.Circle,
    MarkerSize = 6
};

// ❌ WRONG — column charts are not preferred for sweep results
var series = new Series("EVM") { ChartType = SeriesChartType.Column };
```

---

## Frequency Sweep Selection — Checkbox Pattern

For frequency sweep GUIs, **always provide checkboxes** for each sweep point so the user can select which channels/bands to measure. Include **Select All** / **Select None** buttons.

```csharp
// Field
private CheckBox[] freqCheckBoxes;

// In BuildFrequencySelectionGroup():
var gb = new GroupBox { Text = "Frequency Sweep Points", ... };
freqCheckBoxes = new CheckBox[SweepFrequencies.Length];
int t = 20;
for (int i = 0; i < SweepFrequencies.Length; i++)
{
    var cb = new CheckBox
    {
        Text = $"{SweepFrequencies[i].Band}  ({SweepFrequencies[i].FreqHz / 1e9:F3} GHz)",
        Left = 16, Top = t, Width = 300, Checked = true
    };
    freqCheckBoxes[i] = cb;
    gb.Controls.Add(cb);
    t += 22;
}

var btnAll = new Button { Text = "Select All", Left = 8, Top = t + 2, Width = 80, Height = 24 };
btnAll.Click += (s, e) => { foreach (var cb in freqCheckBoxes) cb.Checked = true; };
gb.Controls.Add(btnAll);

var btnNone = new Button { Text = "Select None", Left = 94, Top = t + 2, Width = 80, Height = 24 };
btnNone.Click += (s, e) => { foreach (var cb in freqCheckBoxes) cb.Checked = false; };
gb.Controls.Add(btnNone);
```

**Rules:**
- All checkboxes checked by default
- Validate at least one is selected before starting sweep
- Collect selected points into a filtered array before passing to the measurement loop
- Update `ProgressBar.Maximum` based on selected count, not total count

---

## GroupBox Layout Rules

Inside a GroupBox, use two-column inline rows:

```csharp
var lbl = new Label { Text = "Field Name:", Left = 8, Top = top + 3, Width = 100, AutoSize = false };
var ctl = new NumericUpDown { Left = 115, Top = top, Width = 90 };
gb.Controls.Add(lbl);
gb.Controls.Add(ctl);
```

- Labels right-aligned or left-aligned at a consistent left edge (e.g. `Left=8`)
- Controls aligned at a consistent left edge (e.g. `Left=115`)
- Two pairs per row for compact configs: `[Label1] [Ctrl1]   [Label2] [Ctrl2]`
- GroupBox height: calculate from content; add `~30 px` for GroupBox title overhead

---

## Control Sizing Reference

| Control         | Typical Height | Notes                                      |
|-----------------|---------------|--------------------------------------------|
| `Label`         | 18 px          | `AutoSize=false` for alignment              |
| `TextBox`       | 22 px          | Single-line                                |
| `NumericUpDown` | 22 px          | Set `DecimalPlaces`, `Minimum`, `Maximum`  |
| `ComboBox`      | 22 px          | `DropDownStyle=DropDownList`               |
| `CheckBox`      | 22 px          | Standard system rendering                  |
| `Button`        | 30-34 px       | Primary: 34 px / Secondary: 28-30 px       |
| `ProgressBar`   | 10-14 px       |                                            |
| `GroupBox`      | content + 30   | 30 px overhead for title + borders         |

---

## Interaction Rules

- Show deterministic progress (`current / total`) via ProgressBar and Label
- Stream logs incrementally; do not wait for run completion to update UI (`BeginInvoke`)
- Keep UI responsive by running instrument calls on `Task.Run`
- Disable Run button and enable Stop button during execution; reverse on completion/error/cancel

---

## Session Learnings — Critical WinForms Pitfalls

### ⚠️ Docking Order: Fill Must Be Added LAST

**Rule**: In `Controls.Add()` calls, always add `Dock=Fill` controls **after** all `Dock=Top`, `Dock=Bottom`, `Dock=Left`, and `Dock=Right` controls. WinForms resolves docking in reverse Controls order — the last-added Fill control gets whatever space remains.

❌ **WRONG — tab page or panel gets zero height, charts crash**:
```csharp
page.Controls.Add(rightPanel);   // Fill — added first, gets 0 height!
page.Controls.Add(headerGroup);  // Top — pushes Fill to 0
```

✅ **CORRECT — add anchored controls first, Fill last**:
```csharp
page.Controls.Add(headerGroup);  // Top — added first
page.Controls.Add(rightPanel);   // Fill — added last, gets remaining space
```

This applies to every container: `Form`, `TabPage`, `Panel`, `GroupBox`. Whenever charts or grids are invisible after layout, check the docking order first.

### ⚠️ TabControl with Hardware GroupBox at Top

When building a multi-tab form with a shared hardware config GroupBox at the top:

```csharp
// 1. Add the hardware GroupBox docked to Top
var grpHardware = new GroupBox { Text = "Hardware", Dock = DockStyle.Top, Height = 60 };
this.Controls.Add(grpHardware);

// 2. Add the TabControl docked to Fill — MUST come after the GroupBox in Controls
var tabs = new TabControl { Dock = DockStyle.Fill };
this.Controls.Add(tabs);
```

If the TabControl is added before the GroupBox, it gets zero height.

### ⚠️ NumericUpDown: Set Minimum/Maximum Before Value

Never set `Value` before `Minimum`/`Maximum`. If `Value` falls outside the range it gets clamped silently and the control shows the wrong initial value.

❌ **WRONG**:
```csharp
var num = new NumericUpDown { Value = 5.0M, Minimum = 1.0M, Maximum = 10.0M };
```

✅ **CORRECT**:
```csharp
var num = new NumericUpDown { Minimum = 1.0M, Maximum = 10.0M, Value = 5.0M };
// OR set them separately in order:
num.Minimum = 1.0M;
num.Maximum = 10.0M;
num.Value   = 5.0M;
```

### ⚠️ Reading NumericUpDown Value from Background Thread

`NumericUpDown.Value` returns `decimal`. When reading via `Invoke()` on a background thread, the boxed return type is `object`-wrapped `decimal` — **not** `double`. Casting directly to `double` throws `InvalidCastException`.

❌ **WRONG — throws InvalidCastException**:
```csharp
double freq = (double)Invoke(new Func<decimal>(() => numFreq.Value));
```

✅ **CORRECT — unbox as decimal first**:
```csharp
double freq = (double)(decimal)Invoke(new Func<decimal>(() => numFreq.Value));
```

### ⚠️ Do Not Use SplitContainer

`SplitContainer.SplitterDistance` is validated against the control's actual pixel width at assignment time. During construction (before the form is shown), width is 0, so any non-zero value throws `InvalidOperationException`.

Use the plain two-panel docking pattern instead (see Layout Blueprint above).

### Shared VST Resource TextBox Pattern (Multi-Tab Forms)

When both tabs need the same instrument session, declare the resource name TextBox at form level and read it once before starting any measurement. This avoids duplicating config controls across tabs:

```csharp
// Form-level field
private TextBox _txtVstResource;

// In BuildUI():
_txtVstResource = new TextBox { Text = "VST3_1", Width = 120 };
var grpHw = new GroupBox { Text = "Hardware", Dock = DockStyle.Top, Height = 60 };
grpHw.Controls.Add(new Label { Text = "VST Resource:", Left = 8, Top = 22 });
grpHw.Controls.Add(_txtVstResource);
_txtVstResource.Left = 110; _txtVstResource.Top = 20;
this.Controls.Add(grpHw);

// In both OnRunClicked handlers:
string resource = _txtVstResource.Text.Trim();
```

### Progress Reporting Pattern for Long Sweeps

For a sequencer running N points, update ProgressBar and a status label on each step:

```csharp
int total = sweepPoints.Count;
for (int i = 0; i < total; i++)
{
    // Run point i ...
    int pct = (int)((i + 1) * 100.0 / total);
    BeginInvoke((Action)(() =>
    {
        _progressBar.Value = pct;
        _lblStatus.Text = $"Point {i + 1} of {total}";
        AppendLog($"[{i+1}/{total}] freq={pt.FreqHz/1e9:F3} GHz  EVM={evm:F2} dB  TxP={txp:F2} dBm");
    }));
}
```

---

## Data and Output Behavior

- Always expose explicit paths for waveform mapping and CSV output
- Show result schema in UI (column names users will get in CSV)
- Support export actions directly from the GUI
- Persist last-used settings (resource name, folders, selected standards, bandwidths)

---

## TabControl Usage

- Use standard `TabControl` on light-theme apps — it renders correctly without any owner-draw hacks
- For dark-theme apps: **do not use TabControl** — OwnerDrawFixed is unreliable; replace with a hand-rolled panel + Button tab strip using `Visible` toggling
- Each TabPage should have `Padding = new Padding(8)` for content breathing room

---

## Known WinForms Pitfalls (Lessons Learned)

| Pitfall | Fix |
|---------|-----|
| `FlatAppearance.BorderColor = Color.Transparent` throws `NotSupportedException` at runtime | Use a matching opaque colour instead: `Color.FromArgb(r, g, b)` |
| `Dock = DockStyle.Top` stacking pushes controls off-screen in tall config sidebars | Use `AutoScroll = true` on the parent panel, or switch to absolute `SetBounds()` positioning with an explicit inner panel `Height` |
| `TabControl` OwnerDrawFixed: tab titles invisible on dark backgrounds | Replace with hand-rolled Button tab strip and `Visible` swap |
| `out` parameter into a C# auto-property (CS0206) | Use a local variable for the `out` arg, then assign to the property |
| `BackColor = Color.Transparent` on a `Panel` inside a non-transparent parent causes flicker | Set `BackColor` to match parent, or leave default |
| **`SplitContainer.SplitterDistance` throws `InvalidOperationException`** at runtime | Never use `SplitContainer`. Use `Dock=Left` fixed-width panel + `Dock=Fill` panel instead (see Layout Blueprint above). |
| **`NumericUpDown.Value` throws `ArgumentOutOfRangeException`** when value is outside default range (0–100) | Always set `Minimum` and `Maximum` **before** `Value`. Never use object initialisers for `NumericUpDown` — use sequential property assignment. |
| **`string.Contains(string, StringComparison)` throws CS1501** — 2-arg overload does not exist in .NET 4.8 | Use `str.IndexOf(value, comparison) >= 0` instead: `sc.SemStatus.IndexOf("Pass", StringComparison.OrdinalIgnoreCase) >= 0` |

---

## Reusable Implementation Checklist

Before finishing a GUI task, verify:

- [ ] All GroupBoxes have meaningful `Text` titles
- [ ] Numeric inputs use `NumericUpDown` (not `TextBox`)
- [ ] Fixed-choice inputs use `ComboBox` with `DropDownStyle=DropDownList`
- [ ] Run/start/stop flow works and prevents invalid concurrent actions
- [ ] Long operations do not freeze the UI (background `Task.Run` + `BeginInvoke` for UI updates)
- [ ] Live log panel updates during execution
- [ ] Results are visible in-app and export correctly to CSV
- [ ] Frequency sweep GUIs use checkboxes for point selection (with Select All / Select None)
- [ ] Charts use `SeriesChartType.Line` with markers — NOT column/bar charts
- [ ] Input validation catches bad frequencies/bandwidths/paths before run start
- [ ] ProgressBar updates correctly (`Maximum`, `Value`, or `Marquee` style)
- [ ] Form resizes gracefully (Dock=Left + Dock=Fill panels, anchored controls — NOT SplitContainer)
- [ ] Every `NumericUpDown` sets `Minimum`/`Maximum` before `Value` (never in object initialiser)
- [ ] No `SplitContainer` used anywhere in the form
- [ ] String contains-checks use `IndexOf(value, comparison) >= 0` — NOT `Contains(value, comparison)` (.NET 4.8)
