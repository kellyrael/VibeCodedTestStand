# .measui XML Schema Reference

## Overview

A `.measui` file is an XML document that defines the InstrumentStudio UI panel for a measurement plug-in. It binds UI controls to measurement configurations (inputs) and outputs via Channel paths.

---

## Document Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="..." Timestamp="..." xmlns="http://www.ni.com/PlatformFramework">
  <SourceModelFeatureSet>
    <!-- Namespace declarations (use these exact values) -->
    <ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="Configuration Based Software Core" Name="http://www.ni.com/ConfigurationBasedSoftware.Core" OldestCompatibleVersion="6.3.0.49152" Version="9.15.0.49152" />
    <ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="LabVIEW Controls" Name="http://www.ni.com/Controls.LabVIEW.Design" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
    <ParsableNamespace AssemblyFileVersion="25.3.0.809" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="24.8.0.0" />
    <ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="Editor" Name="http://www.ni.com/PanelCommon" OldestCompatibleVersion="6.1.0.0" Version="6.1.0.49152" />
    <ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
    <ApplicationVersionInfo Build="25.3.0.809" Name="Measurement Plug-In UI Editor" Version="25.3.0.809" />
  </SourceModelFeatureSet>
  <Screen DisplayName="..." Id="..." ServiceClass="..." xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
    <ScreenSurface ...>
      <!-- UI controls go here -->
    </ScreenSurface>
  </Screen>
</SourceFile>
```

---

## Critical Elements

### Screen
```xml
<Screen DisplayName="My Measurement"
        Id="<32_hex_chars>"
        ServiceClass="com.example.MyMeasurement_Python"
        xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
```

- `DisplayName`: Measurement name shown in InstrumentStudio
- `Id`: Unique 32-character lowercase hex ID (GUID without dashes)
- `ServiceClass`: **Must exactly match** the `serviceClass` in `.serviceconfig`

### ScreenSurface
```xml
<ScreenSurface BackgroundColor="[SMSolidColorBrush]#00ffffff"
               Height="[float]600" Width="[float]800"
               Id="<32_hex_chars>"
               Left="[float]0" Top="[float]0"
               PanelSizeMode="Fixed"
               xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
```

---

## Channel Binding Syntax

Every interactive control uses a `Channel` attribute to bind to a measurement parameter:

```
Channel="[string]{ClientId}/Configuration/<Display Name>"   ← for inputs
Channel="[string]{ClientId}/Output/<Display Name>"           ← for outputs
```

- `{ClientId}` is a GUID with dashes (e.g., `{d001b29b-5739-42de-9c18-004303c47a0b}`)
- `<Display Name>` must **exactly match** the `display_name` argument in the corresponding `@measurement_service.configuration()` or `@measurement_service.output()` decorator

The same `ClientId` GUID is used for ALL controls in one `.measui` file. It can also be specified in the `<Screen>` element as the `ClientId` attribute (optional — only needed in SampleMeasurement.measui style).

---

## ID Rules

- Every XML element that has an `Id` attribute needs a **unique 32-character lowercase hex string**
- Examples: `ac8d5d6abc13430eba5b9b5008242f2e`, `b16b7fdf2cd2444aaba612c28dff288c`
- **Never** use placeholder strings, UUIDs with dashes, or duplicate IDs
- The `ClientId` in Channel paths IS a UUID with dashes in curly braces: `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`

---

## Control Catalog

> **Source of truth**: All snippets below are derived from the InstrumentStudio `ScreenEditorPalette.xml`.
> Every control lives in the `http://www.ni.com/ConfigurationBasedSoftware.Core` namespace unless noted otherwise.
> Replace `<32_hex>` with a unique 32-char lowercase hex ID, `{CLIENT_ID}` with the shared ClientId GUID (with dashes, in braces), and `<label_id>` with the label element's hex ID.

---

### ChannelNumericText — Numeric Input/Output

**Configuration (input):**
```xml
<ChannelNumericText
    Id="<32_hex>"
    BaseName="[string]Numeric"
    Channel="[string]{CLIENT_ID}/Configuration/Voltage Level"
    Enabled="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]36"
    Width="[float]70" Height="[float]24"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    ValueFormatter="[string]LV:G5"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

**Output (read-only indicator):**
```xml
<ChannelNumericText
    Id="<32_hex>"
    BaseName="[string]Numeric"
    Channel="[string]{CLIENT_ID}/Output/Measured Voltage"
    IsReadOnly="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]36"
    Width="[float]70" Height="[float]24"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    ValueFormatter="[string]LV:G5"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

`ValueType` options: `Single` (Float), `Double`, `Int32`, `Int64`, `UInt32`, `UInt64`

Optional attributes:
- `IsLabelBoundToChannel="[bool]True"` — auto-populates the label text from the channel name (useful when channel names are already descriptive)
- `Interval` — increment step; use `[float]1` or `[double]1` for Double, `[int]1` for Int32
- `TabIndex="[int]N"` — keyboard tab order (sequential across all controls)
- `RadixBase="[RadixBase]0"` and `RadixVisibility="[SMVisibility]Collapsed"` — hide the hex/octal/binary radix selector
- `ButtonsVisibility="[SMVisibility]Collapsed"` — hide the increment/decrement spinner buttons
- `UnitAnnotation="[string]"` — empty string hides unit display; set to e.g. `"[string]V"` to show a unit suffix
- **Large display output**: Add a `<FontSetting>` child for prominent readouts:
  ```xml
  <ChannelNumericText ... IsReadOnly="[bool]True" Height="[float]51" MinHeight="[float]51" ...>
      <FontSetting FontFamily="Segoe UI" FontSize="24" Id="<32_hex>"
          xmlns="http://www.ni.com/PlatformFramework" />
  </ChannelNumericText>
  ```

---

### ChannelSlider — Numeric Slider Input

```xml
<ChannelSlider
    Id="<32_hex>"
    BaseName="[string]Slider"
    Channel="[string]{CLIENT_ID}/Configuration/Voltage Level"
    Enabled="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]80"
    Orientation="[Orientation]Horizontal"
    Width="[float]150" Height="[float]50"
    MinWidth="[float]60" MinHeight="[float]50"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

For vertical: `Orientation="[Orientation]Vertical"`, `Width="[float]50"`, `Height="[float]150"`.

---

### ChannelGauge — Gauge Indicator (Output)

```xml
<ChannelGauge
    Id="<32_hex>"
    BaseName="[string]Gauge"
    Channel="[string]{CLIENT_ID}/Output/Temperature"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]80"
    Width="[float]170" Height="[float]170"
    MinWidth="[float]125" MinHeight="[float]125"
    InteractionMode="[NumericPointerInteractionModes]EditRange"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelMeter — Meter Indicator (Output)

```xml
<ChannelMeter
    Id="<32_hex>"
    BaseName="[string]Meter"
    Channel="[string]{CLIENT_ID}/Output/Voltage"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]80"
    Width="[float]200" Height="[float]130"
    MinWidth="[float]110" MinHeight="[float]65"
    InteractionMode="[NumericPointerInteractionModes]EditRange"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelKnob — Knob Input

```xml
<ChannelKnob
    Id="<32_hex>"
    BaseName="[string]Knob"
    Channel="[string]{CLIENT_ID}/Configuration/Gain"
    Enabled="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]80"
    Width="[float]125" Height="[float]125"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelLinearProgressBar — Progress Bar (Output)

```xml
<ChannelLinearProgressBar
    Id="<32_hex>"
    BaseName="[string]Progress Bar"
    Channel="[string]{CLIENT_ID}/Output/Progress"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]260"
    Width="[float]140" Height="[float]14"
    IsSegmented="[bool]False"
    Minimum="[double]0" Maximum="[double]100"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelRadialProgressBar — Radial Progress Bar (Output)

```xml
<ChannelRadialProgressBar
    Id="<32_hex>"
    BaseName="[string]Radial Progress Bar"
    Channel="[string]{CLIENT_ID}/Output/Completion"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]280"
    Width="[float]70" Height="[float]70"
    Background="[SMSolidColorBrush]#FFD2D5D8"
    FillBrush="[SMSolidColorBrush]#FF027CB8"
    Minimum="[double]0" Maximum="[double]100"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelTank — Tank Indicator (Output)

```xml
<ChannelTank
    Id="<32_hex>"
    BaseName="[string]Tank"
    Channel="[string]{CLIENT_ID}/Output/Fill Level"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]80"
    Orientation="[Orientation]Vertical"
    Width="[float]150" Height="[float]200"
    MinWidth="[float]50" MinHeight="[float]50"
    InteractionMode="[NumericPointerInteractionModes]EditRange"
    AdaptsToType="[bool]True"
    ValueType="[Type]Double"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelCheckBox — Boolean Input

```xml
<ChannelCheckBox
    Id="<32_hex>"
    BaseName="[string]Checkbox"
    Channel="[string]{CLIENT_ID}/Configuration/Enable Output"
    Content="Off/On"
    Enabled="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]91"
    Width="[float]88" Height="[float]17"
    MinWidth="[float]16" MinHeight="[float]16"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelLED — Boolean Output (Round or Square)

```xml
<ChannelLED
    Id="<32_hex>"
    BaseName="[string]Round LED"
    Channel="[string]{CLIENT_ID}/Output/In Compliance"
    Shape="[LEDShape]Round"
    IsReadOnly="[bool]true"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]91"
    Width="[float]30" Height="[float]30"
    MinWidth="[float]20" MinHeight="[float]20"
    TrueContent="[string]On" FalseContent="[string]Off"
    TrueBackground="[SMSolidColorBrush]#ff83ca9d"
    FalseBackground="[SMSolidColorBrush]#ff007133"
    ContentVisibility="[Visibility]Collapsed"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

Use `Shape="[LEDShape]Square"` for a square LED.

`TrueBackground` / `FalseBackground` are optional — they override the default on/off colors.

---

### ChannelSwitch — Boolean Toggle Input

**Power button:**
```xml
<ChannelSwitch
    Id="<32_hex>"
    BaseName="[string]Power Button"
    Channel="[string]{CLIENT_ID}/Configuration/Power"
    Shape="[SwitchShape]Power"
    Width="[float]55" Height="[float]55"
    ClickMode="[ClickMode]Press"
    IncludeInCapture="[bool]False"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

**Slider switch (vertical):**
```xml
<ChannelSwitch
    Id="<32_hex>"
    BaseName="[string]Switch"
    Channel="[string]{CLIENT_ID}/Configuration/Mode"
    Shape="[SwitchShape]Slider"
    TrueContent="On" FalseContent="Off"
    Orientation="[Orientation]Vertical"
    Width="[float]50" Height="[float]50"
    MinWidth="[float]12" MinHeight="[float]24"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

**Slider switch (horizontal):**
Same as above but `Orientation="[Orientation]Horizontal"`, `Width="[float]104"`, `Height="[float]28"`.

**Round switch:**
```xml
<ChannelSwitch
    Id="<32_hex>"
    BaseName="[string]Round Switch"
    Channel="[string]{CLIENT_ID}/Configuration/Enable"
    Shape="[SwitchShape]Round"
    TrueContent="On" FalseContent="Off"
    Width="[float]112" Height="[float]91"
    IncludeInCapture="[bool]False"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelButton — Boolean Momentary/Toggle Button

```xml
<ChannelButton
    Id="<32_hex>"
    BaseName="[string]Text Button"
    Channel="[string]{CLIENT_ID}/Configuration/Trigger"
    Shape="[ButtonShape]Square"
    Content="Button"
    IsMomentary="[bool]False"
    IncludeInCapture="[bool]False"
    Width="[float]75" Height="[float]30"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelStringControl — String Input/Output

**Input:**
```xml
<ChannelStringControl
    BaseName="[string]String"
    Channel="[string]{CLIENT_ID}/Configuration/DUT Serial"
    Enabled="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]138"
    Width="[float]72" Height="[float]24"
    AcceptsReturn="[bool]false"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Auto"
    HorizontalScrollBarVisibility="[ScrollBarVisibility]Hidden"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

**Output (read-only):**
```xml
<ChannelStringControl
    BaseName="[string]String"
    Channel="[string]{CLIENT_ID}/Output/Status Message"
    IsReadOnly="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]138"
    Width="[float]72" Height="[float]24"
    AcceptsReturn="[bool]false"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Auto"
    HorizontalScrollBarVisibility="[ScrollBarVisibility]Hidden"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelEnumSelector — Enum Input/Output

**Input:**
```xml
<ChannelEnumSelector
    BaseName="[string]Enum"
    Channel="[string]{CLIENT_ID}/Configuration/Color"
    Enabled="[bool]True"
    Label="[UIModel]<label_id>"
    Left="[float]30" Top="[float]355"
    Width="[float]136" Height="[float]24"
    AllowNonSequentialValues="[bool]True"
    AdaptsToType="[bool]True"
    Id="<32_hex>"
    Value="[int]0"
    xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
    <RingSelectorInfo DisplayValue="[string]NONE" IsEnabled="[bool]True" Value="[int]0" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]RED" IsEnabled="[bool]True" Value="[int]1" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]GREEN" IsEnabled="[bool]True" Value="[int]2" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]BLUE" IsEnabled="[bool]True" Value="[int]3" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
</ChannelEnumSelector>
```

**Output (read-only):**
```xml
<ChannelEnumSelector
    BaseName="[string]Enum"
    Channel="[string]{CLIENT_ID}/Output/Result Color"
    InteractionMode="[SelectorInteractionModes]ReadOnly"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]355"
    Width="[float]136" Height="[float]24"
    AllowNonSequentialValues="[bool]True"
    AdaptsToType="[bool]True"
    Id="<32_hex>"
    xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
    <RingSelectorInfo DisplayValue="[string]NONE" IsEnabled="[bool]True" Value="[int]0" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]RED" IsEnabled="[bool]True" Value="[int]1" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]GREEN" IsEnabled="[bool]True" Value="[int]2" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]BLUE" IsEnabled="[bool]True" Value="[int]3" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
</ChannelEnumSelector>
```

Key differences:
- Input: Has `Enabled="[bool]True"`, has `Value="[int]0"` (default selection)
- Output: Has `InteractionMode="[SelectorInteractionModes]ReadOnly"`, no `Enabled` or `Value`

The `RingSelectorInfo` children must match the enum members defined in Python. The `DisplayValue` is the member name, and `Value` is the integer value.

**Non-sequential values**: ChannelEnumSelector supports highly non-sequential integer values (e.g. nidmm Function enum: 0–5, 101, 104, 105, 108, 1001–1006). Always set `AllowNonSequentialValues="[bool]True"`.

---

### ChannelRingSelector — Ring Selector Input/Output

RingSelector is an alternative to EnumSelector. Use it for simple drop-down choices without a Python Enum class. It lives in the `ConfigurationBasedSoftware.Core` namespace (unlike ChannelEnumSelector which is in InstrumentFramework/ScreenDocument).

**Input with static items:**
```xml
<ChannelRingSelector
    BaseName="[string]Ring"
    Channel="[string]{CLIENT_ID}/Configuration/Signal Type"
    Width="[float]136" Height="[float]24"
    AdaptsToType="[bool]True"
    AllowNonSequentialValues="[bool]True"
    PopulateEnumWithChannelInfo="[bool]False"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]283"
    Id="<32_hex>"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <RingSelectorInfo DisplayValue="[string]DC" IsEnabled="[bool]True" Value="[int]0" ValueType="[Type]Int32" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]AC" IsEnabled="[bool]True" Value="[int]1" ValueType="[Type]Int32" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
    <RingSelectorInfo DisplayValue="[string]AC Volts DC Coupled" DisplayValueOverride="[string]" IsEnabled="[bool]True" Value="[int]2" ValueType="[Type]Int32" xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
</ChannelRingSelector>
```

- `DisplayValueOverride`: optional; when set to empty string `"[string]"`, the control shows `DisplayValue` unmodified
- `ValueType="[Type]Int32"` on each `RingSelectorInfo` is required when items have explicit types
- Unlike ChannelEnumSelector, RingSelector is in the `ConfigurationBasedSoftware.Core` namespace

**Output (read-only):**
```xml
<ChannelRingSelector
    BaseName="[string]Ring"
    Channel="[string]{CLIENT_ID}/Output/Selected Range"
    Width="[float]136" Height="[float]24"
    AdaptsToType="[bool]True"
    InteractionMode="[SelectorInteractionModes]ReadOnly"
    AllowNonSequentialValues="[bool]True"
    PopulateEnumWithChannelInfo="[bool]False"
    Id="<32_hex>"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelPinSelector — IOResource Pin Selector

```xml
<ChannelPinSelector
    BaseName="[string]Pin"
    Channel="[string]{CLIENT_ID}/Configuration/Pin"
    Width="[float]136" Height="[float]24"
    DataType="[Type]String"
    Enabled="[bool]True"
    AllowUndefinedValues="[bool]True"
    IsLabelBoundToChannel="[bool]False"
    SelectedResource="[NI_Core_DataValues_TagRefnum]Pin1"
    Label="[UIModel]<label_id>"
    Left="[float]31" Top="[float]36"
    Id="<32_hex>"
    xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument" />
```

- `SelectedResource`: default pin/resource shown before a session; value is an alias like `Pin1`, `NI_DMM_Pin`, etc.
- Multiple pin selectors can target different instruments (e.g. `source_pin` and `measure_pin`)

---

### ChannelImageButton — Toggle Images Button/Indicator

**Indicator (read-only):**
```xml
<ChannelImageButton
    Id="<32_hex>"
    BaseName="[string]Toggle Images Indicator"
    Channel="[string]{CLIENT_ID}/Output/Status Light"
    Width="[float]75" Height="[float]75"
    TrueImage="[UIModel]<true_img_id>"
    FalseImage="[UIModel]<false_img_id>"
    IsMomentary="[bool]False"
    IsReadOnly="[bool]true"
    IncludeInCapture="[bool]False"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <Image Stretch="[SMStretch]Fill" BaseName="[string]Image" Id="<true_img_id>"
        Source="pack://application:,,,/NationalInstruments.Hmi.Core;component/Resources/ImageButtonTrue_40x40.xml"
        xmlns="http://www.ni.com/PlatformFramework" />
    <Image Stretch="[SMStretch]Fill" BaseName="[string]Image" Id="<false_img_id>"
        Source="pack://application:,,,/NationalInstruments.Hmi.Core;component/Resources/ImageButtonFalse_40x40.xml"
        xmlns="http://www.ni.com/PlatformFramework" />
</ChannelImageButton>
```

**Button (input):**
Same structure but without `IsReadOnly`, and set `IsMomentary="[bool]True"` for push-button behavior.

---

### ChannelPathSelector — File Path Selector

```xml
<ChannelPathSelector
    BaseName="[string]Path"
    Channel="[string]{CLIENT_ID}/Configuration/Output File"
    Width="[float]136" Height="[float]24"
    FilterLabel="[null]" FilterPatterns="[null]"
    WrapText="[bool]False"
    InteractionMode="[PathSelectorInteractionModes]BrowseDialog, TextInput"
    Id="<32_hex>"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core" />
```

---

### ChannelArrayViewer — 1D Array Input/Output

**Numeric array input:**
```xml
<ChannelArrayViewer
    AdaptsToType="[bool]True"
    ArrayElement="[UIModel]<inner_control_id>"
    BaseName="[string]Numeric Array Input"
    Channel="[string]{CLIENT_ID}/Configuration/Voltage Levels"
    Columns="[int]1" Dimensions="[int]1"
    Enabled="[bool]True"
    Height="[float]120" Width="[float]104"
    Id="<32_hex>"
    IndexVisibility="[Visibility]Collapsed"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Label="[UIModel]<label_id>"
    Left="[float]30" Top="[float]201"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]4"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>0</p.DefaultElementValue>
    <ChannelArrayNumericText
        BaseName="[string]Numeric"
        Height="[float]24" Width="[float]72"
        Id="<inner_control_id>"
        ValueType="[Type]Double"
        ValueFormatter="[string]LV:G5" />
</ChannelArrayViewer>
```

**Numeric array output:**
```xml
<ChannelArrayViewer
    AdaptsToType="[bool]True"
    ArrayElement="[UIModel]<inner_control_id>"
    BaseName="[string]Numeric Array Output"
    Channel="[string]{CLIENT_ID}/Output/Results"
    Columns="[int]1" Dimensions="[int]1"
    Height="[float]120" Width="[float]104"
    Id="<32_hex>"
    IndexVisibility="[Visibility]Collapsed"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Label="[UIModel]<label_id>"
    Left="[float]239" Top="[float]201"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]4"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>0</p.DefaultElementValue>
    <ChannelArrayNumericText
        BaseName="[string]Numeric"
        Height="[float]24" Width="[float]72"
        Id="<inner_control_id>"
        IsReadOnly="[bool]True"
        ValueType="[Type]Double"
        ValueFormatter="[string]LV:G5" />
</ChannelArrayViewer>
```

**Boolean array input:**
```xml
<ChannelArrayViewer
    AdaptsToType="[bool]True"
    ArrayElement="[UIModel]<inner_control_id>"
    BaseName="[string]Boolean Array Input"
    Channel="[string]{CLIENT_ID}/Configuration/Channel Enable"
    Columns="[int]1" Dimensions="[int]1"
    Height="[float]120" Width="[float]104"
    Id="<32_hex>"
    IndexVisibility="[Visibility]Collapsed"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]4"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>false</p.DefaultElementValue>
    <ChannelArrayCheckBox
        Id="<inner_control_id>"
        BaseName="[string]Checkbox"
        Width="[float]88" Height="[float]17"
        Content="Off/On"
        MinWidth="[float]16" MinHeight="[float]16" />
</ChannelArrayViewer>
```

**Boolean array output:**
```xml
<ChannelArrayViewer
    AdaptsToType="[bool]True"
    ArrayElement="[UIModel]<inner_control_id>"
    BaseName="[string]Boolean Array Output"
    Channel="[string]{CLIENT_ID}/Output/Pass Fail"
    Columns="[int]1" Dimensions="[int]1"
    Height="[float]120" Width="[float]20"
    Id="<32_hex>"
    IndexVisibility="[Visibility]Collapsed"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]4"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>false</p.DefaultElementValue>
    <ChannelArrayBooleanLed
        Id="<inner_control_id>"
        BaseName="[string]Round LED"
        Shape="[LEDShape]Round"
        Width="[float]17" Height="[float]17"
        TrueContent="On" FalseContent="Off"
        IsReadOnly="[bool]true"
        MinWidth="[float]20" MinHeight="[float]20"
        ContentVisibility="[Visibility]Collapsed" />
</ChannelArrayViewer>
```

**String array input:**
```xml
<ChannelArrayViewer
    ArrayElement="[UIModel]<inner_control_id>"
    BaseName="[string]String Array Input"
    Channel="[string]{CLIENT_ID}/Configuration/Labels"
    Columns="[int]1" Dimensions="[int]1"
    Height="[float]120" Width="[float]106"
    Id="<32_hex>"
    IndexVisibility="[Visibility]Collapsed"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]4"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>""</p.DefaultElementValue>
    <ChannelArrayStringControl
        BaseName="[string]String"
        Id="<inner_control_id>"
        Height="[float]24" Width="[float]74"
        AcceptsReturn="[bool]false"
        HorizontalScrollBarVisibility="[ScrollBarVisibility]Hidden"
        VerticalScrollBarVisibility="[ScrollBarVisibility]Auto" />
</ChannelArrayViewer>
```

**String array output:**
```xml
<ChannelArrayViewer
    ArrayElement="[UIModel]<inner_control_id>"
    BaseName="[string]String Array Output"
    Channel="[string]{CLIENT_ID}/Output/Messages"
    Columns="[int]1" Dimensions="[int]1"
    Height="[float]120" Width="[float]106"
    Id="<32_hex>"
    IndexVisibility="[Visibility]Collapsed"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]4"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>""</p.DefaultElementValue>
    <ChannelArrayStringControl
        BaseName="[string]String"
        Id="<inner_control_id>"
        Height="[float]24" Width="[float]74"
        IsReadOnly="[bool]True"
        AcceptsReturn="[bool]false"
        HorizontalScrollBarVisibility="[ScrollBarVisibility]Hidden"
        VerticalScrollBarVisibility="[ScrollBarVisibility]Auto" />
</ChannelArrayViewer>
```

**2D Array viewer (output only):**
```xml
<ChannelArrayViewer AdaptsToType="[bool]True"
                    ArrayElement="[UIModel]<inner_id>"
                    BaseName="[string]Numeric Array Output"
                    Channel="[string]{CLIENT_ID}/Output/2D Data"
                    Columns="[int]3" Dimensions="[int]2"
                    FirstIndex="[ArrayElementIndex]0,0"
                    Height="[float]120" Width="[float]256"
                    Id="<32_hex>"
                    IndexVisibility="[Visibility]Collapsed"
                    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
                    Label="[UIModel]<label_id>"
                    Left="[float]239" Top="[float]482"
                    Orientation="[SMOrientation]Horizontal"
                    Rows="[int]4"
                    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <p.DefaultElementValue>0</p.DefaultElementValue>
    <ChannelArrayNumericText BaseName="[string]Numeric"
                             Height="[float]24" Width="[float]72"
                             Id="<inner_id>"
                             IsReadOnly="[bool]True"
                             ValueType="[Type]Double"
                             ValueFormatter="[string]LV:G5" />
</ChannelArrayViewer>
```

Key: `Dimensions="[int]2"` and `FirstIndex="[ArrayElementIndex]0,0"` for 2D.

---

### ArrayGraph — Array/XY Graph (Output)

Use these compatibility rules when binding graph channels:

1. `DoubleArray1D` output: bind one plot per output array channel, typically sharing the same horizontal index axis.
2. `DoubleXYData` output: bind plot channel directly to that XY output channel.
3. The graph `Channel` display name segment must exactly match the output decorator display name.
4. Do not mix channel names that are not present in `measurement.py` outputs.

Loader safety rules for graph blocks:

1. Every `LabelOwner="[UIModel]<id>"` must reference an existing element Id.
2. Every legend/tool `Graph="[UIModel]<graph_id>"` must reference an existing `<ArrayGraph Id="...">`.
3. If you comment/remove an `<ArrayGraph>`, also comment/remove labels and helper controls that reference that graph Id.
4. Avoid partial commenting that leaves dangling references.

XML well-formedness rules (critical):

1. Do not mix self-closing and explicit closing forms for the same element (for example, `<ScreenSurface ... />` must not also have `</ScreenSurface>`).
2. Ensure there are no stray characters after closing tags.
3. After generating or editing `.measui`, run an XML parse check before considering it complete.

**Canonical ArrayGraph (from palette — use this as the starting template):**
```xml
<ArrayGraph
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core"
    Id="<graph_id>"
    BaseName="[string]Array Graph"
    Label="[UIModel]<label_id>"
    Left="[float]420" Top="[float]38"
    Background="[SMSolidColorBrush]#00000000"
    Width="[float]500" Height="[float]300"
    MinWidth="[float]230"
    RenderMode="[RenderMode]Hardware"
    PreferIndexData="[bool]False"
    SuppressScaleLayout="[bool]False"
    PlotAreaMargin="[SMThickness]0,26,0,0">
    <!-- Horizontal axis -->
    <ArrayGraphAxis
        Orientation="[SMOrientation]Horizontal"
        Adjuster="[RangeAdjuster]FitExactly"
        Range="[IRange]0, 10"
        ValueType="[Type]Double"
        Label="Index"
        LabelVisibility="[SMVisibility]Collapsed"
        MinorTickVisibility="[SMVisibility]Collapsed"
        Id="<x_axis_id>"
        MajorDivisions="[UIModel]<x_div_id>">
        <RangeLabeledDivisions
            xmlns="http://www.ni.com/Controls.LabVIEW.Design"
            Id="<x_div_id>" />
    </ArrayGraphAxis>
    <!-- Vertical axis -->
    <ArrayGraphAxis
        Orientation="[SMOrientation]Vertical"
        Adjuster="[RangeAdjuster]FitExactly"
        Range="[IRange]0, 10"
        ValueType="[Type]Double"
        Label="Value"
        LabelVisibility="[SMVisibility]Collapsed"
        Id="<y_axis_id>"
        MajorDivisions="[UIModel]<y_div_id>">
        <RangeLabeledDivisions
            xmlns="http://www.ni.com/Controls.LabVIEW.Design"
            Id="<y_div_id>" />
    </ArrayGraphAxis>
    <!-- Plot bound to output channel -->
    <HmiGraphPlot
        Channel="[string]{CLIENT_ID}/Output/Waveform Data"
        Label="Waveform Data"
        HorizontalScale="[UIModel]<x_axis_id>"
        VerticalScale="[UIModel]<y_axis_id>"
        IsDefaultPlot="[bool]true"
        Id="<plot_id>" />
</ArrayGraph>
```

**Multiple-plot example (add more `HmiGraphPlot` children):**
```xml
<ArrayGraph ... Id="<graph_id>">
  <ArrayGraphAxis ... Id="<x_axis_id>" ... />
  <ArrayGraphAxis ... Id="<y_axis_id>" ... />
  <HmiGraphPlot Channel="[string]{CLIENT_ID}/Output/Efficiency Sweep (Percent)"
      Label="Efficiency Sweep (Percent)"
      HorizontalScale="[UIModel]<x_axis_id>"
      VerticalScale="[UIModel]<y_axis_id>"
      IsDefaultPlot="[bool]true"
      Id="<plot1_id>" />
  <HmiGraphPlot Channel="[string]{CLIENT_ID}/Output/Load Current Sweep (A)"
      Label="Load Current Sweep (A)"
      HorizontalScale="[UIModel]<x_axis_id>"
      VerticalScale="[UIModel]<y_axis_id>"
      IsDefaultPlot="[bool]false"
      Id="<plot2_id>" />
</ArrayGraph>
```

**Supporting elements (place as siblings AFTER the `</ArrayGraph>` closing tag):**
```xml
<!-- Plot legend (shows plot names) -->
<HmiChartPlotLegend
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core"
    Graph="[UIModel]<graph_id>"
    Visible="[bool]true"
    Left="[float]507" Top="[float]0"
    Height="[float]28"
    Id="<32_hex>" />

<!-- Cursor legend (hidden by default) -->
<HmiChartCursorLegend
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core"
    Graph="[UIModel]<graph_id>"
    Visible="[bool]false"
    MinHeight="[float]80"
    Width="[float]316"
    Left="[float]5" Top="[float]329"
    Id="<32_hex>" />

<!-- Scale legend (hidden by default) -->
<HmiChartScaleLegend
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core"
    Graph="[UIModel]<graph_id>"
    Visible="[bool]false"
    Width="[float]157" Height="[float]52"
    Left="[float]425" Top="[float]307"
    Id="<32_hex>" />

<!-- Graph toolbar (zoom, pan, reset) -->
<ArrayGraphTools
    Id="<tools_id>"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core"
    Graph="[UIModel]<graph_id>"
    Width="[float]122" Height="[float]26"
    OffsetX="[float]346" OffsetY="[float]0">
    <ComposableButton BaseName="Horizontal Zoom" Name="Horizontal Zoom"
        Id="<32_hex>" Top="[float]2" Left="[float]2"
        BackingCanDelete="[bool]false" Width="[float]28" Height="[float]22"
        Content="[UIModel]<img1_id>" PartName="PART_ZoomHorizontalButton" IsMomentary="[bool]False">
        <pf:Image Stretch="[SMStretch]Uniform" BaseName="Image" Id="<img1_id>"
            Source="pack://application:,,,/NationalInstruments.Hmi.Core;component/Resources/ZoomHorizontal.png"
            xmlns:pf="http://www.ni.com/PlatformFramework" />
    </ComposableButton>
    <ComposableButton BaseName="Vertical Zoom" Name="Vertical Zoom"
        Id="<32_hex>" Top="[float]2" Left="[float]32"
        BackingCanDelete="[bool]false" Width="[float]28" Height="[float]22"
        Content="[UIModel]<img2_id>" PartName="PART_ZoomVerticalButton" IsMomentary="[bool]False">
        <pf:Image Stretch="[SMStretch]Uniform" BaseName="Image" Id="<img2_id>"
            Source="pack://application:,,,/NationalInstruments.Hmi.Core;component/Resources/ZoomVertical.png"
            xmlns:pf="http://www.ni.com/PlatformFramework" />
    </ComposableButton>
    <ComposableButton BaseName="Pan" Name="Pan"
        Id="<32_hex>" Top="[float]2" Left="[float]62"
        BackingCanDelete="[bool]false" Width="[float]28" Height="[float]22"
        Content="[UIModel]<img3_id>" PartName="PART_PanButton" IsMomentary="[bool]False">
        <pf:Image Stretch="[SMStretch]Uniform" BaseName="Image" Id="<img3_id>"
            Source="pack://application:,,,/NationalInstruments.Hmi.Core;component/Resources/ZoomPan.png"
            xmlns:pf="http://www.ni.com/PlatformFramework" />
    </ComposableButton>
    <ComposableButton BaseName="Reset" Name="Reset"
        Id="<32_hex>" Top="[float]2" Left="[float]92"
        BackingCanDelete="[bool]false" Width="[float]28" Height="[float]22"
        Content="[UIModel]<img4_id>" PartName="PART_ResetButton" IsMomentary="[bool]True">
        <pf:Image Stretch="[SMStretch]Uniform" BaseName="Image" Id="<img4_id>"
            Source="pack://application:,,,/NationalInstruments.Hmi.Core;component/Resources/ZoomExtents.png"
            xmlns:pf="http://www.ni.com/PlatformFramework" />
    </ComposableButton>
</ArrayGraphTools>
```

---

### Labels

Every control should have a corresponding Label:

```xml
<Label Height="[float]16"
       Id="<label_id>"
       LabelOwner="[UIModel]<control_id>"
       Left="[float]31"
       Text="[string]Voltage Level"
       Top="[float]16"
       Width="[float]75"
       xmlns="http://www.ni.com/PanelCommon" />
```

- `LabelOwner`: References the `Id` of the control this label belongs to
- `Text`: The label text shown above the control
- Position the label above its control (same `Left`, `Top` about 20px above the control's `Top`)

---

### Text — Static Text Label (non-channel-bound)

**Simple text:**
```xml
<Text Text="[string]Section Header"
     xmlns="http://www.ni.com/PlatformFramework" />
```

**Styled section header (recommended for UI sections):**
```xml
<Text Height="[float]40" Id="<32_hex>" Left="[float]49"
    SizeMode="[TextModelSizeMode]Fixed"
    Text="[string]Configuration"
    TextAlignment="[TextAlignment]Left"
    TextWrapping="[TextWrapping]Wrap"
    Top="[float]53" Width="[float]200"
    xmlns="http://www.ni.com/PlatformFramework">
    <FontSetting FontFamily="Segoe UI" FontSize="18" FontStyle="Bold"
        Id="<32_hex>" />
</Text>
```

**Subsection label (smaller, no bold):**
```xml
<Text Height="[float]22" Id="<32_hex>" Left="[float]908"
    SizeMode="[TextModelSizeMode]Fixed"
    Text="[string]SOURCE CONFIGURATION"
    TextWrapping="[TextWrapping]Wrap"
    Top="[float]210" Width="[float]307"
    xmlns="http://www.ni.com/PlatformFramework">
    <FontSetting FontFamily="Segoe UI" FontSize="12" Id="<32_hex>" />
</Text>
```

Not bound to any channel. Use for section headings, annotations, or unit labels (e.g. `"(V)"`).

---

### Line — Visual Divider

**Vertical divider (between config and results sections):**
```xml
<Line ArrowLocation="[ArrowLocation]None"
    Data="[PathGeometry]M 0,0 L 0,600"
    Fill="[SMSolidColorBrush]#ff2b3033"
    Height="[float]600" Width="[float]0"
    Id="<32_hex>" Left="[float]894" Top="[float]17"
    ShapeBuilder="[string]"
    Stroke="[SMSolidColorBrush]#ffffffff"
    StrokeThickness="[float]2"
    xmlns="http://www.ni.com/PlatformFramework" />
```

**Horizontal divider:**
```xml
<Line ArrowLocation="[ArrowLocation]None"
    Data="[PathGeometry]M 0,0 L 844,0"
    Fill="[SMSolidColorBrush]#ff2b3033"
    Height="[float]0" Width="[float]844"
    Id="<32_hex>" Left="[float]0" Top="[float]514"
    ShapeBuilder="[string]"
    Stroke="[SMSolidColorBrush]#ffffffff"
    StrokeThickness="[float]2"
    xmlns="http://www.ni.com/PlatformFramework" />
```

For a subtle divider, add `Opacity="[float]0.6"`.

---

### ScreenSurfaceCanvas — Grouping Container

```xml
<ScreenSurfaceCanvas
    Id="<32_hex>"
    BaseName="Canvas"
    Width="[float]200" Height="[float]200"
    Background="[SMSolidColorBrush]#80808080"
    Label="[UIModel]<canvas_label_id>"
    Left="[float]40" Top="[float]40"
    xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
    <!-- Controls inside this group -->
</ScreenSurfaceCanvas>
<Label Height="[float]16"
       Id="<canvas_label_id>"
       LabelOwner="[UIModel]<canvas_id>"
       Left="[float]40"
       Text="[string]Measurement Configurations"
       Top="[float]20" Width="[float]154"
       xmlns="http://www.ni.com/PanelCommon" />
```

---

### TabControl — Tabbed Container

```xml
<sm:TabControl xmlns:sm="http://www.ni.com/Controls.LabVIEW.Design"
    SelectedIndex="[int]0"
    Width="[float]200" Height="[float]150"
    BaseName="Tab"
    Id="<32_hex>">
    <sm:TabItem Header="Tab 0">
        <pf:Canvas xmlns:pf="http://www.ni.com/PlatformFramework" />
    </sm:TabItem>
    <sm:TabItem Header="Tab 1">
        <pf:Canvas xmlns:pf="http://www.ni.com/PlatformFramework" />
    </sm:TabItem>
</sm:TabControl>
```

---

## Layout Guidelines

1. **Configurations on the left, Outputs on the right** — Standard convention
2. **Vertical spacing**: ~50-60px between controls (label + control)
3. **Label above control**: Label `Top` = control `Top` - 20
4. **Standard control sizes**: Numeric/String width=160, height=24; Checkbox height=16; LED height=20; ArrayViewer height=120
5. **Canvas groups**: Use `ScreenSurfaceCanvas` to group related controls with a header label
6. **Graphs**: Place to the right of scalar outputs, typically 300-500px wide and 250-300px tall

---

## Complete Minimal .measui Example

A measurement with one Float input and one Float output:

```xml
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" Timestamp="1DB76DDF80FECA6" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="Configuration Based Software Core" Name="http://www.ni.com/ConfigurationBasedSoftware.Core" OldestCompatibleVersion="6.3.0.49152" Version="9.15.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="LabVIEW Controls" Name="http://www.ni.com/Controls.LabVIEW.Design" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="25.3.0.809" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="24.8.0.0" />
		<ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="Editor" Name="http://www.ni.com/PanelCommon" OldestCompatibleVersion="6.1.0.0" Version="6.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.16.0.809" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="25.3.0.809" Name="Measurement Plug-In UI Editor" Version="25.3.0.809" />
	</SourceModelFeatureSet>
	<Screen DisplayName="My Measurement" Id="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6" ServiceClass="com.example.MyMeasurement_Python" xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
		<ScreenSurface BackgroundColor="[SMSolidColorBrush]#00ffffff" Height="[float]200" Id="f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6" Left="[float]0" PanelSizeMode="Fixed" Top="[float]0" Width="[float]500" xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
			<ChannelNumericText AdaptsToType="[bool]True" BaseName="[string]Numeric" Channel="[string]{d001b29b-5739-42de-9c18-004303c47a0b}/Configuration/Voltage Level" Enabled="[bool]True" Height="[float]24" Id="1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d" Interval="[float]1" Label="[UIModel]2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e" Left="[float]31" Top="[float]36" UnitAnnotation="[string]" ValueFormatter="[string]DisplayFormat=Automatic:Digits=5:DigitDisplayType=SignificantDigits:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False" ValueType="[Type]Double" Width="[float]160" />
			<Label Height="[float]16" Id="2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e" LabelOwner="[UIModel]1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d" Left="[float]31" Text="[string]Voltage Level" Top="[float]16" Width="[float]75" xmlns="http://www.ni.com/PanelCommon" />
			<ChannelNumericText AdaptsToType="[bool]True" BaseName="[string]Numeric" Channel="[string]{d001b29b-5739-42de-9c18-004303c47a0b}/Output/Measured Voltage" Height="[float]24" Id="3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f" IsReadOnly="[bool]True" Interval="[float]1" Label="[UIModel]4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a" Left="[float]260" Top="[float]36" UnitAnnotation="[string]" ValueFormatter="[string]DisplayFormat=Automatic:Digits=5:DigitDisplayType=SignificantDigits:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False" ValueType="[Type]Double" Width="[float]160" />
			<Label Height="[float]16" Id="4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a" LabelOwner="[UIModel]3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f" Left="[float]260" Text="[string]Measured Voltage" Top="[float]16" Width="[float]100" xmlns="http://www.ni.com/PanelCommon" />
		</ScreenSurface>
	</Screen>
</SourceFile>
```

---

## ValueFormatter Patterns

| Format | Usage |
|---|---|
| `LV:G5` | Compact shorthand (5 significant digits). Best for array elements and simple displays |
| `LV:G6` | 6 significant digits |
| `DisplayFormat=Automatic:Digits=5:DigitDisplayType=SignificantDigits:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False` | Default explicit formatting |
| `DisplayFormat=SystemInternational:Digits=5:DigitDisplayType=SignificantDigits:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False` | SI-style with metric prefixes (k, M, m, µ). Most common in real-world .measui files |
| `DisplayFormat=FloatingPoint:Digits=2:DigitDisplayType=DigitsOfPrecision:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False` | Fixed-point decimal (e.g. current limit) |
| `DisplayFormat=Automatic:Digits=0:DigitDisplayType=DigitsOfPrecision:...` | Integer display (0 decimal places) |

DigitDisplayType options:
- `SignificantDigits` — total significant figures (e.g. `5` → `3.3000`)
- `DigitsOfPrecision` — digits after decimal point (e.g. `2` → `3.30`)

---

## Namespace Summary

| Namespace URI | Used By |
|---|---|
| `http://www.ni.com/PlatformFramework` | Root `SourceFile`, `Text`, `Image`, `Line`, `Rectangle`, `Ellipse`, `Path`, `FontSetting`, `Canvas` |
| `http://www.ni.com/ConfigurationBasedSoftware.Core` | `ScreenSurface`, `ScreenSurfaceCanvas`, `ChannelNumericText`, `ChannelStringControl`, `ChannelSlider`, `ChannelKnob`, `ChannelGauge`, `ChannelMeter`, `ChannelTank`, `ChannelLinearProgressBar`, `ChannelRadialProgressBar`, `ChannelCheckBox`, `ChannelLED`, `ChannelSwitch`, `ChannelButton`, `ChannelImageButton`, `ChannelRingSelector`, `ChannelPathSelector`, `ChannelArrayViewer`, `ArrayGraph`, `ArrayGraphAxis`, `ArrayGraphTools`, `HmiChartPlotLegend`, `HmiChartCursorLegend`, `HmiChartScaleLegend` |
| `http://www.ni.com/InstrumentFramework/ScreenDocument` | `Screen`, `ChannelEnumSelector`, `ChannelPinSelector`, `HmiGraphPlot` ⚠️ |

> ⚠️ **`HmiGraphPlot`**: Do NOT add an inline `xmlns` to this element when it appears inside an `ArrayGraph`. InstrumentStudio resolves it from the document-level `ParsableNamespace` declarations. Adding `xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument"` directly on `HmiGraphPlot` causes its data source to appear as "Unmapped" in the UI editor. Only the parent `ArrayGraph` needs an explicit `xmlns` (set to `ConfigurationBasedSoftware.Core`).
| `http://www.ni.com/PanelCommon` | `Label` elements |
| `http://www.ni.com/Controls.LabVIEW.Design` | `RingSelectorInfo`, `RangeLabeledDivisions`, `PlotRenderer`, `TabControl`, `TabItem` |
