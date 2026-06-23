$ErrorActionPreference = "Stop"

# Documentation example for Codex. This demonstrates the preferred tsctl
# workflow for creating a disk-performance TestStand sequence.
#
# Replace these placeholders with real values when adapting the pattern:
# - <SHARED_CONNECTION_ID>: one connection-id reused across the workflow
# - <ABSOLUTE_OUTPUT_SEQ_PATH>: absolute path to the .seq output file, using a
#   normal PowerShell string like C:\Temp\disk_verification.seq
# - <ABSOLUTE_PATH_TO_DISK_TEST_MODULE.py>: Python module used by the step
#   configuration, using a normal Windows path
# - <ABSOLUTE_PATH_TO_DISK_TEST_VENV>: Python virtual environment for the
#   standalone module, using a normal Windows path
#
# Prefer a direct command or a .ps1 file like this over nested pwsh -Command
# when building tsctl workflows. Nested shell quoting is much easier to break.
# If a path looks suspicious, validate it first:
#   tsctl doctor validate-path --kind module --path C:/work/module.py --query normalized
#   tsctl doctor validate-path --kind save --path C:/work/output.seq --query normalized
# For standalone Python modules, validate the virtual environment too:
#   tsctl doctor validate-python-env --venv-path C:/work/.venv --query venvPath

$connectionId = "<SHARED_CONNECTION_ID>"
$sequencePath = "<ABSOLUTE_OUTPUT_SEQ_PATH>"
$modulePath = "<ABSOLUTE_PATH_TO_DISK_TEST_MODULE.py>"
$venvPath = "<ABSOLUTE_PATH_TO_DISK_TEST_VENV>"
$testDir = "C:/absolute/path/to/test/output"  # Forward slashes because this becomes a TestStand string expression

function Invoke-TsctlJson {
    param([string[]] $Arguments)

    $output = & tsctl --connection-id $connectionId @Arguments --output json
    return $output | ConvertFrom-Json
}

$null = Invoke-TsctlJson @("engine", "load-palettes")
$null = Invoke-TsctlJson @("doctor", "validate-python-env", "--venv-path", $venvPath)

$sequenceFileId = & tsctl --connection-id $connectionId sequence create --output id
$sequenceId = & tsctl --connection-id $connectionId sequence get --file-id $sequenceFileId --query sequenceId

$null = Invoke-TsctlJson @(
    "step", "add-python-action",
    "--sequence-id", $sequenceId,
    "--group", "setup",
    "--name", "Initialize Test Environment",
    "--module-path", $modulePath,
    "--function-name", "setup",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir"
)

$null = Invoke-TsctlJson @(
    "step", "add-python-numeric-test",
    "--sequence-id", $sequenceId,
    "--group", "main",
    "--name", "Sequential Write Test",
    "--module-path", $modulePath,
    "--function-name", "sequential_write",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir",
    "--param-number", "file_size_mb=100",
    "--param-number", "block_size_kb=64",
    "--low", "50",
    "--high", "10000"
)

$null = Invoke-TsctlJson @(
    "step", "add-python-numeric-test",
    "--sequence-id", $sequenceId,
    "--group", "main",
    "--name", "Sequential Read Test",
    "--module-path", $modulePath,
    "--function-name", "sequential_read",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir",
    "--param-number", "file_size_mb=100",
    "--param-number", "block_size_kb=64",
    "--low", "50",
    "--high", "10000"
)

$null = Invoke-TsctlJson @(
    "step", "add-python-numeric-test",
    "--sequence-id", $sequenceId,
    "--group", "main",
    "--name", "Random I/O Test",
    "--module-path", $modulePath,
    "--function-name", "random_io_test",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir",
    "--param-number", "file_size_mb=50",
    "--param-number", "num_operations=100",
    "--param-number", "block_size_kb=4",
    "--low", "10",
    "--high", "10000"
)

$null = Invoke-TsctlJson @(
    "step", "add-python-numeric-test",
    "--sequence-id", $sequenceId,
    "--group", "main",
    "--name", "IOPS Measurement",
    "--module-path", $modulePath,
    "--function-name", "measure_iops",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir",
    "--param-number", "file_size_mb=50",
    "--param-number", "duration_seconds=5",
    "--param-number", "block_size_kb=4",
    "--low", "100",
    "--high", "1000000"
)

$null = Invoke-TsctlJson @(
    "step", "add-python-numeric-test",
    "--sequence-id", $sequenceId,
    "--group", "main",
    "--name", "Latency Measurement",
    "--module-path", $modulePath,
    "--function-name", "measure_latency",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir",
    "--param-number", "file_size_mb=50",
    "--param-number", "num_samples=100",
    "--param-number", "block_size_kb=4",
    "--low", "0",
    "--high", "100"
)

$null = Invoke-TsctlJson @(
    "step", "add-python-action",
    "--sequence-id", $sequenceId,
    "--group", "cleanup",
    "--name", "Cleanup Test Files",
    "--module-path", $modulePath,
    "--function-name", "cleanup",
    "--venv-path", $venvPath,
    "--param-string", "test_dir=$testDir"
)

$null = Invoke-TsctlJson @(
    "sequence", "save",
    "--id", $sequenceFileId,
    "--path", $sequencePath,
    "--format", "binary"
)

$null = Invoke-TsctlJson @("sequence", "release", "--id", $sequenceFileId)
