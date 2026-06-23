---
name: creating-teststand-sequences
description: >
  Create or modify NI TestStand sequence files with tsctl. Use when asked to
  generate a .seq file, add or reorder TestStand steps, build a shell workflow
  for TestStand sequence authoring, or translate test requirements into a
  TestStand sequence. Supports Python, LabVIEW, and .NET code modules.
---

# Creating TestStand Sequences

Use `tsctl` as the sequence-authoring interface.

## Locating tsctl

The `tsctl` executable is bundled with this skill at:

```
Skills_Dev_NICon-2026/.agents/skills/creating-teststand-sequences/tools/tsctl.exe
```

Before running any `tsctl` command, resolve the absolute path to this executable
relative to the workspace root. For example in PowerShell:

```powershell
$tsctl = Join-Path $workspaceRoot "Skills_Dev_NICon-2026\.agents\skills\creating-teststand-sequences\tools\tsctl.exe"
```

Then invoke it as `& $tsctl --connection-id ...` rather than assuming `tsctl` is
on the system PATH.

## Ensuring the TestStand Service Is Running

`tsctl` communicates with the TestStand engine via gRPC. The gRPC server is
provided by `ni.teststand.service.exe`, bundled at:

```
Skills_Dev_NICon-2026/.agents/skills/creating-teststand-sequences/tools/teststandservice/ni.teststand.service.exe
```

**Before running any `tsctl` command**, ensure the service is running and
ready. The service **must** be launched from its own directory so it can find
`teststand-service.serviceconfig` and `appsettings.json`.

Use `livez` as the single authoritative readiness check — always poll it,
whether or not the process appears to be running. A running process does not
guarantee the gRPC server is accepting connections. Only a successful `livez`
response means the service is ready.

PowerShell example:

```powershell
$serviceDir = Join-Path $workspaceRoot "Skills_Dev_NICon-2026\.agents\skills\creating-teststand-sequences\tools\teststandservice"
$serviceExe = Join-Path $serviceDir "ni.teststand.service.exe"

# Always check livez first — if it passes, the service is ready regardless of process state.
# If livez fails AND the process is not running, start it.
# If livez fails but the process IS running, it may still be initializing — just poll.
$ready = $false
try {
    Invoke-RestMethod -Uri "http://localhost:42001/api/ts-service/livez" -TimeoutSec 2 | Out-Null
    $ready = $true
} catch {}

if (-not $ready) {
    $running = Get-Process -Name "ni.teststand.service" -ErrorAction SilentlyContinue
    if (-not $running) {
        # Process is not running — start it from its own directory (required for config discovery)
        Start-Process -FilePath $serviceExe -WorkingDirectory $serviceDir -WindowStyle Hidden
    }
    # else: process is running but not yet healthy — just fall through to the polling loop
}

# Always poll livez until healthy (covers both fresh start and already-running cases)
$maxRetries = 15
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        Invoke-RestMethod -Uri "http://localhost:42001/api/ts-service/livez" -TimeoutSec 2 | Out-Null
        Write-Host "TestStand service is ready."
        break
    } catch {
        Start-Sleep -Seconds 1
    }
    if ($i -eq $maxRetries - 1) { Write-Error "TestStand service did not become ready." }
}
```

Alternatively, start it in an async terminal so you can see its logs:

```powershell
Set-Location $serviceDir; & $serviceExe
```

If `tsctl` returns an error like `"Failed to resolve service. No matches were
found."`, it means the service is not ready — start it, wait for `livez`, and retry.

## Launching TestStand Sequence Editor

Do not hard-code a TestStand version year. Discover the installed version first:

```powershell
$tsDir = Get-ChildItem "C:\Program Files\National Instruments\TestStand*" -Directory | Select-Object -Last 1
Start-Process (Join-Path $tsDir.FullName "Bin\SeqEdit.exe")
```

## Use This Workflow

1. Create a sequence file with `sequence create` (resolves `MainSequence`
   automatically).
2. Prefer helper commands for code-module-backed steps:
   - **Python**: `tsctl step add-python-action`, `tsctl step add-python-numeric-test`
   - **LabVIEW**: `tsctl step add-labview-action`, `tsctl step add-labview-numeric-test`
   - **.NET**: `tsctl step add-dotnet-action`, `tsctl step add-dotnet-numeric-test`
3. For existing files, reopen the file, resolve the target step, then edit it.
4. Fall back to primitive commands only when a helper does not fit.
5. Insert steps into `setup`, `main`, or `cleanup`.
6. Save with an absolute output path. Use `--release` to free engine memory.

## Required Rules

- **Never edit `.seq` files directly.** TestStand sequence files are binary —
  they cannot be created or modified by writing text or bytes to disk. Always
  use `tsctl` commands to create, modify, and save sequences.

- **Connection identity is mandatory.** Pick a short, stable connection name at
  the start of every workflow (e.g., `seq-build`) and pass
  `--connection-id <name>` on **every** `tsctl` command in that workflow.
  Omitting the flag generates a random UUID, which creates a new server-side
  session and loses all previously created objects (sequences, steps).
  Store the value in a variable (`$cid = "seq-build"`) and reference it
  everywhere:
  ```text
  tsctl --connection-id $cid sequence create --output json
  tsctl --connection-id $cid step add-python-action ...
  tsctl --connection-id $cid sequence save ...
  ```
- Prefer machine-readable output. Use `--query <field>` for a
  single scalar, and `--output json` when multiple fields are needed.
- `sequence create` returns both `sequenceFileId` and `sequenceId`. There is
  no need to call `sequence get` separately.
- Use `sequence save --release` to save and release in one step.
- Use an absolute path with `tsctl sequence save`.
- Prefer direct command invocation or a `.ps1` file over nested
  `pwsh -Command` when constructing `tsctl` workflows.
- Use forward slashes inside TestStand string expressions.
- Use normal Windows paths for `--module-path`, `--vi-path`, `--project-path`,
  `--assembly-path`, and `sequence save --path`.
- If path quoting is uncertain, run `tsctl doctor validate-path` first and use
  the normalized output.

### Python-Specific Rules

- When creating a new standalone Python module for TestStand, create a local
  `.venv` next to that module, install required packages there, validate it with
  `tsctl doctor validate-python-env`, and bind the step with `--venv-path`.
- If the Python code belongs to an existing Python project, reuse that
  project's existing environment and dependency workflow instead of creating a
  second `.venv`.
- Do not assume TestStand will call Python step functions with zero arguments.
  Starter functions should accept positional arguments even if they ignore them.
- Validate a standalone Python environment with
  `tsctl doctor validate-python-env --venv-path <value>` before binding it to a
  step when package availability is uncertain.

### LabVIEW-Specific Rules

- Assume LabVIEW is installed and available. Only use
  `tsctl doctor validate-labview-env` after a failure to diagnose problems.
- LabVIEW parameters are **discovered from the VI** via `LoadPrototype`, not
  created manually. The composite commands (`add-labview-action`,
  `add-labview-numeric-test`) call LoadPrototype automatically.
- Use `--param NAME=EXPR` to set LabVIEW parameter values by name. The category
  is auto-discovered from the VI connector pane.
- For `add-labview-numeric-test`, `--return-value` is **optional** when the VI
  has exactly one non-error output parameter — it is auto-mapped to
  `Step.Result.Numeric`. Specify `--return-value NAME=EXPR` only when the VI
  has multiple non-error outputs.
- LabVIEW composite commands require LabVIEW to be reachable at
  sequence-creation time (for LoadPrototype).

### .NET-Specific Rules

- Assume the .NET adapter is installed and available. Use
  `tsctl doctor validate-dotnet-env` after a failure to diagnose adapter
  availability.
- `.NET` parameters are discovered from the configured assembly member via
  `LoadPrototypeFromSignature`. The composite commands (`add-dotnet-action`,
  `add-dotnet-numeric-test`) load the prototype automatically.
- Use `--assembly-path` with a normal Windows DLL path and `--class-name` with
  the fully qualified .NET type name.
- Use `--create-object` when a step calls an instance member and should
  construct the .NET object before invoking that member.
- Use `--class-reference <expr>` when a step should reuse an existing object, or
  when a setup step should populate an object reference for later steps.
- `--dispose-object` is only valid together with `--create-object`.
- Use `--member-type constructor` when binding a constructor-only step with the
  primitive commands. Omit `--member-name` for constructors; provide it for
  methods and properties.
- Use `--param NAME=EXPR` to set .NET parameter values by name. **However,
  `--param` only works reliably for numeric and boolean values.** For string
  parameters, create the step first with numeric params only, then use
  `step param set-value` via `cmd /c` to set each string param (see Lessons
  Learned #12).
- For `add-dotnet-numeric-test`, `--return-value` is optional when the member
  exposes exactly one eligible numeric output or return value. Specify
  `--return-value NAME=EXPR` when multiple numeric outputs are available or when
  you want to override the auto-mapped result.
- `--class-reference` must point to an existing TestStand object-reference
  variable when you want to persist or reuse an object across steps.
- When building a .NET DLL for TestStand, set `<Private>True</Private>` on all
  NI and IVI assembly references so dependencies are copied alongside the DLL.
  TestStand does not probe the GAC or NI installation directories (see Lessons
  Learned #13).
- For test matrices with many steps calling the same DLL, structure the DLL
  with separate `Initialize` / `MeasurePoint` / `Cleanup` static methods
  mapped to TestStand setup/main/cleanup groups (see Lessons Learned #14).

## Core Commands For New Files — Python

```text
tsctl --connection-id <id> sequence create --output json
tsctl doctor validate-path --kind module --path C:/work/module.py --query normalized
tsctl doctor validate-python-env --venv-path C:/work/.venv --query venvPath
tsctl --connection-id <id> step add-python-action --sequence-id <sequence-id> --group setup --name <step-name> --module-path <module-path> --function-name <function-name> --venv-path <venv-path> --param-string test_dir=C:/Temp --output json
tsctl --connection-id <id> step add-python-numeric-test --sequence-id <sequence-id> --group main --name <step-name> --module-path <module-path> --function-name <function-name> --venv-path <venv-path> --param-number target=5.0 --low <value> --high <value> --output json
tsctl --connection-id <id> sequence save --id <sequence-file-id> --path <absolute-output-path> --release --output json
```

## Core Commands For New Files — LabVIEW

```text
tsctl --connection-id <id> sequence create --output json
tsctl doctor validate-path --kind module --path C:/work/test.vi --query normalized
tsctl --connection-id <id> step add-labview-action --sequence-id <sequence-id> --group setup --name <step-name> --vi-path <vi-path> --param Timeout=5000 --output json
tsctl --connection-id <id> step add-labview-numeric-test --sequence-id <sequence-id> --group main --name <step-name> --vi-path <vi-path> --low <value> --high <value> --output json
tsctl --connection-id <id> sequence save --id <sequence-file-id> --path <absolute-output-path> --release --output json
```

## Core Commands For New Files — .NET

```text
tsctl doctor validate-dotnet-env --output json
tsctl --connection-id <id> sequence create --output json
tsctl doctor validate-path --kind module --path C:/work/DotNetTest.dll --query normalized
tsctl --connection-id <id> step add-dotnet-action --sequence-id <sequence-id> --group setup --name <step-name> --assembly-path <assembly-path> --class-name <class-name> --member-name <member-name> --create-object --param station=Locals.Station --output json
tsctl --connection-id <id> step add-dotnet-numeric-test --sequence-id <sequence-id> --group main --name <step-name> --assembly-path <assembly-path> --class-name <class-name> --member-name <member-name> --create-object --low <value> --high <value> --output json
tsctl --connection-id <id> sequence save --id <sequence-file-id> --path <absolute-output-path> --release --output json
```

## LabVIEW Primitive Commands

When the composite commands do not fit, use these primitives:

```text
tsctl --connection-id <id> step create --type Action --labview --vi-path <vi-path> --output id
tsctl --connection-id <id> step set-module --step-id <step-id> --vi-path <vi-path> --project-path <lvproj-path> --output json
tsctl --connection-id <id> step get-module --step-id <step-id> --adapter labview --output json
tsctl --connection-id <id> step load-prototype --step-id <step-id> --output json
tsctl --connection-id <id> step param list --step-id <step-id> --output json
tsctl --connection-id <id> step param set-value --step-id <step-id> --name <param-name> --value-expr <expr> --output json
```

## .NET Primitive Commands

When the composite commands do not fit, use these primitives:

```text
tsctl doctor validate-dotnet-env --output json
tsctl --connection-id <id> step create --type Action --dotnet --assembly-path <assembly-path> --class-name <class-name> --member-name <member-name> --output id
tsctl --connection-id <id> step set-module --step-id <step-id> --adapter dotnet --assembly-path <assembly-path> --class-name <class-name> --member-name <member-name> --member-type <member-type> --create-object --class-reference <expr> --output json
tsctl --connection-id <id> step get-module --step-id <step-id> --adapter dotnet --output json
tsctl --connection-id <id> step load-prototype --step-id <step-id> --adapter dotnet --output json
tsctl --connection-id <id> step param list --step-id <step-id> --adapter dotnet --output json
tsctl --connection-id <id> step param set-value --step-id <step-id> --adapter dotnet --name <param-name> --value-expr <expr> --output json
```

## Python Dependencies

Use this rule when Codex generates Python for TestStand:

1. If the code is part of an existing Python project, reuse that project's
   dependency and environment setup.
2. If the code is a new standalone module, create a module folder, create a
   local `.venv`, install dependencies there, and pass that environment to the
   step with `--venv-path`.
3. Do not rely on globally installed packages such as `psutil`.
4. Keep the dependency declaration with the module so the environment can be
   recreated.

## Python Function Signatures

TestStand Python steps should use tolerant entry-point signatures.

1. Do not generate zero-argument Python entry points for step functions.
2. Python functions used by `Action` and `NumericLimitTest` steps should accept
   positional arguments from TestStand, even when the current implementation
   does not need them.
3. Prefer signatures like `def measure(*args, **kwargs):` or a named parameter
   followed by `*args, **kwargs` when you know one argument will be passed.
4. If a value is configured with `--param-number`, `--param-string`, or another
   step parameter, make sure the Python function signature can accept what
   TestStand passes at runtime.
5. For generated starter modules, favor permissive signatures first and tighten
   them only when the exact calling convention has been verified.

## Core Commands For Existing Files

```text
tsctl doctor validate-path --kind save --path C:/work/existing.seq --query normalized
tsctl --connection-id <id> sequence open --path <absolute-sequence-path> --output id
tsctl --connection-id <id> sequence get --file-id <sequence-file-id> --query sequenceId
tsctl --connection-id <id> step list --sequence-id <sequence-id> --group main --output json
tsctl --connection-id <id> step resolve --sequence-id <sequence-id> --group main --name <step-name> --query stepId
tsctl --connection-id <id> step get-limits --step-id <step-id> --output json
tsctl --connection-id <id> step set-limits --step-id <step-id> --low <value> --high <value> --output json
tsctl --connection-id <id> sequence save --id <sequence-file-id> --path <absolute-sequence-path> --release --output json
```

- For existing-file edits, reacquire live sequence and step IDs after opening a
  file. Do not reuse IDs from an earlier connection or reopen cycle.

## Step Types

| Step Type | Use | Return Mapping |
|-----------|-----|----------------|
| `Action` | Setup or cleanup code with no limit evaluation | None |
| `NumericLimitTest` | Numeric measurement with limits | `Step.Result.Numeric` |
| `PassFailTest` | Boolean evaluation | `Step.Result.PassFail` |
| `StringValueTest` | String comparison | `Step.Result.String` |

## Adapter Types

| Adapter | Key Name | Auto-Detected From |
|---------|----------|--------------------|
| Python | `Python Adapter` | `.py` file paths |
| LabVIEW | `G Flexible VI Adapter` | `.vi` or `.lvproj` file paths |
| .NET | `DotNet Adapter` | `.dll` assemblies and .NET module flags |

## Step Groups

- `setup`: initialization before the main flow
- `main`: primary test flow
- `cleanup`: always-run teardown and cleanup

## Parameter Categories — Python

| Category | Use |
|----------|-----|
| `numeric` | Numeric values |
| `string` | String values |
| `boolean` | Boolean values |

Examples:

```text
--value-expr 100 --category numeric
--value-expr '"C:/Temp"' --category string
--value-expr True --category boolean
```

## Parameter Handling — LabVIEW

LabVIEW parameters are discovered from the VI connector pane via
`LoadPrototype`. Categories (numeric, string, boolean, cluster, etc.) and
directions (in/out) are read from the VI, not specified by the user.

Use the simple `--param NAME=EXPR` syntax:

```text
--param Timeout=5000
--param FilePath='"C:/data/input.csv"'
--param EnableLogging=True
```

Use `--return-value NAME=EXPR` to explicitly map an output parameter. This is
only needed when the VI has multiple non-error output parameters — if there is
exactly one, it is auto-mapped to `Step.Result.Numeric`:

```text
--return-value Measurement=Step.Result.Numeric
```

## Parameter Handling — .NET

.NET parameters are discovered from the configured member signature via
`LoadPrototypeFromSignature`. Directions are reported as adapter flags such as
`in`, `out`, `return`, or pipe-separated combinations like `in|out` (the `ref`
case) and `out|return`. Type metadata is read from the adapter, not specified
by the user.

Object lifecycle is configured separately from the member parameters:

```text
--create-object
--class-reference FileGlobals.Instrument
--dispose-object
```

- `--create-object` prepends a constructor call before the configured member.
- `--class-reference` prepends a "Use Existing Object" call when
  `--create-object` is absent, or stores the constructed object when
  `--create-object` is present.
- `--dispose-object` disposes the constructed object after the step completes.

Use the simple `--param NAME=EXPR` syntax:

```text
--param timeout=5000
--param channel=Locals.Channel
--param station='"StationA"'
```

Use `--return-value NAME=EXPR` to explicitly map an output or return parameter:

```text
--return-value result=Step.Result.Numeric
```

## LabVIEW Call Types

| Call Type | Flag Value | Use |
|-----------|------------|-----|
| VI Call | `vi` (default) | Standard VI call |
| Class Member Call | `class-member` | LabVIEW class member VI |
| Property Node Call | `property-node` | LabVIEW property node |

## Gotchas

- TestStand string literals treat backslashes as escapes. Use `C:/path/to/dir`
  in `--value-expr` string parameters.
- Existing step names and IDs should be taken from the live file state. If the
  exact name is uncertain, use `step list` before `step resolve`.
- The module path configured on a Python step can use a normal Windows path.
- The virtual environment path configured on a Python step can use a normal
  Windows path.
- The assembly path configured on a .NET step can use a normal Windows path.
- `sequence save --path` accepts either `C:\out\file.seq` or
  `C:/out/file.seq`, but the value must be a normal absolute path, not an
  over-escaped shell literal.
- When in doubt, validate a path first with
  `tsctl doctor validate-path --kind <save|module> --path <value> --query normalized`.
- For LabVIEW `NumericLimitTest`, the output parameter is auto-mapped to
  `Step.Result.Numeric` when the VI has exactly one non-error output. If there
  are multiple, the command fails with a list of available outputs.
- The return parameter already exists on Python-backed steps. Use
  `step return-value`; do not add a second return parameter.
- For LabVIEW steps, `LoadPrototype` requires LabVIEW to be reachable. If it
  fails, run `tsctl doctor validate-labview-env` to diagnose.
- LabVIEW parameter names must match the VI connector-pane terminal names
  exactly (case-sensitive).
- For .NET steps, prototype loading requires the assembly, class name, member
  name, and member type to match a real callable member. Constructors should use
  `--member-type constructor` and omit `--member-name`.
- Instance-member `.NET` steps need either `--create-object` or
  `--class-reference`. If you omit both and the member is not static, the step
  fails at runtime with an object-reference error.
- `--class-reference` only works when the target TestStand variable already
  exists and has an object-reference-compatible type.
- For .NET `NumericLimitTest`, the measurement output is auto-mapped only when
  the member exposes exactly one eligible numeric output or return parameter. If
  there are multiple, the command fails with the available choices.

## Diagnostics

| Command | When to Use |
|---------|-------------|
| `doctor validate-path` | Uncertain path quoting |
| `doctor validate-python-env` | Before binding a standalone Python venv |
| `doctor validate-labview-env` | After a LabVIEW step creation failure |
| `doctor validate-dotnet-env` | After a .NET step creation or prototype-load failure |

## Examples

Use `examples/generate-sequence.ps1` as the canonical worked example for a
Python multi-step creation workflow.
Use `examples/generate-labview-sequence.ps1` as the canonical worked example
for a LabVIEW multi-step creation workflow.
Use `examples/generate-dotnet-sequence.ps1` as the canonical worked example for
a .NET multi-step creation workflow.
Use `examples/update-step-limits.ps1` for a focused existing-sequence
modification workflow.

## References

- Read `references/LESSONS_LEARNED.md` for path, save, and connection-id
  pitfalls.
- Read `references/teststand-api-reference/` only when the available `tsctl`
  commands are not enough to answer a specific TestStand API question.
