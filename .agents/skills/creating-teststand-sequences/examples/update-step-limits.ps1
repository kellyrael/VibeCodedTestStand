$ErrorActionPreference = "Stop"

# Documentation example for Codex. This demonstrates the preferred tsctl
# workflow for updating numeric limits on an existing TestStand step.
#
# Replace these placeholders when adapting the pattern:
# - <SHARED_CONNECTION_ID>: one connection-id reused across the workflow
# - <ABSOLUTE_SEQUENCE_PATH>: existing .seq file path, e.g. C:\Temp\demo.seq
# - <STEP_NAME>: step to update inside MainSequence

$connectionId = "<SHARED_CONNECTION_ID>"
$sequencePath = "<ABSOLUTE_SEQUENCE_PATH>"
$stepName = "<STEP_NAME>"
$lowLimit = "4.85"
$highLimit = "5.15"

function Invoke-TsctlJson {
    param([string[]] $Arguments)

    $output = & tsctl --connection-id $connectionId @Arguments --output json
    return $output | ConvertFrom-Json
}

# Optional preflight if the path may have come from a shell-generated string.
$normalizedSequencePath = & tsctl doctor validate-path --kind save --path $sequencePath --query normalized

# Open the existing sequence file and fetch MainSequence.
$sequenceFileId = & tsctl --connection-id $connectionId sequence open --path $normalizedSequencePath --output id
$sequenceId = & tsctl --connection-id $connectionId sequence get --file-id $sequenceFileId --query sequenceId

# If the exact step name is uncertain, list the group first.
$null = Invoke-TsctlJson @(
    "step", "list",
    "--sequence-id", $sequenceId,
    "--group", "main"
)

# Resolve the target step by name to get the live step instance ID for this connection.
$stepId = & tsctl --connection-id $connectionId step resolve --sequence-id $sequenceId --group main --name $stepName --query stepId

# Optional readback before the edit.
$null = Invoke-TsctlJson @("step", "get-limits", "--step-id", $stepId)

# Update the limits on the existing step.
$null = Invoke-TsctlJson @(
    "step", "set-limits",
    "--step-id", $stepId,
    "--low", $lowLimit,
    "--high", $highLimit
)

# Save the same file path, then release the file from memory.
$null = Invoke-TsctlJson @(
    "sequence", "save",
    "--id", $sequenceFileId,
    "--path", $normalizedSequencePath,
    "--format", "binary"
)

$null = Invoke-TsctlJson @("sequence", "release", "--id", $sequenceFileId)
