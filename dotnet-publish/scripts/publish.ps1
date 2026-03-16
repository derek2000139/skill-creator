#Requires -Version 5.1
<#
.SYNOPSIS
    .NET Desktop Application Auto Publish Script
.DESCRIPTION
    Reads publish-config.json configuration, automatically completes version update, build, publish, and packaging
.PARAMETER VersionBump
    Version upgrade method: patch | minor | major | custom version number
.PARAMETER SkipZip
    Skip ZIP packaging
.PARAMETER SkipChangelog
    Skip changelog update
.EXAMPLE
    .\scripts\publish.ps1
    .\scripts\publish.ps1 -VersionBump minor
    .\scripts\publish.ps1 -VersionBump "2.1.0"
#>

param(
    [Parameter(Position = 0)]
    [string]$VersionBump = "patch",
    
    [switch]$SkipZip,
    [switch]$SkipChangelog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================
# Utility Functions
# ============================================================

function Write-Header($text) {
    $line = "=" * 56
    Write-Host "`n$line" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "$line" -ForegroundColor Cyan
}

function Write-Step($step, $text) {
    Write-Host "`n[$step] $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  [OK] $text" -ForegroundColor Green
}

function Write-Fail($text) {
    Write-Host "  [FAIL] $text" -ForegroundColor Red
}

function Get-BumpedVersion([string]$current, [string]$bump) {
    # Try to parse as custom version number
    if ($bump -match '^\d+\.\d+\.\d+$') {
        return $bump
    }
    
    $parts = $current.Split('.')
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2]
    
    switch ($bump.ToLower()) {
        "major" { $major++; $minor = 0; $patch = 0 }
        "minor" { $minor++; $patch = 0 }
        "patch" { $patch++ }
        default { 
            Write-Fail "Unknown version bump type: $bump"
            exit 1
        }
    }
    
    return "$major.$minor.$patch"
}

function Get-FileSizeMB($path) {
    if (Test-Path $path) {
        $size = (Get-Item $path).Length / 1MB
        return "{0:N1} MB" -f $size
    }
    return "N/A"
}

# ============================================================
# Main Flow
# ============================================================

$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    Write-Header ".NET Desktop Application Publish Tool"
    
    # ----------------------------------------------------------
    # Step 1: Environment Check
    # ----------------------------------------------------------
    Write-Step 1 "Environment Check"
    
    $dotnetVersion = & dotnet --version 2>$null
    if (-not $dotnetVersion) {
        Write-Fail ".NET SDK not detected, please install: https://dotnet.microsoft.com/download"
        exit 1
    }
    Write-Success ".NET SDK: $dotnetVersion"
    
    # ----------------------------------------------------------
    # Step 2: Read Configuration
    # ----------------------------------------------------------
    Write-Step 2 "Read Publish Configuration"
    
    $configPath = Join-Path $projectRoot "publish-config.json"
    if (-not (Test-Path $configPath)) {
        Write-Fail "publish-config.json not found, please create configuration file first"
        exit 1
    }
    
    $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $appName = $config.appName
    $currentVersion = $config.currentVersion
    $projectPath = Join-Path $projectRoot $config.projectPath
    $outputBaseDir = Join-Path $projectRoot $config.outputBaseDir
    
    Write-Success "App: $appName  Current Version: v$currentVersion"
    
    # ----------------------------------------------------------
    # Step 3: Calculate New Version
    # ----------------------------------------------------------
    Write-Step 3 "Version Upgrade"
    
    $newVersion = Get-BumpedVersion $currentVersion $VersionBump
    Write-Success "v$currentVersion -> v$newVersion ($VersionBump)"
    
    # ----------------------------------------------------------
    # Step 4: Update Version Number
    # ----------------------------------------------------------
    Write-Step 4 "Update Version Number"
    
    # Update publish-config.json
    $config.currentVersion = $newVersion
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    Write-Success "publish-config.json updated"
    
    # Update .csproj
    if (Test-Path $projectPath) {
        $csprojContent = Get-Content $projectPath -Raw -Encoding UTF8
        
        # Replace or insert version number
        $versionProps = @{
            'Version'         = $newVersion
            'FileVersion'     = "$newVersion.0"
            'AssemblyVersion' = "$newVersion.0"
        }
        
        foreach ($prop in $versionProps.GetEnumerator()) {
            $pattern = "(<$($prop.Key)>)(.*?)(</$($prop.Key)>)"
            if ($csprojContent -match $pattern) {
                $csprojContent = $csprojContent -replace $pattern, "`${1}$($prop.Value)`${3}"
            }
        }
        
        Set-Content $projectPath $csprojContent -Encoding UTF8
        Write-Success "$($config.projectPath) updated"
    }
    
    # ----------------------------------------------------------
    # Step 5: Update Changelog
    # ----------------------------------------------------------
    if (-not $SkipChangelog) {
        Write-Step 5 "Update Changelog"
        
        $changelogPath = Join-Path $projectRoot "CHANGELOG.md"
        $date = Get-Date -Format "yyyy-MM-dd"
        $entry = @"

## [$newVersion] - $date

### Changed
- Regular updates and optimizations

"@
        
        if (Test-Path $changelogPath) {
            $content = Get-Content $changelogPath -Raw -Encoding UTF8
            # Insert after first title line
            $content = $content -replace "(# .+\r?\n)", "`$1$entry"
            Set-Content $changelogPath $content -Encoding UTF8
        }
        else {
            $content = "# Changelog`n$entry"
            Set-Content $changelogPath $content -Encoding UTF8
        }
        
        Write-Success "CHANGELOG.md updated"
    }
    
    # ----------------------------------------------------------
    # Step 6: Build and Publish
    # ----------------------------------------------------------
    Write-Step 6 "Build and Publish"
    
    # Ensure output directory exists
    if (-not (Test-Path $outputBaseDir)) {
        New-Item -ItemType Directory -Path $outputBaseDir -Force | Out-Null
    }
    
    $results = @()
    
    foreach ($profile in $config.publishProfiles) {
        $rid = $profile.rid
        $profileName = $profile.name
        $outDir = Join-Path $outputBaseDir "$appName-v$newVersion-$rid"
        $zipPath = Join-Path $outputBaseDir "$appName-v$newVersion-$rid.zip"
        
        Write-Host "`n  Building $profileName ..." -ForegroundColor White
        
        # Clean old output
        if (Test-Path $outDir) { Remove-Item $outDir -Recurse -Force }
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        
        # Assemble dotnet publish arguments
        $publishArgs = @(
            "publish"
            "`"$projectPath`""
            "-c", "Release"
            "-r", $rid
            "-f", $profile.framework
            "--self-contained", $profile.selfContained.ToString().ToLower()
            "-p:PublishSingleFile=$($profile.singleFile.ToString().ToLower())"
            "-p:IncludeNativeLibrariesForSelfExtract=true"
            "-p:EnableCompressionInSingleFile=true"
            "-p:DebugType=none"
            "-p:DebugSymbols=false"
            "-o", "`"$outDir`""
        )
        
        if ($profile.trimmed -eq $true) {
            $publishArgs += "-p:PublishTrimmed=true"
            $publishArgs += "-p:TrimMode=partial"
        }
        
        if ($profile.readyToRun -eq $true) {
            $publishArgs += "-p:PublishReadyToRun=true"
        }
        
        # Execute publish
        $process = Start-Process -FilePath "dotnet" -ArgumentList $publishArgs `
            -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput "$outDir.build.log" `
            -RedirectStandardError "$outDir.error.log"
        
        $result = @{
            Name    = $profileName
            Rid     = $rid
            OutDir  = $outDir
            ZipPath = $zipPath
            Success = ($process.ExitCode -eq 0)
        }
        
        if ($result.Success) {
            # Find exe file size
            $exeFile = Get-ChildItem $outDir -Filter "*.exe" | Select-Object -First 1
            $exeSize = if ($exeFile) { Get-FileSizeMB $exeFile.FullName } else { "N/A" }
            $result.ExeSize = $exeSize
            
            Write-Success "$profileName build success (exe: $exeSize)"
            
            # Package ZIP
            if (-not $SkipZip) {
                Compress-Archive -Path "$outDir\*" -DestinationPath $zipPath -Force
                $zipSize = Get-FileSizeMB $zipPath
                $result.ZipSize = $zipSize
                Write-Success "$profileName packaged -> $($result.ZipPath | Split-Path -Leaf) ($zipSize)"
            }
        }
        else {
            $errorContent = ""
            if (Test-Path "$outDir.error.log") {
                $errorContent = Get-Content "$outDir.error.log" -Raw
            }
            Write-Fail "$profileName build failed"
            if ($errorContent) {
                Write-Host "    Error: $errorContent" -ForegroundColor Red
            }
        }
        
        # Clean temp logs
        Remove-Item "$outDir.build.log" -ErrorAction SilentlyContinue
        Remove-Item "$outDir.error.log" -ErrorAction SilentlyContinue
        
        $results += $result
    }
    
    # ----------------------------------------------------------
    # Step 7: Publish Summary
    # ----------------------------------------------------------
    Write-Host ""
    Write-Header "Publish Complete Summary"
    Write-Host "  Application: $appName"
    Write-Host "  Version: v$newVersion"
    Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "  $("-" * 52)" -ForegroundColor DarkGray
    Write-Host "  Artifacts:" 
    
    foreach ($r in $results) {
        if ($r.Success) {
            $zipFile = $r.ZipPath | Split-Path -Leaf
            $size = if ($r.ZipSize) { $r.ZipSize } else { $r.ExeSize }
            Write-Success "$zipFile  ($size)"
        }
        else {
            Write-Fail "$($r.Name) build failed"
        }
    }
    
    Write-Host "  $("-" * 52)" -ForegroundColor DarkGray
    Write-Host "  Location: $outputBaseDir"
    Write-Host ""
    
    $successCount = ($results | Where-Object { $_.Success }).Count
    $totalCount = $results.Count
    
    if ($successCount -eq $totalCount) {
        Write-Host "  All $totalCount targets built successfully!" -ForegroundColor Green
    }
    else {
        Write-Host "  $successCount/$totalCount targets built successfully" -ForegroundColor Yellow
    }
    
    Write-Host ""
}
finally {
    Pop-Location
}
