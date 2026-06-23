# NI Dependency Management - PowerShell Script Reference

Complete reference for creating and using PowerShell scripts to manage NI assembly dependencies in C# projects.

## Overview

This document provides production-ready PowerShell scripts for automating NI assembly reference management. These scripts solve the "assembly not found" problem by automatically discovering NI installations and updating .csproj files.

---

## Core Scripts

### 1. Quick-Check.ps1

**Purpose:** Fast verification that required NI assemblies are installed.

**Complete Implementation:**

```powershell
# Quick-Check.ps1
# Fast check for essential NI assemblies

param(
    [string[]]$Assemblies = @(
        "NationalInstruments.RFmx.WlanMX.Fx40",
        "NationalInstruments.ModularInstruments.NIRfsg.Fx40",
        "NationalInstruments.ModularInstruments.NIRfsa.Fx40",
        "NationalInstruments.RFmx.SpecAnMX.Fx40"
    )
)

Write-Host "=== NI Assembly Quick Check ===" -ForegroundColor Cyan
Write-Host ""

$SearchPaths = @(
    "C:\Program Files\National Instruments\MeasurementStudioVS\DotNET\Assemblies\",
    "C:\Program Files (x86)\National Instruments\MeasurementStudioVS\DotNET\Assemblies\",
    "C:\Program Files\National Instruments\Shared\",
    "C:\Program Files (x86)\National Instruments\Shared\"
)

$allFound = $true

foreach ($asm in $Assemblies) {
    $found = $false
    $foundPath = $null

    foreach ($basePath in $SearchPaths) {
        if (Test-Path $basePath) {
            $result = Get-ChildItem -Path $basePath -Filter "$asm.dll" -Recurse -ErrorAction SilentlyContinue |
                      Sort-Object LastWriteTime -Descending |
                      Select-Object -First 1

            if ($result) {
                $foundPath = $result.FullName
                $found = $true
                break
            }
        }
    }

    if ($found) {
        Write-Host "✓ $asm" -ForegroundColor Green
        Write-Host "  $foundPath" -ForegroundColor Gray
    } else {
        Write-Host "✗ $asm" -ForegroundColor Red
        $allFound = $false
    }
}

Write-Host ""
if ($allFound) {
    Write-Host "All required assemblies found! ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Missing assemblies detected." -ForegroundColor Yellow
    Write-Host "Install via NI Package Manager: https://www.ni.com/ni-package-manager" -ForegroundColor Yellow
    exit 1
}
```

**Usage:**
```powershell
# Default check (common assemblies)
.\Quick-Check.ps1

# Custom assembly list
.\Quick-Check.ps1 -Assemblies "NationalInstruments.ModularInstruments.NIDCPower.Fx40","NationalInstruments.ModularInstruments.NIDmm.Fx40"
```

---

### 2. Find-NIAssemblies.ps1

**Purpose:** Comprehensive discovery and reporting of all NI assemblies on the system.

**Complete Implementation:**

```powershell
# Find-NIAssemblies.ps1
# Discover all NI assemblies and report details

param(
    [switch]$Verbose
)

Write-Host "=== NI Assembly Discovery ===" -ForegroundColor Cyan
Write-Host ""

$SearchPaths = @(
    "C:\Program Files\National Instruments\",
    "C:\Program Files (x86)\National Instruments\",
    "C:\Windows\Microsoft.NET\assembly\GAC_MSIL\",
    "C:\Windows\assembly\GAC_MSIL\"
)

$assemblies = @()

foreach ($basePath in $SearchPaths) {
    if (Test-Path $basePath) {
        if ($Verbose) {
            Write-Host "Scanning: $basePath" -ForegroundColor Gray
        }

        $found = Get-ChildItem -Path $basePath -Filter "NationalInstruments.*.dll" -Recurse -ErrorAction SilentlyContinue |
                 Where-Object { $_.Name -match "^NationalInstruments\." }

        foreach ($dll in $found) {
            try {
                $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($dll.FullName).FileVersion

                $assemblies += [PSCustomObject]@{
                    Name = $dll.BaseName
                    Version = $version
                    Path = $dll.FullName
                    LastModified = $dll.LastWriteTime
                    Size = [math]::Round($dll.Length / 1MB, 2)
                }
            }
            catch {
                # Skip if can't read version
            }
        }
    }
}

# Remove duplicates (keep newest)
$uniqueAssemblies = $assemblies | 
    Group-Object -Property Name | 
    ForEach-Object {
        $_.Group | Sort-Object LastModified -Descending | Select-Object -First 1
    } |
    Sort-Object Name

Write-Host "Found $($uniqueAssemblies.Count) unique NI assemblies:" -ForegroundColor Green
Write-Host ""

$uniqueAssemblies | Format-Table -Property Name, Version, @{Label="Size(MB)";Expression={$_.Size}}, LastModified -AutoSize

if ($Verbose) {
    Write-Host "`nDetailed Paths:" -ForegroundColor Cyan
    $uniqueAssemblies | ForEach-Object {
        Write-Host "$($_.Name)" -ForegroundColor Yellow
        Write-Host "  $($_.Path)" -ForegroundColor Gray
        Write-Host ""
    }
}
```

**Usage:**
```powershell
# Basic discovery
.\Find-NIAssemblies.ps1

# Verbose output with paths
.\Find-NIAssemblies.ps1 -Verbose

# Filter results
.\Find-NIAssemblies.ps1 | Where-Object { $_.Name -like "*RFmx*" }

# Export to CSV
.\Find-NIAssemblies.ps1 | Export-Csv -Path ni-assemblies.csv -NoTypeInformation
```

---

### 3. Update-ProjectReferences.ps1

**Purpose:** Update a single .csproj file with correct NI assembly HintPaths.

**Complete Implementation:**

```powershell
# Update-ProjectReferences.ps1
# Update .csproj file with correct NI assembly references

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [bool]$Backup = $true,

    [switch]$WhatIf
)

if (-not (Test-Path $ProjectPath)) {
    Write-Error "Project file not found: $ProjectPath"
    exit 1
}

Write-Host "=== Update Project References ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectPath" -ForegroundColor White
Write-Host ""

# Backup
if ($Backup -and -not $WhatIf) {
    $backupPath = "$ProjectPath.backup"
    Copy-Item $ProjectPath $backupPath -Force
    Write-Host "Backup created: $backupPath" -ForegroundColor Gray
}

# Discover NI assemblies
$SearchPaths = @(
    "C:\Program Files\National Instruments\MeasurementStudioVS\DotNET\Assemblies\",
    "C:\Program Files (x86)\National Instruments\MeasurementStudioVS\DotNET\Assemblies\",
    "C:\Program Files\National Instruments\Shared\",
    "C:\Program Files (x86)\National Instruments\Shared\"
)

$assemblyCache = @{}
foreach ($basePath in $SearchPaths) {
    if (Test-Path $basePath) {
        Get-ChildItem -Path $basePath -Filter "NationalInstruments.*.dll" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "^NationalInstruments\." } |
            ForEach-Object {
                $name = $_.BaseName
                if (-not $assemblyCache.ContainsKey($name) -or $_.LastWriteTime -gt $assemblyCache[$name].LastWriteTime) {
                    $assemblyCache[$name] = $_
                }
            }
    }
}

Write-Host "Found $($assemblyCache.Count) NI assemblies in cache" -ForegroundColor Green

# Load and update project file
[xml]$proj = Get-Content $ProjectPath
$ns = New-Object System.Xml.XmlNamespaceManager($proj.NameTable)
$ns.AddNamespace("ms", "http://schemas.microsoft.com/developer/msbuild/2003")

$references = $proj.SelectNodes("//ms:Reference[@Include]", $ns)
$updatedCount = 0

foreach ($ref in $references) {
    $includeName = $ref.GetAttribute("Include")

    # Extract assembly name (before comma if versioned)
    $assemblyName = $includeName -split ',' | Select-Object -First 1
    $assemblyName = $assemblyName.Trim()

    # Check if it's an NI assembly
    if ($assemblyName -match "^NationalInstruments\.") {
        if ($assemblyCache.ContainsKey($assemblyName)) {
            $newPath = $assemblyCache[$assemblyName].FullName

            # Update or create HintPath
            $hintPath = $ref.SelectSingleNode("ms:HintPath", $ns)
            if ($hintPath) {
                $oldPath = $hintPath.InnerText
                if ($oldPath -ne $newPath) {
                    Write-Host "Updating $assemblyName" -ForegroundColor Yellow
                    Write-Host "  Old: $oldPath" -ForegroundColor Gray
                    Write-Host "  New: $newPath" -ForegroundColor Green

                    if (-not $WhatIf) {
                        $hintPath.InnerText = $newPath
                    }
                    $updatedCount++
                }
            } else {
                Write-Host "Adding HintPath for $assemblyName" -ForegroundColor Yellow
                Write-Host "  Path: $newPath" -ForegroundColor Green

                if (-not $WhatIf) {
                    $hintPathNode = $proj.CreateElement("HintPath", $proj.DocumentElement.NamespaceURI)
                    $hintPathNode.InnerText = $newPath
                    [void]$ref.AppendChild($hintPathNode)
                }
                $updatedCount++
            }

            # Add Private=False if not present
            $private = $ref.SelectSingleNode("ms:Private", $ns)
            if (-not $private -and -not $WhatIf) {
                $privateNode = $proj.CreateElement("Private", $proj.DocumentElement.NamespaceURI)
                $privateNode.InnerText = "False"
                [void]$ref.AppendChild($privateNode)
            }
        }
        else {
            Write-Host "⚠ $assemblyName not found on system" -ForegroundColor Red
        }
    }
}

# Save changes
if ($updatedCount -gt 0) {
    if ($WhatIf) {
        Write-Host "`n[WhatIf] Would update $updatedCount references" -ForegroundColor Cyan
    } else {
        $proj.Save($ProjectPath)
        Write-Host "`n✓ Updated $updatedCount references" -ForegroundColor Green
    }
} else {
    Write-Host "`n✓ No updates needed" -ForegroundColor Green
}
```

**Usage:**
```powershell
# Update specific project
.\Update-ProjectReferences.ps1 -ProjectPath "..\src\MyProject\MyProject.csproj"

# Dry run (show changes without applying)
.\Update-ProjectReferences.ps1 -ProjectPath "..\src\MyProject\MyProject.csproj" -WhatIf

# No backup
.\Update-ProjectReferences.ps1 -ProjectPath "..\src\MyProject\MyProject.csproj" -Backup $false
```

---

### 4. Update-ProjectsSmart.ps1

**Purpose:** Intelligently update all projects with version validation and build testing.

**Complete Implementation:**

```powershell
# Update-ProjectsSmart.ps1
# Smart update with version control and build validation

param(
    [switch]$PreferStable = $true,
    [switch]$WhatIf,
    [switch]$Confirm = $true
)

Write-Host "=== Smart Project Update ===" -ForegroundColor Cyan
Write-Host ""

# Find all .csproj files
$projects = Get-ChildItem -Path "..\src" -Filter "*.csproj" -Recurse -ErrorAction SilentlyContinue

if ($projects.Count -eq 0) {
    Write-Error "No .csproj files found in ..\src"
    exit 1
}

Write-Host "Found $($projects.Count) project(s):" -ForegroundColor Green
$projects | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor White }
Write-Host ""

# Known stable version (default)
$stableVersion = "23.8"

if ($PreferStable) {
    Write-Host "Using stable version: $stableVersion" -ForegroundColor Green
} else {
    Write-Host "Using latest available versions" -ForegroundColor Yellow
}

# Discover assemblies with version filtering
$SearchPaths = @(
    "C:\Program Files\National Instruments\MeasurementStudioVS\DotNET\Assemblies\",
    "C:\Program Files (x86)\National Instruments\MeasurementStudioVS\DotNET\Assemblies\"
)

$assemblyCache = @{}
foreach ($basePath in $SearchPaths) {
    if (Test-Path $basePath) {
        Get-ChildItem -Path $basePath -Filter "NationalInstruments.*.dll" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "^NationalInstruments\." } |
            ForEach-Object {
                $name = $_.BaseName
                $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($_.FullName).FileVersion

                # If prefer stable, filter by version
                if ($PreferStable) {
                    if ($version -like "$stableVersion.*") {
                        if (-not $assemblyCache.ContainsKey($name) -or $_.LastWriteTime -gt $assemblyCache[$name].LastWriteTime) {
                            $assemblyCache[$name] = $_
                        }
                    }
                } else {
                    # Use latest
                    if (-not $assemblyCache.ContainsKey($name) -or $_.LastWriteTime -gt $assemblyCache[$name].LastWriteTime) {
                        $assemblyCache[$name] = $_
                    }
                }
            }
    }
}

Write-Host "Assembly cache: $($assemblyCache.Count) assemblies" -ForegroundColor Green
Write-Host ""

# Update each project
foreach ($proj in $projects) {
    Write-Host "Processing: $($proj.Name)" -ForegroundColor Cyan

    # Create backup
    $backupPath = "$($proj.FullName).backup"
    if (-not $WhatIf) {
        Copy-Item $proj.FullName $backupPath -Force
    }

    # Update references using Update-ProjectReferences logic
    & ".\Update-ProjectReferences.ps1" -ProjectPath $proj.FullName -Backup $false -WhatIf:$WhatIf

    Write-Host ""
}

# Build validation
if (-not $WhatIf) {
    Write-Host "=== Build Validation ===" -ForegroundColor Cyan
    Write-Host "Testing build..." -ForegroundColor White

    Push-Location ..
    $buildResult = dotnet build --nologo --verbosity quiet 2>&1
    $buildSuccess = $LASTEXITCODE -eq 0
    Pop-Location

    if ($buildSuccess) {
        Write-Host "✓ Build succeeded!" -ForegroundColor Green
    } else {
        Write-Host "✗ Build failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Build output:" -ForegroundColor Yellow
        $buildResult | Write-Host

        Write-Host ""
        Write-Host "Rolling back changes..." -ForegroundColor Yellow

        # Restore backups
        foreach ($proj in $projects) {
            $backupPath = "$($proj.FullName).backup"
            if (Test-Path $backupPath) {
                Copy-Item $backupPath $proj.FullName -Force
                Write-Host "  Restored: $($proj.Name)" -ForegroundColor Gray
            }
        }

        exit 1
    }
}

Write-Host ""
Write-Host "✓ Update complete!" -ForegroundColor Green
```

**Usage:**
```powershell
# Default: Use stable v23.8
.\Update-ProjectsSmart.ps1

# Use latest versions
.\Update-ProjectsSmart.ps1 -PreferStable:$false

# Dry run
.\Update-ProjectsSmart.ps1 -WhatIf

# Skip confirmation
.\Update-ProjectsSmart.ps1 -Confirm:$false
```

---

## Helper Functions

### Get-NIAssemblyVersion

```powershell
function Get-NIAssemblyVersion {
    param([string]$AssemblyPath)

    try {
        $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($AssemblyPath)
        return $version.FileVersion
    }
    catch {
        return "Unknown"
    }
}
```

### Test-NIAssemblyCompatibility

```powershell
function Test-NIAssemblyCompatibility {
    param(
        [string]$Assembly1Path,
        [string]$Assembly2Path
    )

    $v1 = Get-NIAssemblyVersion $Assembly1Path
    $v2 = Get-NIAssemblyVersion $Assembly2Path

    $v1Major = ($v1 -split '\.')[0..1] -join '.'
    $v2Major = ($v2 -split '\.')[0..1] -join '.'

    return $v1Major -eq $v2Major
}
```

---

## Integration Examples

### Visual Studio Pre-Build Event

Add to .csproj:

```xml
<Target Name="PreBuild" BeforeTargets="PreBuildEvent">
  <Exec Command="powershell -ExecutionPolicy Bypass -File &quot;$(SolutionDir)build-tools\Quick-Check.ps1&quot;" />
</Target>
```

### Git Pre-Commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
cd build-tools
powershell -ExecutionPolicy Bypass -File Quick-Check.ps1
if [ $? -ne 0 ]; then
    echo "NI assemblies check failed. Commit aborted."
    exit 1
fi
```

### Azure DevOps Pipeline

```yaml
- task: PowerShell@2
  displayName: 'Verify NI Dependencies'
  inputs:
    targetType: 'filePath'
    filePath: 'build-tools/Quick-Check.ps1'
    failOnStderr: true

- task: PowerShell@2
  displayName: 'Update Project References'
  inputs:
    targetType: 'filePath'
    filePath: 'build-tools/Update-ProjectsSmart.ps1'
    arguments: '-Confirm:$false'
```

---

## See Also

- [NI Dependency Management Skill](./SKILL.md) - Overview and usage guide
- [NI Hardware Drivers C# Skill](../ni-hw-drivers-csharp/SKILL.md) - C# API patterns
- NI Package Manager: https://www.ni.com/ni-package-manager
$gacSection
