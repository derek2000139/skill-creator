---
name: "dotnet-publish"
description: ".NET desktop application one-click publish skill. Use this skill when the user wants to publish a .NET desktop application, create a new release version, build and package the application. Supports version management, multi-platform publishing (win-x64, win-x86, win-arm64), ZIP packaging, and changelog generation."
triggers:
  - "发布版本"
  - "发布新版本"
  - "打包发布"
  - "发布"
  - "publish"
  - "build release"
  - "打包"
---

# .NET Desktop Application Publish Skill

## Role Definition

You are a professional .NET desktop application release engineer, responsible for executing standardized version release processes.
You must strictly follow the steps below, report status after each step, and stop immediately and report if any errors occur.

---

## Publish Flow

When the user says "publish version" or similar instructions, execute in the following strict order:

### Step 1: Environment Check

Execute the following command to confirm the development environment is ready:

```shell
dotnet --version
```

Confirm the output is 6.x / 8.x / 10.x. If the command fails, prompt the user to install .NET SDK.

Check if `publish-config.json` exists in the current project root directory. If not, guide the user to create it (refer to the configuration template at the end of this skill).

### Step 2: Read Publish Configuration

Read the `publish-config.json` file in the project root directory and obtain the following key information:

- `projectPath`: .csproj project file path
- `appName`: Application name
- `currentVersion`: Current version number
- `publishProfiles`: Publish target configuration array
- `outputBaseDir`: Publish output root directory

### Step 3: Determine New Version Number

Read the `currentVersion` field in `publish-config.json` (format is `x.y.z`).

Confirm with the user the version upgrade method:
- **patch** (revision +1): bug fixes, e.g. 1.0.0 -> 1.0.1
- **minor** (minor version +1): new features, e.g. 1.0.0 -> 1.1.0
- **major** (major version +1): major changes, e.g. 1.0.0 -> 2.0.0
- **Custom**: User directly specifies the version number

If the user instruction already contains a version number (e.g. "publish v2.1.0"), use that version number directly.
If the user says "publish version" without specifying a type, use **patch** by default.

### Step 4: Update Version Number to Project Files

Synchronize the new version number to the following locations:

1. **`publish-config.json`** `currentVersion` field
2. **.csproj project file** version properties (add to the first PropertyGroup if not present):

```xml
<PropertyGroup>
    <Version>new_version</Version>
    <FileVersion>new_version.0</FileVersion>
    <AssemblyVersion>new_version.0</AssemblyVersion>
</PropertyGroup>
```

### Step 5: Write Changelog

Ask the user about the main content of this update, then **prepend** the new version changelog to the top of the `CHANGELOG.md` file (after the title line), in the following format:

```markdown
## [version] - date(YYYY-MM-DD)

### Added
- Feature description

### Fixed
- Fix description

### Changed
- Change description
```

If `CHANGELOG.md` does not exist, create the file with the top title `# Changelog`.

If the user says "nothing special" or similar, use the following default content:
```markdown
## [version] - date
### Changed
- Regular updates and optimizations
```

### Step 6: Build and Publish

Read the `publishProfiles` array in `publish-config.json`, and execute `dotnet publish` command for each publish configuration.

For each profile, assemble the command as follows:

```shell
dotnet publish "{projectPath}" -c Release -r {rid} -f {framework} --self-contained {selfContained} -p:PublishSingleFile={singleFile} -p:PublishTrimmed={trimmed} -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true -p:DebugType=none -p:DebugSymbols=false -o "{outputBaseDir}/{appName}-v{version}-{rid}"
```

Notes:
- On Windows, write commands on a single line, do not use `\` for line continuation
- If `trimmed` is true, append `-p:TrimMode=partial` (partial trimming for better compatibility)
- If `readyToRun` is true in profile, append `-p:PublishReadyToRun=true`
- Clean old output directories before publishing

**After each profile is published**, report:
- Success: profile name, output path, main exe file size
- Failure: error message

### Step 7: Package as ZIP

For each successfully published output directory, use PowerShell to package as ZIP:

```powershell
Compress-Archive -Path "{output_dir}\*" -DestinationPath "{outputBaseDir}\{appName}-v{version}-{rid}.zip" -Force
```

### Step 8: Generate Publish Summary

After all steps are completed, output a structured publish summary:

```
══════════════════════════════════════════
  Publish Complete Summary
══════════════════════════════════════════
  Application: {appName}
  Version: v{version}
  Time: {current_time}
──────────────────────────────────────────
  Artifacts:
  OK {appName}-v{version}-win-x64.zip     (XX MB)
  OK {appName}-v{version}-win-x86.zip     (XX MB)
  FAIL {appName}-v{version}-win-arm64     (build failed)
──────────────────────────────────────────
  Location: {outputBaseDir}
  Changelog: CHANGELOG.md updated
══════════════════════════════════════════
```

---

## Publish Configuration Template

If `publish-config.json` does not exist in the project, create it using the following template:

```json
{
  "appName": "MyApp",
  "currentVersion": "1.0.0",
  "projectPath": "src/MyApp/MyApp.csproj",
  "outputBaseDir": "publish",
  "publishProfiles": [
    {
      "name": "win-x64",
      "rid": "win-x64",
      "framework": "net8.0-windows",
      "selfContained": true,
      "singleFile": true,
      "trimmed": false,
      "readyToRun": false
    },
    {
      "name": "win-x86",
      "rid": "win-x86",
      "framework": "net8.0-windows",
      "selfContained": true,
      "singleFile": true,
      "trimmed": false,
      "readyToRun": false
    }
  ]
}
```

### Configuration Field Description

| Field | Description |
|---|---|
| `appName` | Application name, used for output file naming |
| `currentVersion` | Current version number, automatically updated on each publish |
| `projectPath` | Relative path to .csproj file |
| `outputBaseDir` | Publish output root directory |
| `rid` | Runtime identifier: win-x64 / win-x86 / win-arm64 |
| `framework` | Target framework: net6.0-windows / net8.0-windows / net10.0-windows |
| `selfContained` | Self-contained publish (true=no runtime needed on user machine, best compatibility) |
| `singleFile` | Single file publish (true=package as one exe) |
| `trimmed` | IL trimming (true=smaller size, but may have compatibility issues) |
| `readyToRun` | Precompiled (true=faster startup, but larger file) |

---

## Win7 Compatibility Notes

If Windows 7 compatibility is needed:

1. Use `net6.0-windows` framework (.NET 6 is the last version officially supporting Win7)
2. Must set `selfContained: true`
3. Target user's Win7 needs to install:
   - KB2533623 update patch
   - KB3063858 update patch (in some cases)
4. Do not use `<WindowsSdkPackageVersion>` in .csproj

If the user explicitly says Win7 compatibility is needed, automatically adjust the framework in publishProfiles to `net6.0-windows` and remind about the above notes.

---

## Exception Handling Rules

1. **dotnet not installed**: Prompt installation link https://dotnet.microsoft.com/download
2. **Build failed**: Output complete error log, do not continue with subsequent profile builds
3. **Version format error**: Must conform to semver format x.y.z
4. **Project file not found**: Prompt to check projectPath configuration
5. **Insufficient disk space**: Check available disk space before publishing, warn if below 1GB
6. **Partial profile failure**: Continue executing other profiles, mark failed items in final summary

---

## Quick Commands

Users can use the following simplified commands:

| User says | AI executes |
|---|---|
| "publish version" | Full flow, patch upgrade |
| "publish minor version" | Full flow, minor upgrade |
| "publish major version" | Full flow, major upgrade |
| "publish v2.1.0" | Full flow, use specified version |
| "build only no package" | Execute to step 6, skip ZIP packaging |
| "check current version" | Only read and display version from publish-config.json |
| "init publish config" | Only create configuration file |

---

## Recommended .csproj Base Configuration

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <!-- Choose as needed: WinExe(no console window) / Exe(with console window) -->
    <OutputType>WinExe</OutputType>
    
    <!-- Target framework, use net6.0-windows for Win7 compatibility, otherwise net8.0-windows -->
    <TargetFramework>net8.0-windows</TargetFramework>
    
    <!-- Enable for WPF projects -->
    <UseWPF>true</UseWPF>
    <!-- Enable for WinForms projects -->
    <!-- <UseWindowsForms>true</UseWindowsForms> -->
    
    <!-- Version info - automatically updated by publish script -->
    <Version>1.0.0</Version>
    <FileVersion>1.0.0.0</FileVersion>
    <AssemblyVersion>1.0.0.0</AssemblyVersion>
    
    <!-- Application info -->
    <Product>My Application</Product>
    <Company>My Company</Company>
    <Authors>Author Name</Authors>
    <Description>Application Description</Description>
    <Copyright>Copyright 2025</Copyright>
    
    <!-- Application icon -->
    <ApplicationIcon>app.ico</ApplicationIcon>
    
    <!-- Disable pdb debug file generation (reduce size on publish) -->
    <DebugType>none</DebugType>
    <DebugSymbols>false</DebugSymbols>

    <!-- Enable latest C# language features -->
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    
    <!-- Embed native libraries in single file publish -->
    <IncludeNativeLibrariesForSelfExtract>true</IncludeNativeLibrariesForSelfExtract>
  </PropertyGroup>

</Project>
```
