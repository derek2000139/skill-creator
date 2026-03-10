---
name: git-mirror-cn
version: 1.1.0
description: >
  Use this skill when the user wants to clone or pull from GitHub but faces network
  issues in China, or when the user asks to configure Git mirror acceleration, 
  speed up GitHub access, or fix Git clone timeout errors. This skill helps 
  configure Chinese mirror proxies for GitHub, test mirror speeds, and manage
  mirror settings. Supports enabling/disabling mirrors, testing connectivity,
  auto-selecting fastest mirror, and direct clone with best mirror.
triggers:
  keywords:
    - "git clone"
    - "github"
    - "mirror"
    - "镜像"
    - "加速"
    - "国内源"
    - "github访问慢"
    - "git超时"
    - "clone失败"
    - "github mirror"
    - "git proxy"
    - "gitclone"
    - "ghproxy"
    - "fastgit"
    - "kgithub"
platform: [windows, macos, linux]
dependencies:
  runtime: "python>=3.9"
  packages: []
---

# Git Mirror CN - GitHub 国内镜像加速工具

## Overview

This skill helps users in China configure Git to use mirror proxies for GitHub access.
It solves the common problem of slow or failed `git clone`/`git pull` operations due to
network restrictions. The skill uses Git's built-in `url.insteadOf` feature to automatically
redirect GitHub URLs through Chinese mirror services.

**Key Features:**
- **8 mirror sources** tested and verified working
- Auto-select fastest mirror with one command
- Direct clone with automatic mirror selection
- Test all mirrors and compare speeds
- Enable/disable mirror acceleration
- Cross-platform support (Windows/macOS/Linux)

**Important Limitation:**
> Mirror acceleration is ONLY for read operations (clone/pull/fetch).
> Push operations will fail because mirrors don't support write access.
> Disable mirrors before pushing to GitHub.

## Prerequisites / Setup

### Requirements
- Git installed and accessible from command line
- Python 3.9+ (for the helper script)
- Network access to at least one mirror service

### First-Time Setup

**Step 1: Locate the script**
```powershell
# Windows PowerShell
Get-ChildItem -Path . -Recurse -Filter "git_mirror.py" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
```
```bash
# macOS/Linux
find . -name "git_mirror.py" -type f 2>/dev/null | head -1
```

**Step 2: Check environment**
```powershell
python "path/to/git_mirror.py" --action check-env
```

**Step 3: Verify Git is installed**
```powershell
git --version
```

## Decision Tree

```
User mentions GitHub/Git access issues
├─ What is the user trying to do?
│  ├─ Clone a repository → Use --action clone or --action auto
│  │  ├─ With auto → Find fastest mirror and clone
│  │  └─ With clone → Test mirrors, pick fastest, clone
│  │
│  ├─ Push to GitHub → WARNING: Disable mirror first!
│  │  └─ Mirror enabled → Disable mirror, then push
│  │
│  ├─ Configure mirror → What operation?
│  │  ├─ Enable → Run enable action
│  │  ├─ Disable → Run disable action
│  │  ├─ Check status → Run status action
│  │  ├─ Test mirrors → Run test action
│  │  ├─ Auto select → Run auto action (recommended)
│  │  └─ Switch mirror → Run switch action
│  │
│  └─ Unknown → Ask clarifying question
│
└─ Proactive: If git clone fails with timeout/network error
   └─ Suggest using --action auto or --action clone
```

## Core Workflows

### Workflow 1: Auto-Select Fastest Mirror (Recommended)

**When to use:** User wants the best mirror automatically selected.

**Steps:**

```powershell
python "SCRIPT_PATH/git_mirror.py" --action auto
```

**Expected output:**
```
=======================================================
AUTO-SELECTING FASTEST MIRROR
=======================================================
Testing all mirrors...
-------------------------------------------------------
  gh-proxy.com... [OK] 1234ms
  cors.isteed.cc... [OK] 2345ms
  hub.yzuu.cf... [OK] 3456ms
  gitclone.com... [OK] 4567ms
  ghproxy.com... [FAILED]
-------------------------------------------------------

[SUCCESS] Enabled fastest mirror: gh-proxy.com
          Speed: 1234ms
          URL: https://gh-proxy.com/https://github.com
```

### Workflow 2: Direct Clone with Auto Mirror

**When to use:** User wants to clone a repo without configuring global mirror.

**Steps:**

```powershell
python "SCRIPT_PATH/git_mirror.py" --action clone --repo "https://github.com/user/repo.git" --depth 1
```

**Expected output:**
```
=======================================================
CLONE WITH MIRROR
=======================================================
Finding fastest mirror...
  Testing gh-proxy.com... [OK] 1234ms
  Testing cors.isteed.cc... [OK] 2345ms
  Testing hub.yzuu.cf... [FAILED]

[INFO] Using mirror: gh-proxy.com (1234ms)
[INFO] Clone URL: https://gh-proxy.com/https://github.com/user/repo.git
-------------------------------------------------------

[SUCCESS] Repository cloned successfully!
```

### Workflow 3: Test All Mirrors

**When to use:** User wants to see which mirrors are working and their speeds.

**Steps:**

```powershell
python "SCRIPT_PATH/git_mirror.py" --action test
```

**Expected output:**
```
=======================================================
TESTING MIRROR CONNECTION SPEED
=======================================================
Test repository: https://github.com/git/git.git
-------------------------------------------------------
Testing gh-proxy.com... [OK] 1234ms
Testing cors.isteed.cc... [OK] 2345ms
Testing hub.yzuu.cf... [OK] 3456ms
Testing gitclone.com... [OK] 4567ms
Testing ghproxy.com... [FAILED] Connection failed
Testing mirror.ghproxy.com... [FAILED] Connection failed
Testing hub.fastgit.xyz... [FAILED] Connection reset
Testing kgithub.com... [FAILED] Could not connect
-------------------------------------------------------

[RECOMMEND] Working mirrors (sorted by speed):
  1. gh-proxy.com (1234ms) - Stable, fast response
  2. cors.isteed.cc (2345ms) - Fast, reliable
  3. hub.yzuu.cf (3456ms) - Good for large repos
  4. gitclone.com (4567ms) - Classic mirror, stable

Fastest: gh-proxy.com (1234ms)
=======================================================
```

### Workflow 4: Enable Specific Mirror

**When to use:** User wants to use a specific mirror permanently.

**Steps:**

1. Enable default mirror (gh-proxy.com):
```powershell
python "SCRIPT_PATH/git_mirror.py" --action enable
```

2. Or enable specific mirror by name:
```powershell
python "SCRIPT_PATH/git_mirror.py" --action enable --mirror "gitclone.com"
```

3. Or enable with custom URL:
```powershell
python "SCRIPT_PATH/git_mirror.py" --action enable --mirror "https://your-mirror.com/github.com"
```

### Workflow 5: Disable Mirror (Before Push)

**When to use:** User needs to push code to GitHub (mirrors don't support push).

**Steps:**

1. Disable mirror:
```powershell
python "SCRIPT_PATH/git_mirror.py" --action disable
```

2. Perform push operation:
```powershell
git push origin main
```

3. Re-enable mirror after push (optional):
```powershell
python "SCRIPT_PATH/git_mirror.py" --action auto
```

### Workflow 6: Interactive Mirror Selection

**When to use:** User wants to manually choose a mirror.

**Steps:**

```powershell
python "SCRIPT_PATH/git_mirror.py" --action switch
```

**Expected output:**
```
=======================================================
SELECT MIRROR SOURCE
=======================================================
0) Disable mirror (direct connection)
A) Auto-select fastest (recommended)
1) gh-proxy.com - Stable, fast response
2) cors.isteed.cc - Fast, reliable
3) hub.yzuu.cf - Good for large repos
4) gitclone.com - Classic mirror, stable
5) ghproxy.com - Popular proxy service
6) mirror.ghproxy.com - Alternative ghproxy
7) hub.fastgit.xyz - May be unstable
8) kgithub.com - Full GitHub mirror
-------------------------------------------------------
Select [0-8, A]: 
```

## Parameter Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--action` | Yes | Action to perform (see table below) |
| `--mirror` | No | Custom mirror URL or name for `enable` action |
| `--repo` | Yes for clone | Repository URL for `clone` action |
| `--dest` | No | Destination directory for `clone` action |
| `--depth` | No | Clone depth (shallow clone) for `clone` action |

### Available Actions

| Action | Description |
|--------|-------------|
| `auto` | Auto-select and enable fastest mirror (recommended) |
| `clone` | Clone repo with automatic mirror selection |
| `test` | Test all mirrors and show speeds |
| `enable` | Enable mirror (default or specified) |
| `disable` | Disable all mirror configurations |
| `status` | Show current mirror configuration |
| `switch` | Interactive mirror selection |
| `check-env` | Check environment dependencies |
| `locate` | Show script path |

### Available Mirror Sources

| Mirror | URL | Notes |
|--------|-----|-------|
| gh-proxy.com | `https://gh-proxy.com/https://github.com` | **Recommended**, stable & fast |
| cors.isteed.cc | `https://cors.isteed.cc/github.com` | Fast, reliable |
| hub.yzuu.cf | `https://hub.yzuu.cf` | Good for large repos |
| gitclone.com | `https://gitclone.com/github.com` | Classic mirror |
| ghproxy.com | `https://ghproxy.com/https://github.com` | Popular proxy |
| mirror.ghproxy.com | `https://mirror.ghproxy.com/https://github.com` | Alternative ghproxy |
| hub.fastgit.xyz | `https://hub.fastgit.xyz` | May be unstable |
| kgithub.com | `https://kgithub.com` | Full GitHub mirror |

## Pattern Library / Templates

### Template 1: Quick Clone (One Command)
```powershell
# Clone with auto mirror selection
python "SCRIPT_PATH/git_mirror.py" --action clone --repo "https://github.com/vuejs/vue.git" --depth 1
```

### Template 2: Setup and Clone
```powershell
# Step 1: Auto-select fastest mirror
python "SCRIPT_PATH/git_mirror.py" --action auto

# Step 2: Clone normally (auto-redirected through mirror)
git clone https://github.com/vuejs/vue.git
```

### Template 3: Push Workflow
```powershell
# Step 1: Disable mirror before push
python "SCRIPT_PATH/git_mirror.py" --action disable

# Step 2: Push to GitHub
git push origin main

# Step 3: Re-enable auto-select
python "SCRIPT_PATH/git_mirror.py" --action auto
```

### Template 4: Manual Mirror URL
```powershell
# Use specific mirror for one clone
git clone https://gh-proxy.com/https://github.com/user/repo.git
```

## Error Handling

### Error Mapping Table

| Error Message | Possible Cause | Recovery Action |
|--------------|----------------|-----------------|
| `git: command not found` | Git not installed | Install Git from https://git-scm.com |
| `fatal: unable to access` | Mirror service down | Run `--action test` to find working mirror |
| `fatal: repository not found` | Invalid repo URL | Verify the GitHub URL is correct |
| `Permission denied (publickey)` | SSH key issue | Use HTTPS URL instead of SSH |
| `Connection timed out` | Network/Mirror issue | Run `--action auto` to find best mirror |
| `SSL certificate problem` | SSL verification issue | Check network proxy settings |
| `error: failed to push` | Mirror doesn't support push | Run `--action disable` before pushing |
| `python: command not found` | Python not installed | Install Python 3.9+ |
| `No working mirrors found` | All mirrors down | Check network, try VPN, or wait |

### Error Recovery Workflow

```
Command Failed
├─ Is it a network error?
│  ├─ YES → Run --action auto to find working mirror
│  │        └─ Or run --action test to see all options
│  └─ NO → Continue below
│
├─ Is it a push error?
│  ├─ YES → Mirror is enabled!
│  │        └─ Run --action disable
│  │        └─ Retry push
│  └─ NO → Continue below
│
├─ Is it a Git not found error?
│  ├─ YES → Install Git
│  └─ NO → Continue below
│
├─ Is it a Python not found error?
│  ├─ YES → Install Python 3.9+
│  └─ NO → Run --action check-env
│
└─ Unknown error → Check Git and network configuration
```

## Complete Examples

### Example 1: Clone a Large Repository

**User says:** "帮我克隆 vuejs/vue 这个仓库，太慢了"

**Step 1: Use auto clone**
```powershell
python "d:/tools/skills/git-mirror-cn/scripts/git_mirror.py" --action clone --repo "https://github.com/vuejs/vue.git" --depth 1
```

Output:
```
=======================================================
CLONE WITH MIRROR
=======================================================
Finding fastest mirror...
  Testing gh-proxy.com... [OK] 1234ms
  Testing cors.isteed.cc... [OK] 2345ms

[INFO] Using mirror: gh-proxy.com (1234ms)
[INFO] Clone URL: https://gh-proxy.com/https://github.com/vuejs/vue.git
-------------------------------------------------------
Cloning into 'vue'...
remote: Enumerating objects: 5000, done.
Receiving objects: 100% (5000/5000), 15.00 MiB | 2.50 MiB/s, done.

[SUCCESS] Repository cloned successfully!
```

### Example 2: Setup Permanent Mirror

**User says:** "配置一个最快的镜像"

**Step 1: Auto-select**
```powershell
python "d:/tools/skills/git-mirror-cn/scripts/git_mirror.py" --action auto
```

**Step 2: Clone normally**
```powershell
git clone https://github.com/any/repo.git
```

### Example 3: Fix Clone Timeout

**User says:** "git clone 一直超时怎么办"

**Step 1: Test mirrors**
```powershell
python "d:/tools/skills/git-mirror-cn/scripts/git_mirror.py" --action test
```

**Step 2: Use fastest or auto**
```powershell
python "d:/tools/skills/git-mirror-cn/scripts/git_mirror.py" --action auto
```

**Step 3: Retry clone**
```powershell
git clone https://github.com/user/repo.git
```

## Platform-Specific Notes

### Windows (PowerShell)

- Use double quotes for paths with spaces
- Use `;` to chain commands (not `&&`)
- Use `Select-String` instead of `grep`
- Path separator: `\` or `/` both work

```powershell
# Check Git config
git config --global --list | Select-String "url."
```

### macOS / Linux (Bash)

- Use `&&` to chain commands
- Use `grep` for filtering
- May need `chmod +x` for script execution

```bash
# Check Git config
git config --global --list | grep "url."
```

## Known Pitfalls

### Pitfall 1: Push Fails with Mirror Enabled

**Symptom:** `git push` returns error like "Repository not found" or "Access denied"

**Cause:** Mirror services only support read operations (clone/pull/fetch), not write operations (push)

**Solution:** Always disable mirror before pushing:
```powershell
python "SCRIPT_PATH/git_mirror.py" --action disable
git push origin main
python "SCRIPT_PATH/git_mirror.py" --action auto  # Re-enable after
```

### Pitfall 2: All Mirrors Down

**Symptom:** `--action test` shows all mirrors failed

**Cause:** Network issues or all mirrors temporarily unavailable

**Solution:** 
1. Check your network connection
2. Try again later (mirrors may recover)
3. Consider using VPN
4. Use `--action clone` which will try multiple mirrors

### Pitfall 3: SSH URLs Not Redirected

**Symptom:** `git clone git@github.com:user/repo.git` still slow

**Cause:** The mirror only redirects HTTPS URLs, not SSH URLs

**Solution:** Use HTTPS URL instead:
```powershell
# Change from:
git clone git@github.com:user/repo.git

# To:
git clone https://github.com/user/repo.git
```

### Pitfall 4: Slow Clone Even with Mirror

**Symptom:** Clone is still slow after enabling mirror

**Cause:** The selected mirror may be slow or overloaded

**Solution:** Run `--action auto` to find the fastest mirror at that moment

## Notes

### Performance Tips

1. **Use --action auto:** Automatically finds the fastest working mirror
2. **Use --action clone:** One-command clone with auto mirror selection
3. **Use --depth 1:** For large repos, shallow clone is much faster
4. **Disable when pushing:** Keep mirror disabled if you frequently push

### Security Considerations

- Mirror services are third-party and may log access patterns
- For sensitive/private repositories, consider using direct connection with VPN
- SSH keys and credentials are not affected by mirror configuration

### Limitations

- Only works with HTTPS URLs (not SSH)
- Does not support push operations
- May not work with all GitHub features (API, releases, etc.)
- Mirror availability varies by region and time

> [!IMPORTANT]
> - Do NOT modify the script source code unless necessary
> - Do NOT enable mirror when you need to push code
> - Do NOT assume mirror will work for all GitHub operations
> - Do NOT forget to run `--action auto` if experiencing issues
> - Do NOT use SSH URLs with mirror (use HTTPS instead)
