# dotnet-publish

.NET Desktop Application One-Click Publish Skill

## Description

This skill provides a complete automated publishing workflow for .NET desktop applications (WPF/WinForms), including:

- Version management (semver)
- Multi-platform publishing (win-x64, win-x86, win-arm64)
- ZIP packaging
- Changelog generation
- Win7 compatibility support

## Usage

In Trae dialog, simply say:

| Command | Action |
|---|---|
| `publish version` | Full flow, patch upgrade |
| `publish minor version` | Full flow, minor upgrade |
| `publish major version` | Full flow, major upgrade |
| `publish v2.0.0` | Full flow, use specified version |
| `build only no package` | Execute to step 6, skip ZIP packaging |
| `check current version` | Only read and display version |
| `init publish config` | Only create configuration file |

## Configuration

Create `publish-config.json` in your project root:

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
    }
  ]
}
```

## Configuration Fields

| Field | Description |
|---|---|
| `appName` | Application name, used for output file naming |
| `currentVersion` | Current version number, automatically updated |
| `projectPath` | Relative path to .csproj file |
| `outputBaseDir` | Publish output root directory |
| `rid` | Runtime identifier: win-x64 / win-x86 / win-arm64 |
| `framework` | Target framework: net6.0-windows / net8.0-windows |
| `selfContained` | Self-contained publish (no runtime needed) |
| `singleFile` | Single file publish |
| `trimmed` | IL trimming (smaller size) |
| `readyToRun` | Precompiled (faster startup) |

## Win7 Compatibility

For Windows 7 support:
1. Use `net6.0-windows` framework
2. Set `selfContained: true`
3. Users need KB2533623 and KB3063858 patches

## Backup Script

If the skill is unavailable, use the PowerShell script directly:

```powershell
.\scripts\publish.ps1
.\scripts\publish.ps1 -VersionBump minor
.\scripts\publish.ps1 -VersionBump "2.1.0"
.\scripts\publish.ps1 -SkipZip
```

## Files

```
dotnet-publish/
├── dotnet-publish.md      # Core skill file
├── README.md              # This file
└── scripts/
    └── publish.ps1        # PowerShell backup script
```
