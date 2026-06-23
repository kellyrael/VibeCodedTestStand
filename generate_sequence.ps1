$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$projectDir  = "C:\Users\localadmin\Documents\Demos\FgenScopeTestStandSystemLink"
$tsctl       = Join-Path $projectDir ".agents\skills\creating-teststand-sequences\tools\tsctl.exe"
$serviceDir  = Join-Path $projectDir ".agents\skills\creating-teststand-sequences\tools\teststandservice"
$serviceExe  = Join-Path $serviceDir "ni.teststand.service.exe"
$modulePath  = Join-Path $projectDir "teststand_steps.py"
$venvPath    = Join-Path $projectDir ".venv"
$outputPath  = Join-Path $projectDir "scope_fgen_validation.seq"
$cid         = "scope-fgen-seq"

# ---------------------------------------------------------------------------
# Ensure TestStand service is running and ready
# ---------------------------------------------------------------------------
Write-Host "Checking TestStand service..."
$ready = $false
try {
    Invoke-RestMethod -Uri "http://localhost:42001/api/ts-service/livez" -TimeoutSec 2 | Out-Null
    $ready = $true
} catch {}

if (-not $ready) {
    $running = Get-Process -Name "ni.teststand.service" -ErrorAction SilentlyContinue
    if (-not $running) {
        Write-Host "Starting TestStand service..."
        Start-Process -FilePath $serviceExe -WorkingDirectory $serviceDir -WindowStyle Hidden
    }
}

$maxRetries = 20
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        Invoke-RestMethod -Uri "http://localhost:42001/api/ts-service/livez" -TimeoutSec 2 | Out-Null
        Write-Host "TestStand service is ready."
        break
    } catch {
        Start-Sleep -Seconds 1
    }
    if ($i -eq $maxRetries - 1) { Write-Error "TestStand service did not become ready in time." }
}

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
function Invoke-Tsctl {
    param([string[]] $Arguments)
    $output = & $tsctl --connection-id $cid @Arguments --output json
    if ($LASTEXITCODE -ne 0) { throw "tsctl failed: $output" }
    return $output | ConvertFrom-Json
}

# ---------------------------------------------------------------------------
# Create sequence
# ---------------------------------------------------------------------------
Write-Host "Creating sequence..."
$seq = Invoke-Tsctl @("sequence", "create")
$seqFileId = $seq.sequenceFileId
$seqId     = $seq.sequenceId

Write-Host "  sequenceFileId = $seqFileId"
Write-Host "  sequenceId     = $seqId"

# ---------------------------------------------------------------------------
# Setup step — Initialize Devices
# ---------------------------------------------------------------------------
Write-Host "Adding Setup: Initialize Devices..."
$null = Invoke-Tsctl @(
    "step", "add-python-action",
    "--sequence-id", $seqId,
    "--group",         "setup",
    "--name",          "Initialize Devices",
    "--module-path",   $modulePath,
    "--function-name", "initialize_devices",
    "--venv-path",     $venvPath,
    "--param-string",  "scope_resource=Scope1",
    "--param-string",  "fgen_resource=FGEN1"
)

# ---------------------------------------------------------------------------
# Helper: add one test case (measure_rms + measure_frequency)
# ---------------------------------------------------------------------------
function Add-TestCase {
    param(
        [string] $label,
        [string] $waveform,
        [double] $freqHz,
        [double] $ampVpp,
        [double] $dcOffsetV,
        [double] $rmsLow,
        [double] $rmsHigh
    )

    $freqLow  = [math]::Round($freqHz * 0.98, 6)
    $freqHigh = [math]::Round($freqHz * 1.02, 6)
    $rmsLowR  = [math]::Round($rmsLow,  6)
    $rmsHighR = [math]::Round($rmsHigh, 6)

    Write-Host "  Adding: $label (RMS + Freq)"

    $null = Invoke-Tsctl @(
        "step", "add-python-numeric-test",
        "--sequence-id", $seqId,
        "--group",         "main",
        "--name",          "RMS - $label",
        "--module-path",   $modulePath,
        "--function-name", "measure_rms",
        "--venv-path",     $venvPath,
        "--param-string",  "waveform=$waveform",
        "--param-number",  "frequency_hz=$freqHz",
        "--param-number",  "amplitude_vpp=$ampVpp",
        "--param-number",  "dc_offset_v=$dcOffsetV",
        "--low",  "$rmsLowR",
        "--high", "$rmsHighR"
    )

    $null = Invoke-Tsctl @(
        "step", "add-python-numeric-test",
        "--sequence-id", $seqId,
        "--group",         "main",
        "--name",          "Freq - $label",
        "--module-path",   $modulePath,
        "--function-name", "measure_frequency",
        "--venv-path",     $venvPath,
        "--param-string",  "waveform=$waveform",
        "--param-number",  "frequency_hz=$freqHz",
        "--param-number",  "amplitude_vpp=$ampVpp",
        "--param-number",  "dc_offset_v=$dcOffsetV",
        "--low",  "$freqLow",
        "--high", "$freqHigh"
    )
}

# RMS expected values (12 % tolerance)
# SINE: peak/sqrt(2)  SQUARE: peak  TRIANGLE/RAMP: peak/sqrt(3)
# peak = amplitude_vpp / 2   total_rms = sqrt(ac_rms^2 + dc_offset^2)

Write-Host "Adding Main steps..."

# Sine frequency sweep (2 Vpk-pk)
Add-TestCase "SINE 100 Hz 2.0 Vpk-pk"     SINE  100.0      2.0  0.0  0.622254  0.791281
Add-TestCase "SINE 1 kHz 2.0 Vpk-pk"      SINE  1000.0     2.0  0.0  0.622254  0.791281
Add-TestCase "SINE 10 kHz 2.0 Vpk-pk"     SINE  10000.0    2.0  0.0  0.622254  0.791281
Add-TestCase "SINE 100 kHz 2.0 Vpk-pk"    SINE  100000.0   2.0  0.0  0.622254  0.791281
Add-TestCase "SINE 1 MHz 2.0 Vpk-pk"      SINE  1000000.0  2.0  0.0  0.622254  0.791281

# Sine amplitude sweep (1 kHz)
Add-TestCase "SINE 1 kHz 0.5 Vpk-pk"      SINE  1000.0     0.5  0.0  0.155563  0.197699
Add-TestCase "SINE 1 kHz 1.0 Vpk-pk"      SINE  1000.0     1.0  0.0  0.311127  0.395285
Add-TestCase "SINE 1 kHz 4.0 Vpk-pk"      SINE  1000.0     4.0  0.0  1.244508  1.583139

# Waveform types (1 kHz, 2 Vpk-pk)
Add-TestCase "SQUARE 1 kHz 2.0 Vpk-pk"    SQUARE    1000.0  2.0  0.0  0.880000  1.120000
Add-TestCase "TRIANGLE 1 kHz 2.0 Vpk-pk"  TRIANGLE  1000.0  2.0  0.0  0.508068  0.646327
Add-TestCase "RAMP_UP 1 kHz 2.0 Vpk-pk"   RAMP_UP   1000.0  2.0  0.0  0.508068  0.646327

# DC offset (within PXIe-5433 hardware limit of +/-500 mV)
Add-TestCase "SINE 1 kHz 2.0 Vpk-pk +0.4V offset"  SINE  1000.0  2.0  0.4  0.714909  0.909063

# ---------------------------------------------------------------------------
# Cleanup step — Disconnect Devices
# ---------------------------------------------------------------------------
Write-Host "Adding Cleanup: Disconnect Devices..."
$null = Invoke-Tsctl @(
    "step", "add-python-action",
    "--sequence-id", $seqId,
    "--group",         "cleanup",
    "--name",          "Disconnect Devices",
    "--module-path",   $modulePath,
    "--function-name", "disconnect_devices",
    "--venv-path",     $venvPath
)

# ---------------------------------------------------------------------------
# Save and release
# ---------------------------------------------------------------------------
Write-Host "Saving sequence to: $outputPath"
$null = Invoke-Tsctl @(
    "sequence", "save",
    "--id",   $seqFileId,
    "--path", $outputPath,
    "--release"
)

Write-Host ""
Write-Host "Done. Sequence saved: $outputPath"
Write-Host "  Setup   : 1 step  (Initialize Devices)"
Write-Host "  Main    : 24 steps (12 cases x RMS + Frequency)"
Write-Host "  Cleanup : 1 step  (Disconnect Devices)"

