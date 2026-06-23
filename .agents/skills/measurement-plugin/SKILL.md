---
name: measurement-plugin
description: >
  Convert Python scripts to NI Measurement Plug-Ins, scaffold new plug-ins, generate .measui UI files
  and .serviceconfig files for InstrumentStudio. Also use when creating a Python script or measurement
  that the user intends to later convert into a plug-in. Covers ni-measurement-plugin-sdk-service,
  MeasurementService decorators, gRPC service hosting, InstrumentStudio UI binding, .measui XML schema,
  .serviceconfig JSON format, pin-map session management, and TestStand integration.
argument-hint: "Describe the measurement: what inputs, what outputs, what hardware (if any), standalone script or full plug-in"
user-invocable: true
---

# Measurement Plug-In Skill

## Trigger

Use this skill when the user asks to:
- Convert an existing Python script into an NI Measurement Plug-In
- Build / scaffold a new measurement plug-in from scratch
- Create a Python measurement script intended for later plug-in conversion
- Generate or modify `.measui` UI files for InstrumentStudio
- Generate or modify `.serviceconfig` files
- Debug plug-in registration, UI binding, or decorator issues
- Understand the measurement plug-in project structure or SDK API

Also trigger on keywords: measurement plug-in, measurement plugin, measui, InstrumentStudio, MeasurementService, ni-measurement-plugin-sdk, service_config, serviceconfig, measurement-plugin-python, plug-in UI, measurement UI.

---

## Overview

NI Measurement Plug-Ins are Python gRPC services built with the `ni-measurement-plugin-sdk-service` package. Each plug-in exposes a measurement function that InstrumentStudio (or TestStand) can call. A plug-in project consists of:

| File | Purpose |
|---|---|
| `measurement.py` | Python entry point — defines configuration inputs, outputs, and the measurement logic |
| `<Name>.serviceconfig` | JSON — declares the service class, display name, version, and gRPC interfaces |
| `<Name>.measui` | XML — defines the InstrumentStudio UI panel (controls bound to configurations/outputs) |
| `pyproject.toml` | Poetry project — declares dependencies (`ni-measurement-plugin-sdk-service`, drivers, etc.) |
| `_helpers.py` | Utility module — logging setup, verbosity CLI option, TestStand support |
| `start.bat` | Launcher for static registration with NI Discovery Service |

---

## Critical Rules

1. **All IDs in `.measui` must be exactly 32 lowercase hexadecimal characters** — only digits `0-9` and letters `a-f`. No dashes, no uppercase, no letters `g-z`. NI's measurement UI parser rejects IDs that contain non-hex characters. Never use placeholder strings like `"INSERT_GUID_HERE"`. Example valid IDs: `a1f0e2d4b6c8498ea2d96e1f9c0b7d3a`, `b2e1f3c5d7a94b1c8e0f2a4d6c8b1e3f`. Generate a unique ID for every element.

2. **Channel paths follow the pattern**: `{ClientId}/Configuration/<Display Name>` for inputs and `{ClientId}/Output/<Display Name>` for outputs. The `<Display Name>` in the Channel attribute **must exactly match** the `display_name` string in the corresponding `@measurement_service.configuration()` or `@measurement_service.output()` decorator in `measurement.py`.

    - SDK display-name charset is restricted. Allowed characters are alphanumeric, spaces, and `().,;:!?-_'+`.
    - Do **not** use `/`, `\\`, `%`, or `^` in decorator display names.
    - Use safe substitutions, e.g. `Percent` instead of `%`, `per` instead of `/`, and `sq` instead of `^2`.

3. **Decorator order matters**:
   - `@measurement_service.register_measurement` goes on TOP (first decorator)
   - `@measurement_service.configuration(...)` decorators follow, one per input, in the **same order** as the function's positional parameters
   - `@measurement_service.output(...)` decorators follow, one per output, in the **same order** as the elements returned in the tuple

4. **The `ServiceClass` in the `.measui` `<Screen>` element must exactly match** the `serviceClass` in `.serviceconfig`.

5. **Enum types require a 0-valued member.** Every enum (Python `Enum` or protobuf enum) used in configuration or output must have a member with value `0`.

6. **Configuration types that are NOT allowed**: `Double2DArray`, `DoubleXYData`, `DoubleXYDataArray1D`, `String2DArray`. These are output-only types.

7. **Use `ni_measurement_plugin_sdk_service` as the import** (aliased as `nims`). This is the service package — not the meta-package.

8. **Output controls in `.measui` must be read-only**: Set `IsReadOnly="[bool]True"` on numeric/string controls, or `InteractionMode="[SelectorInteractionModes]ReadOnly"` on enum selectors.

9. **Input controls must have `Enabled="[bool]True"`**.

10. **The `.serviceconfig` must declare both v1 and v2 provided interfaces**:
    ```json
    "providedInterfaces": [
      "ni.measurementlink.measurement.v1.MeasurementService",
      "ni.measurementlink.measurement.v2.MeasurementService"
    ]
    ```

11. **Do not bind `DataType.Path` outputs to `ChannelStringControl` in `.measui`**. If an output is displayed with `ChannelStringControl`, declare it as `nims.DataType.String`. Use `Path` primarily for configuration inputs with `ChannelPathSelector`.

12. **Only use controls that exist in the measurement UI framework's supported schema.** The `.measui` format is a closed schema — do not invent, guess, or import XML element names that are not documented in `references/measui_schema.md`. The complete set of supported channel-bound controls is:

    | Category | Supported Controls |
    |---|---|
    | Numeric | `ChannelNumericText`, `ChannelSlider`, `ChannelKnob`, `ChannelGauge`, `ChannelMeter`, `ChannelTank`, `ChannelLinearProgressBar`, `ChannelRadialProgressBar` |
    | Boolean | `ChannelCheckBox`, `ChannelLED`, `ChannelSwitch`, `ChannelButton`, `ChannelImageButton` |
    | String | `ChannelStringControl` |
    | Enum | `ChannelEnumSelector`, `ChannelRingSelector` |
    | Pin / Path | `ChannelPinSelector`, `ChannelPathSelector` |
    | Array | `ChannelArrayViewer` (with `ChannelArrayNumericText` or `ChannelArrayStringControl` children) |
    | Graph | `ArrayGraph` (with `ArrayGraphAxis`, `HmiGraphPlot`, `HmiChartPlotLegend`, `HmiChartCursorLegend`, `HmiChartScaleLegend`, `ArrayGraphTools`) |
    | Layout | `ScreenSurfaceCanvas`, `TabControl` / `TabItem`, `Text`, `Line`, `Rectangle` |

    If a user asks for a UI element that is not in this list (e.g. a dropdown combo box, a table/grid, a tree view, a date picker, an image display, a progress spinner, or any HTML/WPF/WinForms control), **tell the user that control does not exist** in the InstrumentStudio measurement UI framework and suggest the closest supported alternative. The same applies to unsupported data dimensions — for example, there is no 2D array input control or 3D graph; if a user requests one, explain the limitation and propose a viable workaround (e.g. flattening to a 1D array, using multiple 1D arrays, or splitting across tabs). Do not silently substitute or fabricate an unsupported element.

---

## Reference Files

Read these before generating code:

| File | Contents |
|---|---|
| `references/measurement_plugin_sdk.md` | SDK API reference — DataType enum, MeasurementService class, decorator patterns, session management, project structure, pyproject.toml |
| `references/measui_schema.md` | .measui XML schema — all control types, Channel binding syntax, layout attributes, enum/ring selectors, array viewers, graphs, drawing elements, ValueFormatter patterns, namespace reference. **Source of truth** derived from InstrumentStudio's `ScreenEditorPalette.xml` and validated against real-world .measui files from `ni/measurement-plugin-python` and `NI-Measurement-Plug-Ins` repos. |

---

## File Naming Convention (from `ni-measurement-plugin-generator`)

The official `ni-measurement-plugin-generator` determines file names as follows:

1. **`display_name_for_filenames`** = display name with all whitespace stripped (e.g. `"Sample Measurement"` → `"SampleMeasurement"`)
2. **Folder** = `<DisplayNameNoSpaces>/` (one subfolder per measurement)
3. **Python entry point** = always **`measurement.py`** (never a custom name)
4. **Serviceconfig** = **`<DisplayNameNoSpaces>.serviceconfig`** (e.g. `SampleMeasurement.serviceconfig`)
5. **Measui** = **`<DisplayNameNoSpaces>.measui`** (e.g. `SampleMeasurement.measui`)
6. **Launcher** = always **`start.bat`** (never prefixed with measurement name)
7. **Helper module** = always **`_helpers.py`**
8. **Service class** default = **`<DisplayName>_Python`** (no org prefix unless explicitly specified)
9. **Measproj** (optional) = **`<DisplayNameNoSpaces>.measproj`**

Example: `ni-measurement-plugin-generator "PMIC Efficiency"` produces:
```
PMICEfficiency/
├── measurement.py                    ← always this name
├── PMICEfficiency.serviceconfig      ← display name, no spaces
├── PMICEfficiency.measui             ← display name, no spaces
├── PMICEfficiency.measproj           ← optional project file
├── _helpers.py                       ← always this name
├── start.bat                         ← always this name
```

Reference: real examples from `ni/measurement-plugin-python`:
- `sample_measurement/` → `measurement.py`, `SampleMeasurement.serviceconfig`, `SampleMeasurement.measui`, `_helpers.py`, `start.bat`
- `nidcpower_source_dc_voltage/` → `measurement.py`, `NIDCPowerSourceDCVoltage.serviceconfig`, `NIDCPowerSourceDCVoltage.measui`, `_helpers.py`, `start.bat`

---

## Workflow: Converting an Existing Python Script

### Definition Of Done (Must Be Complete Before Responding)

A measurement plug-in conversion is not complete unless all of the following exist and are wired correctly:

1. `measurement.py` with `MeasurementService(...)`, ordered decorators, and executable host entrypoint
2. `<DisplayNameNoSpaces>.serviceconfig` with matching `serviceClass`, `displayName`, version, and both v1/v2 interfaces
3. `<DisplayNameNoSpaces>.measui` with controls bound to every configuration/output channel and matching `ServiceClass`
4. `start.bat` that starts the measurement host from the project environment
5. `_helpers.py` with logging setup and verbosity CLI option
6. Dependency declaration (`pyproject.toml` or `requirements.txt`) including `ni-measurement-plugin-sdk-service`
7. Validation evidence:
    - Python syntax check passes
    - `.measui` parses as valid XML
    - Host starts and registers with discovery service

If any item above is missing, clearly state what is missing and do not present the conversion as complete.

### Step 0 — Move the Original Script into the Plug-In Folder

**Move** (not copy) the original script into the plug-in subfolder. Then have `measurement.py` import its `measure()` function instead of duplicating the logic. This keeps measurement logic in one place and preserves standalone testability via the script's `if __name__ == "__main__":` block.

```
<DisplayNameNoSpaces>/
├── <original_script>.py        ← moved here from its original location
├── measurement.py              ← thin wrapper that imports measure()
├── <DisplayNameNoSpaces>.serviceconfig
├── <DisplayNameNoSpaces>.measui
├── _helpers.py
└── start.bat
```

In `measurement.py`, import and wrap with SDK decorators:

```python
from <original_script> import measure as _measure

@measurement_service.register_measurement
@measurement_service.configuration("Input Name", nims.DataType.Double, 0.0)
@measurement_service.output("Output Name", nims.DataType.Double)
def measure(input_name: float) -> tuple[float]:
    return _measure(input_name)
```

### Step 1 — Analyze the Script
- Identify inputs (parameters the user would configure before running)
- Identify outputs (values the script produces / returns)
- Map each to a `DataType` from the SDK (see `references/measurement_plugin_sdk.md`)
- Identify any NI driver sessions (nidcpower, nidmm, niscope, etc.) — these use `IOResource` pins

### Step 2 — Create Project Structure

**Before scaffolding**, check whether a `.venv` directory already exists at the **workspace root** (i.e. the parent of the measurement subfolder). If it does, the project should reuse that environment instead of creating a per-plugin Poetry virtualenv:

- **Root `.venv` exists** → skip `pyproject.toml` and `poetry.toml`; install dependencies with `pip install` into the existing `.venv`; set `start.bat` to use `..\.venv\Scripts\python.exe measurement.py`.
- **No root `.venv`** → use Poetry as before (`pyproject.toml` + optional `poetry.toml`).

Each measurement lives in its own subfolder. Use the naming convention above:

```
<display_name_no_spaces>/
├── measurement.py                        ← always this name
├── <DisplayNameNoSpaces>.serviceconfig
├── <DisplayNameNoSpaces>.measui
├── _helpers.py                           ← always this name
├── pyproject.toml                        ← omit if reusing root .venv
├── start.bat                             ← always this name
└── poetry.toml      (optional — sets virtualenvs.in-project = true; omit if reusing root .venv)
```

### Step 3 — Build `measurement.py`
Follow the template in `references/measurement_plugin_sdk.md`. Key pattern:

```python
import ni_measurement_plugin_sdk_service as nims

measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "<DisplayNameNoSpaces>.serviceconfig",
    ui_file_paths=[service_directory / "<DisplayNameNoSpaces>.measui"],
)

@measurement_service.register_measurement
@measurement_service.configuration("Voltage Level", nims.DataType.Double, 5.0)
@measurement_service.output("Measured Voltage", nims.DataType.Double)
def measure(voltage_level: float) -> tuple[float]:
    # ... measurement logic ...
    return (measured_voltage,)
```

### Step 4 — Build `.serviceconfig`
See template in `references/measurement_plugin_sdk.md`.

### Step 5 — Build `.measui`
See control catalog in `references/measui_schema.md`. Every configuration and output needs a UI control with a matching Channel path.

### Step 6 — Dependencies

- **If reusing a root `.venv`**: First check whether each required package is already installed:
  ```
  pip show ni-measurement-plugin-sdk-service
  ```
  Only install packages that are **not** already present. No `pyproject.toml` needed.
- **Otherwise**: create a `pyproject.toml` with Poetry. Include `ni-measurement-plugin-sdk-service` and any driver packages as dependencies.

---

## Workflow: Creating a New Measurement Script (Pre-Plugin)

When the user wants a standalone Python script that can later be wrapped as a plug-in:
- Structure the code so inputs are function parameters and outputs are return values
- Use type hints matching SDK DataTypes (float, int, bool, str, list[float], Enum, etc.)
- Keep instrument session logic in the function body
- Add a `if __name__ == "__main__":` block for standalone testing
- Document which parameters will become configurations and which will become outputs

---

## DataType Quick Reference

| DataType | Python Type | .measui Control (Input) | .measui Control (Output) |
|---|---|---|---|
| `Float` | `float` | `ChannelNumericText` (ValueType=Single) | `ChannelNumericText` (IsReadOnly) |
| `Double` | `float` | `ChannelNumericText` (ValueType=Double) | `ChannelNumericText` (IsReadOnly) |
| `Int32` | `int` | `ChannelNumericText` (ValueType=Int32) | `ChannelNumericText` (IsReadOnly) |
| `Boolean` | `bool` | `ChannelCheckBox` | `ChannelLED` (Round/Square) |
| `String` | `str` | `ChannelStringControl` | `ChannelStringControl` (IsReadOnly) |
| `Enum` | `Enum` subclass | `ChannelEnumSelector` or `ChannelRingSelector` | `ChannelEnumSelector` (ReadOnly) |
| `DoubleArray1D` | `list[float]` | `ChannelArrayViewer` + `ChannelArrayNumericText` | Same (IsReadOnly) or `ArrayGraph` |
| `StringArray1D` | `list[str]` | `ChannelArrayViewer` + `ChannelArrayStringControl` | Same (IsReadOnly) |
| `IOResource` | `str` | `ChannelPinSelector` or `ChannelStringControl` | — |
| `Path` | `str` | `ChannelPathSelector` | — |
| `Double2DArray` | `Double2DArray` pb | — (output only) | `ChannelArrayViewer` (2D) / `ArrayGraph` |
| `DoubleXYData` | `DoubleXYData` pb | — (output only) | `ArrayGraph` with `HmiGraphPlot` |

For artifact file outputs (for example CSV/PNG paths), prefer `DataType.String` + read-only `ChannelStringControl`.

### Alternative Numeric Controls (can bind to Double/Float/Int32 channels)

| Control | Use Case | Key Attributes |
|---|---|---|
| `ChannelSlider` | Bounded numeric input | `Orientation`, `MinWidth`, `MinHeight` |
| `ChannelKnob` | Rotary numeric input | 125×125 default |
| `ChannelGauge` | Radial numeric output | `InteractionMode=EditRange` |
| `ChannelMeter` | Arc numeric output | 200×130 default |
| `ChannelTank` | Fill-level output | `Orientation=Vertical` |
| `ChannelLinearProgressBar` | Percentage output | `Minimum`, `Maximum` |
| `ChannelRadialProgressBar` | Circular percentage output | `FillBrush`, `Background` |

### Alternative Boolean Controls

| Control | Use Case | Key Attributes |
|---|---|---|
| `ChannelSwitch` | Toggle (Power/Round/Slider) | `Shape`, `Orientation` |
| `ChannelButton` | Momentary or toggle button | `IsMomentary`, `Content` |
| `ChannelImageButton` | Image-based toggle/indicator | `TrueImage`, `FalseImage`, `IsReadOnly` |

---

## Visual / Layout Elements

These are non-channel-bound elements for structuring the UI:

| Element | Use Case | Namespace |
|---|---|---|
| `Text` | Section headers, labels, unit annotations | PlatformFramework |
| `Line` | Vertical/horizontal dividers between sections | PlatformFramework |
| `Rectangle` | Decorative boxes and backgrounds | PlatformFramework |
| `FontSetting` | Child of Text/ChannelNumericText for custom font | PlatformFramework |
| `ScreenSurfaceCanvas` | Grouping container with background | ConfigurationBasedSoftware.Core |
| `TabControl` / `TabItem` | Multi-tab container for views | Controls.LabVIEW.Design |

---

## Common Mistakes to Avoid

1. **Mismatched display names** — The name in `@configuration("Voltage Level", ...)` must match the Channel path `{id}/Configuration/Voltage Level` in `.measui` exactly (case-sensitive, spaces included)
2. **Invalid display-name characters** — `@configuration()` / `@output()` display names reject `/`, `\\`, `%`, `^`; prefer `per`, `Percent`, `sq`
3. **Placeholder GUIDs** — Every `Id` attribute in `.measui` must be a unique 32-char lowercase hex string
4. **Missing 0-value enum member** — All enums must have a member with value 0
5. **Wrong decorator order** — `register_measurement` must be the outermost (first) decorator
6. **Using unsupported config types** — `Double2DArray`, `String2DArray`, `DoubleXYData` are output-only
7. **Forgetting `IsReadOnly` on outputs** — Output numeric/string controls must be read-only
8. **Mismatched ServiceClass** — `.measui` `ServiceClass` must match `.serviceconfig` `serviceClass`
9. **Dangling `LabelOwner` / `Graph` references** — Every `LabelOwner="[UIModel]..."` and every legend/tool `Graph="[UIModel]..."` must reference an existing element in the active XML (not a commented block)
10. **ArrayGraph channel/type mismatch** — Graph channels must map to real outputs in `measurement.py` with compatible output types (`DoubleArray1D` channels for array plots, `DoubleXYData` channels for XY plots)
11. **Partially commented graph blocks** — Never comment out only `<ArrayGraph>` while leaving labels/legends/tools that reference its Id
12. **Mismatched self-closing tags** — Do not write `<ScreenSurface ... />` and later `</ScreenSurface>`; use one style consistently
13. **Stray characters from copy/paste** — Never leave trailing markdown artifacts (such as backticks) in XML lines
14. **Path output bound to string control** — If `.measui` uses `ChannelStringControl` for an output path, the decorator type must be `DataType.String` (not `DataType.Path`), or InstrumentStudio can reject parameter configuration as invalid
15. **Do NOT add `xmlns` to `HmiGraphPlot` elements inside an `ArrayGraph`.** Although `HmiGraphPlot` belongs to the `InstrumentFramework/ScreenDocument` namespace in the schema, InstrumentStudio resolves it from the document-level `ParsableNamespace` declarations. Adding an inline `xmlns` causes the plot data source to appear as "Unmapped" in the UI editor. Only the parent `ArrayGraph` should carry an explicit `xmlns` (set to `ConfigurationBasedSoftware.Core`).

---

## ValueFormatter Quick Reference

| Format String | When to Use |
|---|---|
| `LV:G5` | Compact shorthand; best for array elements |
| `DisplayFormat=SystemInternational:Digits=5:DigitDisplayType=SignificantDigits:...` | Most common for standalone numerics (SI prefixes) |
| `DisplayFormat=Automatic:Digits=5:DigitDisplayType=SignificantDigits:...` | Default auto-scaling |
| `DisplayFormat=FloatingPoint:Digits=2:DigitDisplayType=DigitsOfPrecision:...` | Fixed decimal places |

The full suffix for all long-form formats is: `:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False`

---

## MeasUI Preflight Checks (Must Run Before Finalizing)

1. Verify every `Channel=".../Configuration/<name>"` and `Channel=".../Output/<name>"` has an exact `<name>` match in decorators.
2. Verify every `LabelOwner` target Id exists.
3. Verify every graph helper (`HmiChartPlotLegend`, `HmiChartCursorLegend`, `HmiChartScaleLegend`, `ArrayGraphTools`) points to an existing graph Id.
4. If disabling a graph, disable/remove all dependent label/legend/tool elements in the same edit.
5. Prefer a known-good graph pattern from a working file when generating from scratch.
6. Verify XML is well-formed: no mixed self-closing + explicit closing tags for the same element.
7. Verify all element `Id` attributes are unique 32-char lowercase hex strings (no dashes, no placeholders).
8. Verify `ServiceClass` in `<Screen>` matches `.serviceconfig` `serviceClass` exactly.
9. Verify `ClientId` GUID (with dashes, in braces) is consistent across all Channel attributes.
10. Verify every `HmiGraphPlot` has valid `HorizontalScale` and `VerticalScale` references to `ArrayGraphAxis` Ids.
11. Verify no `HmiGraphPlot` element carries an inline `xmlns` attribute — only the parent `ArrayGraph` should have an explicit namespace.
12. Verify no stray characters exist outside valid XML tokens.
