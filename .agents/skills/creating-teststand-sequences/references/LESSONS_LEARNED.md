# Lessons Learned: Using `tsctl` From Codex

This file keeps only the non-obvious failure modes. The main skill already
covers the normal create, modify, save, and release workflow.

## 1. TestStand Object IDs Are Connection-Scoped

**Problem:** Commands fail with object-instance errors after a reopen or on a
new connection.

**Root cause:** TestStand object instance IDs are scoped to the gRPC
`connection-id`.

**Use this rule:**
- Reuse one `--connection-id` across a multi-command workflow.
- After `sequence open`, reacquire `sequenceFileId`, `sequenceId`, and `stepId`
  from live command output.
- Do not hard-code or reuse object IDs from a previous shell, a previous
  connection, or an earlier reopen cycle.

## 2. Existing-Step Edits Must Resolve Live Step State

**Problem:** `step resolve` or follow-up edits fail because the guessed step
name or cached step ID is no longer correct.

**Use this rule:**
- Open the file first, then get `MainSequence`, then resolve the step.
- If the exact step name is uncertain, run `step list` for the relevant group
  before `step resolve`.
- After reopening a file for persistence checks, resolve the step again instead
  of reusing the old `stepId`.

## 3. Prefer Direct `tsctl` Invocation Over Nested PowerShell

**Problem:** Nested `pwsh -Command` calls damage quoting, expand variables in the
wrong shell, or pass malformed paths.

**Use this rule:**
- Run `tsctl` directly or put the workflow in a `.ps1` script.
- Avoid wrapping a second PowerShell command string around `tsctl`.
- If a path value looks suspicious, validate it first with
  `tsctl doctor validate-path`.

## 4. Path Rules Depend On What TestStand Consumes

**Problem:** A path that works for one argument fails for another.

**Root cause:** TestStand string expressions and filesystem paths are not the
same thing.

**Use this rule:**
- Use forward slashes only for values that become TestStand string expressions,
  such as `--param-string test_dir=C:/Temp`.
- Use normal absolute Windows paths for `--module-path`, `sequence open --path`,
  and `sequence save --path`.
- Treat over-escaped values like `C:\\Temp\\demo.seq` as shell damage, not
  valid input.

## 5. Persisted Edit Verification Needs A Full Reopen Cycle

**Problem:** In-session edits appear to work, but persistence is not proven.

**Use this rule:**
- Save the sequence file.
- Release it.
- Reopen it, ideally on a fresh `--connection-id`.
- Reacquire live IDs.
- Read back the edited state with commands like `step get-limits` or
  `step get-module`.

This validation pattern was confirmed for updating existing step limits and for
rebinding an existing Python step to a different function.

## 6. Choose Output Modes That Match The Next Command

**Problem:** Extra parsing and brittle command chaining make workflows harder
than necessary.

**Use this rule:**
- Use `--output id` when the next command only needs one returned ID.
- Use `--query <field>` when one scalar field is needed from a richer payload.
- Use `--output json` when multiple fields need to be inspected or passed on.

## 7. Python Step Semantics Need A Few Special Cases

**Problem:** Python-backed TestStand steps can behave differently than a naive
Python caller expects.

**Use this rule:**
- Numeric values from TestStand commonly arrive as floats, so cast to `int()` in
  the Python module when integer behavior is required.
- TestStand may pass positional arguments to Python step functions even when the
  generated starter logic does not use them yet. Do not generate zero-argument
  function signatures for step entry points.
- For `NumericLimitTest`, map the return value to `Step.Result.Numeric`.
- Do not add a second return parameter to a Python step; update the existing one
  with `step return-value`.
- For standalone modules with external packages, create a local `.venv` and bind
  the step to it with `--venv-path` instead of assuming global packages exist.

## 8. Flow Control Steps (For/ForEach) Cannot Be Configured via `set-property`

**Problem:** Creating `NI_Flow_For` steps works, but setting loop expressions
(init, condition, increment) via `step set-property` fails because the property
paths (`TS.SData.InitExpr`, `Step.InitializationExpression`, etc.) are not
accessible through the gRPC API.

**Use this rule:**
- Do not attempt to generate TestStand For/ForEach loops with `tsctl`.
- Instead, flatten the test matrix \u2014 generate one step per test point with
  parameters for each dimension (standard, bandwidth, frequency, etc.).
- This approach also provides better TestStand traceability since each test
  point is an individually identifiable step with its own pass/fail outcome.

## 9. Negative Numeric Arguments Are Parsed As Flags

**Problem:** Passing `--low -60` or `--high -20` to `tsctl` causes a parse
error because `-60` is interpreted as a short flag, not a numeric value.

**Use this rule:**
- Use the `--flag=value` syntax for any negative numeric argument:
  `--low=-60` not `--low -60`.
- This applies to `--low`, `--high`, and any `--param-number` with negative
  default values.

## 10. TestStand Requires `virtualenv`, Not Python `venv`

**Problem:** `python -m venv` creates a virtual environment that TestStand
rejects with "Invalid virtual environment path. TestStand supports virtual
environment created using 'virtualenv' tool."

**Use this rule:**
- Install `virtualenv` via `pip install virtualenv`.
- Create the environment with `python -m virtualenv .venv`, not `python -m venv .venv`.
- Always validate with `tsctl doctor validate-python-env --venv-path <path>`
  before binding to a step.

## 11. PowerShell Execution Policy Blocks `.ps1` Scripts

**Problem:** Running a generated `.ps1` script via `powershell -File` fails
with `UnauthorizedAccess` because script execution is disabled by default on
many Windows systems.

**Use this rule:**
- Always invoke scripts with `-ExecutionPolicy Bypass`:
  `powershell -ExecutionPolicy Bypass -File script.ps1`
- When launching from a C# GUI, set this in `ProcessStartInfo.Arguments`.

## 12. String Parameters Are Stripped of Quotes by the Go CLI Parser

**Problem:** Passing TestStand string-literal expressions like `"PXI1Slot9_2"`
via `--param smuResource='"PXI1Slot9_2"'` or `[char]34` loses the surrounding
double quotes. The Go CLI parser consumes them, so TestStand receives a bare
identifier (`PXI1Slot9_2`) instead of a string literal (`"PXI1Slot9_2"`),
causing runtime errors when the .NET adapter evaluates the expression.

For paths with spaces (e.g., waveform paths), the unquoted value is split into
multiple arguments causing `unexpected argument` errors from the CLI parser.

**Use this rule:**
- When creating a step with `add-dotnet-action` or `add-dotnet-numeric-test`,
  use `--param` only for numeric/boolean parameters. Do not pass string
  parameters with `--param`.
- After creating the step, set each string parameter individually using
  `step param set-value` via `cmd /c` to preserve escaped quotes:

```powershell
function Set-StringParam($tsctl, $cid, $stepId, $paramName, $value) {
    $cmdLine = "`"$tsctl`" --connection-id $cid step param set-value --step-id $stepId --adapter dotnet --name $paramName `"--value-expr=\`"$value\`"`" --output json"
    cmd /c $cmdLine
}

# Usage:
Set-StringParam $tsctl $cid $stepId "smuResource" "PXI1Slot9_2"
Set-StringParam $tsctl $cid $stepId "waveformPath" "C:/Users/Public/Documents/National Instruments/RFIC Test Software/Waveforms/80211ax_80M_MCS11.tdms"
```

- The `cmd /c` approach with `\"value\"` inside the `--value-expr=` argument is
  the only reliable way to pass string literals containing spaces to `tsctl`
  from PowerShell.
- Simple strings without spaces (e.g., `"VST3_1"`) also require this pattern —
  PowerShell always strips `"` before it reaches the Go binary.

## 13. .NET DLL Assemblies Must Be Co-Located for TestStand

**Problem:** TestStand's .NET adapter loads the configured assembly but cannot
resolve its transitive dependencies (e.g., `NIDCPower.Fx40.dll` →
`Ivi.DCPwr.dll`), causing `Could not load file or assembly` errors at runtime
even though the code compiles and runs fine from Visual Studio or `dotnet run`.

**Root cause:** Console apps and WinForms projects use the standard .NET
assembly resolver which probes the GAC and the application base directory.
TestStand's .NET adapter resolves assemblies from the DLL's directory only — it
does not probe the GAC, IVI Foundation directories, or NI installation paths.

**Use this rule:**
- In the `.csproj` for any DLL called by TestStand, set `<Private>True</Private>`
  on **all** NI and IVI assembly references so MSBuild copies them to the output
  directory alongside the DLL.
- Explicitly reference transitive IVI dependencies that NI drivers depend on:

```xml
<Reference Include="Ivi.DCPwr">
  <HintPath>C:\Program Files\IVI Foundation\IVI\Microsoft.NET\Framework64\v2.0.50727\IviFoundationSharedComponents 2.0.0\Ivi.DCPwr.dll</HintPath>
  <Private>True</Private>
</Reference>
```

- After building, verify all required DLLs are in the output directory:
  `Get-ChildItem bin\Release\net48\*.dll | Select Name`
- If a new `Could not load file or assembly` error appears for an IVI assembly,
  copy all IVI Foundation assemblies in one shot:

```powershell
$iviDir = "C:\Program Files\IVI Foundation\IVI\Microsoft.NET\Framework64\v2.0.50727\IviFoundationSharedComponents 2.0.0"
Get-ChildItem "$iviDir\Ivi.*.dll" | Copy-Item -Destination $outputDir
```

## 14. TestStand .NET Steps Should Separate Init/Measure/Cleanup

**Problem:** A .NET step that initializes hardware, measures, and cleans up in
a single method causes repeated init/teardown cycles when called 100+ times in
a flattened test matrix. This causes driver state errors (e.g., NIDCPower
session conflicts) and is extremely slow.

**Use this rule:**
- Structure the .NET DLL with three static methods:
  - `Initialize()` — opens all hardware sessions (SMU, RFSG, RFmx). Called once
    from the TestStand **Setup** group as an `Action` step.
  - `MeasurePoint()` — retunes frequency/power and runs a single measurement.
    Called per test point from the **Main** group as a `NumericLimitTest` step.
    Uses a static counter and named signal configs (`"meas0"`, `"meas1"`, …) to
    avoid RFmx state machine errors.
  - `Cleanup()` — closes all hardware sessions. Called once from the **Cleanup**
    group as an `Action` step.
- Hold hardware sessions in `private static` fields so they persist across
  step calls within the same TestStand execution.
- This matches the TestStand setup/main/cleanup pattern and avoids 110×
  init/close cycles.

## 15. Python Step Functions Must Use Explicit Named Parameters

**Problem:** A Python step function using `*args, **kwargs` does not receive
the values configured with `--param-number` in TestStand. The step runs but all
parameters fall back to their defaults, ignoring the values shown in the Step
Settings panel.

**Root cause:** The TestStand Python adapter maps step parameters to function
arguments by name. When the function signature is `def f(*args, **kwargs)`,
TestStand has no named parameters to bind to, so the configured values are
silently dropped.

**Use this rule:**
- Always declare explicit named parameters in the Python function signature,
  matching the exact names used in `--param-number` / `--param-string`:
  ```python
  def run_test(vin_voltage=6.0, current_limit=25.0, *args, **kwargs):
  ```
- Do **not** rely on `kwargs.get("param_name", default)` as the primary
  parameter-passing mechanism.
- Keep `*args, **kwargs` at the end of the signature for forward compatibility,
  but put all configured parameters as explicit named arguments first.
- Cast parameter values (e.g., `int(num_steps)`) since TestStand commonly
  passes numeric values as floats.
