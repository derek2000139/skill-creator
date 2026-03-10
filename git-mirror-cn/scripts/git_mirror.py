#!/usr/bin/env python3
"""
Git Mirror CN - GitHub Mirror Acceleration Tool for China

Usage:
    python git_mirror.py --action check-env
    python git_mirror.py --action locate
    python git_mirror.py --action enable [--mirror URL]
    python git_mirror.py --action disable
    python git_mirror.py --action status
    python git_mirror.py --action test
    python git_mirror.py --action switch
    python git_mirror.py --action auto
"""

import argparse
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Tuple

__version__ = "1.1.0"

MIRRORS: List[Dict[str, str]] = [
    {
        "name": "gh-proxy.com",
        "url": "https://gh-proxy.com/https://github.com",
        "raw_url": "https://gh-proxy.com/https://raw.githubusercontent.com",
        "desc": "Stable, fast response"
    },
    {
        "name": "cors.isteed.cc",
        "url": "https://cors.isteed.cc/github.com",
        "raw_url": "https://cors.isteed.cc/raw.githubusercontent.com",
        "desc": "Fast, reliable"
    },
    {
        "name": "hub.yzuu.cf",
        "url": "https://hub.yzuu.cf",
        "raw_url": "https://hub.yzuu.cf",
        "desc": "Good for large repos"
    },
    {
        "name": "gitclone.com",
        "url": "https://gitclone.com/github.com",
        "raw_url": "https://gitclone.com/github.com",
        "desc": "Classic mirror, stable"
    },
    {
        "name": "ghproxy.com",
        "url": "https://ghproxy.com/https://github.com",
        "raw_url": "https://ghproxy.com/https://raw.githubusercontent.com",
        "desc": "Popular proxy service"
    },
    {
        "name": "mirror.ghproxy.com",
        "url": "https://mirror.ghproxy.com/https://github.com",
        "raw_url": "https://mirror.ghproxy.com/https://raw.githubusercontent.com",
        "desc": "Alternative ghproxy"
    },
    {
        "name": "hub.fastgit.xyz",
        "url": "https://hub.fastgit.xyz",
        "raw_url": "https://hub.fastgit.xyz",
        "desc": "May be unstable"
    },
    {
        "name": "kgithub.com",
        "url": "https://kgithub.com",
        "raw_url": "https://kgithub.com",
        "desc": "Full GitHub mirror"
    },
]

TEST_REPO = "https://github.com/git/git.git"
TEST_TIMEOUT = 20


class SkillError(Exception):
    """Base error with recovery suggestion."""
    def __init__(self, message: str, suggestion: str = None):
        super().__init__(message)
        self.suggestion = suggestion
    
    def format(self) -> str:
        msg = f"Error: {self}"
        if self.suggestion:
            msg += f"\nSuggestion: {self.suggestion}"
        return msg


def run_command(cmd: List[str], timeout: int = 30, check: bool = True) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -3, "", str(e)


def check_environment() -> dict:
    """Check runtime dependencies. Returns status dict."""
    result = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_path": sys.executable,
        "platform": sys.platform,
        "script_path": str(Path(__file__).resolve()),
        "git": {"status": "unknown", "version": None},
        "all_ok": True,
        "errors": [],
    }
    
    if sys.version_info < (3, 9):
        result["errors"].append("Python 3.9+ required")
        result["all_ok"] = False
    
    ret, stdout, stderr = run_command(["git", "--version"], timeout=10, check=False)
    if ret == 0 and stdout:
        result["git"]["status"] = "ok"
        version_line = stdout.strip()
        if "git version" in version_line:
            result["git"]["version"] = version_line.replace("git version", "").strip()
    else:
        result["git"]["status"] = "missing"
        result["errors"].append("Git not found. Install from https://git-scm.com")
        result["all_ok"] = False
    
    return result


def print_env_report(info: dict):
    """Pretty-print environment check."""
    print("=" * 55)
    print("ENVIRONMENT CHECK")
    print("=" * 55)
    print(f"  Python  : {info['python_version']}")
    print(f"  Path    : {info['python_path']}")
    print(f"  Platform: {info['platform']}")
    print(f"  Script  : {info['script_path']}")
    
    git_status = info["git"]["status"]
    git_icon = "[OK]" if git_status == "ok" else "[MISSING]"
    git_ver = info["git"]["version"] or "N/A"
    print(f"  {git_icon} Git    : {git_ver}")
    
    if info["all_ok"]:
        print("\n  [OK] All dependencies satisfied!")
    else:
        for e in info["errors"]:
            print(f"  [ERROR] {e}")
    print("=" * 55)


def get_current_mirror() -> Optional[Dict[str, str]]:
    """Check if any mirror is currently configured."""
    ret, stdout, stderr = run_command(
        ["git", "config", "--global", "--get-regexp", r"^url\."],
        timeout=10,
        check=False
    )
    
    if ret != 0 or not stdout:
        return None
    
    for line in stdout.strip().split("\n"):
        for mirror in MIRRORS:
            if mirror["url"] in line and "github.com" in line:
                return mirror
    
    return None


def enable_mirror(mirror: Optional[Dict[str, str]] = None) -> bool:
    """Enable Git mirror acceleration."""
    if mirror is None:
        mirror = MIRRORS[0]
    
    disable_mirror()
    
    ret1, _, stderr1 = run_command(
        ["git", "config", "--global", f"url.{mirror['url']}.insteadOf", "https://github.com"],
        timeout=10,
        check=False
    )
    
    ret2, _, stderr2 = run_command(
        ["git", "config", "--global", f"url.{mirror['raw_url']}.insteadOf", "https://raw.githubusercontent.com"],
        timeout=10,
        check=False
    )
    
    if ret1 != 0:
        raise SkillError(
            f"Failed to configure mirror: {stderr1}",
            "Check if you have write permission to Git config"
        )
    
    return True


def disable_mirror() -> bool:
    """Disable all Git mirror configurations."""
    for mirror in MIRRORS:
        run_command(
            ["git", "config", "--global", "--unset-all", f"url.{mirror['url']}.insteadOf"],
            timeout=10,
            check=False
        )
        run_command(
            ["git", "config", "--global", "--unset-all", f"url.{mirror['raw_url']}.insteadOf"],
            timeout=10,
            check=False
        )
    
    ret, stdout, _ = run_command(
        ["git", "config", "--global", "--get-regexp", r"^url\."],
        timeout=10,
        check=False
    )
    
    if ret == 0 and stdout:
        for line in stdout.strip().split("\n"):
            if "github.com" in line:
                parts = line.split(".", 1)
                if len(parts) > 1:
                    url_part = parts[1].split(".insteadOf")[0]
                    run_command(
                        ["git", "config", "--global", "--unset-all", f"url.{url_part}.insteadOf"],
                        timeout=10,
                        check=False
                    )
    
    return True


def show_status():
    """Display current mirror configuration status."""
    print("=" * 55)
    print("GIT MIRROR CONFIGURATION STATUS")
    print("=" * 55)
    
    current = get_current_mirror()
    if current:
        print(f"[INFO] Mirror enabled: {current['name']}")
        print(f"       URL: {current['url']}")
    else:
        print("[WARN] No mirror configured (direct connection to GitHub)")
    
    print("\nFull Git URL configuration:")
    ret, stdout, stderr = run_command(
        ["git", "config", "--global", "--get-regexp", r"^url\."],
        timeout=10,
        check=False
    )
    
    if ret == 0 and stdout:
        for line in stdout.strip().split("\n"):
            print(f"  {line}")
    else:
        print("  (No URL rewrites configured)")
    
    print("=" * 55)


def test_mirrors(detailed: bool = False):
    """Test all available mirrors and report speeds."""
    print("=" * 55)
    print("TESTING MIRROR CONNECTION SPEED")
    print("=" * 55)
    print(f"Test repository: {TEST_REPO}")
    print("-" * 55)
    
    results = []
    
    for mirror in MIRRORS:
        test_url = TEST_REPO.replace("https://github.com", mirror["url"])
        print(f"Testing {mirror['name']}...", end=" ", flush=True)
        
        start = time.time()
        ret, stdout, stderr = run_command(
            ["git", "ls-remote", "--exit-code", test_url, "HEAD"],
            timeout=TEST_TIMEOUT,
            check=False
        )
        elapsed = (time.time() - start) * 1000
        
        if ret == 0:
            print(f"[OK] {elapsed:.0f}ms")
            results.append((mirror, elapsed, True))
        else:
            error_msg = stderr[:50] if stderr else "Connection failed"
            print(f"[FAILED] {error_msg}")
            results.append((mirror, elapsed, False))
    
    print("-" * 55)
    
    working = sorted([r for r in results if r[2]], key=lambda x: x[1])
    if working:
        print(f"\n[RECOMMEND] Working mirrors (sorted by speed):")
        for i, (m, t, _) in enumerate(working, 1):
            print(f"  {i}. {m['name']} ({t:.0f}ms) - {m['desc']}")
        print(f"\nFastest: {working[0][0]['name']} ({working[0][1]:.0f}ms)")
    else:
        print("\n[WARN] No mirrors are currently working!")
        print("       Check your network connection or try again later.")
    
    print("=" * 55)
    return working


def auto_select_mirror():
    """Automatically select and enable the fastest working mirror."""
    print("=" * 55)
    print("AUTO-SELECTING FASTEST MIRROR")
    print("=" * 55)
    print("Testing all mirrors...")
    print("-" * 55)
    
    working = []
    
    for mirror in MIRRORS:
        test_url = TEST_REPO.replace("https://github.com", mirror["url"])
        print(f"  {mirror['name']}...", end=" ", flush=True)
        
        start = time.time()
        ret, stdout, stderr = run_command(
            ["git", "ls-remote", "--exit-code", test_url, "HEAD"],
            timeout=TEST_TIMEOUT,
            check=False
        )
        elapsed = (time.time() - start) * 1000
        
        if ret == 0:
            print(f"[OK] {elapsed:.0f}ms")
            working.append((mirror, elapsed))
        else:
            print("[FAILED]")
    
    print("-" * 55)
    
    if working:
        fastest = min(working, key=lambda x: x[1])
        mirror, speed = fastest
        
        enable_mirror(mirror)
        print(f"\n[SUCCESS] Enabled fastest mirror: {mirror['name']}")
        print(f"          Speed: {speed:.0f}ms")
        print(f"          URL: {mirror['url']}")
        return mirror
    else:
        print("\n[ERROR] No working mirrors found!")
        print("        Please check your network connection.")
        return None


def interactive_switch():
    """Interactive mirror selection."""
    print("=" * 55)
    print("SELECT MIRROR SOURCE")
    print("=" * 55)
    print("0) Disable mirror (direct connection)")
    print("A) Auto-select fastest (recommended)")
    
    current = get_current_mirror()
    
    for i, mirror in enumerate(MIRRORS, 1):
        marker = " (current)" if current and current["name"] == mirror["name"] else ""
        print(f"{i}) {mirror['name']}{marker} - {mirror['desc']}")
    
    print("-" * 55)
    
    try:
        choice = input("Select [0-{}, A]: ".format(len(MIRRORS))).strip().upper()
        
        if choice == "A":
            auto_select_mirror()
        elif choice == "0":
            disable_mirror()
            print("[INFO] Mirror disabled. Using direct connection to GitHub.")
        else:
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(MIRRORS):
                    selected = MIRRORS[choice_num - 1]
                    enable_mirror(selected)
                    print(f"[INFO] Mirror enabled: {selected['name']}")
                else:
                    print("[ERROR] Invalid selection")
                    return False
            except ValueError:
                print("[ERROR] Please enter a number or 'A'")
                return False
        
        return True
    except KeyboardInterrupt:
        print("\n[CANCELLED]")
        return False


def clone_with_mirror(repo_url: str, dest: str = None, depth: int = None):
    """Clone a repository using the best available mirror."""
    print("=" * 55)
    print("CLONE WITH MIRROR")
    print("=" * 55)
    
    working = []
    print("Finding fastest mirror...")
    
    for mirror in MIRRORS[:5]:
        test_url = repo_url.replace("https://github.com", mirror["url"])
        print(f"  Testing {mirror['name']}...", end=" ", flush=True)
        
        start = time.time()
        ret, _, _ = run_command(
            ["git", "ls-remote", "--exit-code", test_url, "HEAD"],
            timeout=10,
            check=False
        )
        elapsed = (time.time() - start) * 1000
        
        if ret == 0:
            print(f"[OK] {elapsed:.0f}ms")
            working.append((mirror, elapsed))
        else:
            print("[FAILED]")
    
    if not working:
        print("\n[ERROR] No working mirrors found for this repository!")
        return False
    
    fastest = min(working, key=lambda x: x[1])
    mirror, speed = fastest
    
    clone_url = repo_url.replace("https://github.com", mirror["url"])
    
    cmd = ["git", "clone", clone_url]
    if depth:
        cmd.extend(["--depth", str(depth)])
    if dest:
        cmd.append(dest)
    
    print(f"\n[INFO] Using mirror: {mirror['name']} ({speed:.0f}ms)")
    print(f"[INFO] Clone URL: {clone_url}")
    print("-" * 55)
    
    ret, stdout, stderr = run_command(cmd, timeout=300, check=False)
    
    if ret == 0:
        print("\n[SUCCESS] Repository cloned successfully!")
        return True
    else:
        print(f"\n[ERROR] Clone failed: {stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Git Mirror CN - GitHub Mirror Acceleration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python git_mirror.py --action enable
  python git_mirror.py --action enable --mirror "https://gitclone.com/github.com"
  python git_mirror.py --action disable
  python git_mirror.py --action status
  python git_mirror.py --action test
  python git_mirror.py --action switch
  python git_mirror.py --action auto
  python git_mirror.py --action clone --repo "https://github.com/user/repo.git"
        """
    )
    
    parser.add_argument(
        "--action",
        required=True,
        choices=["check-env", "locate", "enable", "disable", "status", "test", "switch", "auto", "clone"],
        help="Action to perform"
    )
    
    parser.add_argument(
        "--mirror",
        type=str,
        default=None,
        help="Custom mirror URL for enable action"
    )
    
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Repository URL for clone action"
    )
    
    parser.add_argument(
        "--dest",
        type=str,
        default=None,
        help="Destination directory for clone action"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Clone depth (shallow clone)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    args = parser.parse_args()
    
    if args.action == "locate":
        print(f"Script: {Path(__file__).resolve()}")
        print(f"Dir:    {Path(__file__).resolve().parent}")
        sys.exit(0)
    
    if args.action == "check-env":
        info = check_environment()
        print_env_report(info)
        sys.exit(0 if info["all_ok"] else 1)
    
    try:
        if args.action == "enable":
            mirror = None
            if args.mirror:
                for m in MIRRORS:
                    if args.mirror in m["url"] or args.mirror == m["name"]:
                        mirror = m
                        break
                if not mirror:
                    mirror = {
                        "name": "custom",
                        "url": args.mirror,
                        "raw_url": args.mirror.replace("github.com", "raw.githubusercontent.com")
                            if "github.com" in args.mirror else args.mirror,
                        "desc": "Custom mirror"
                    }
            
            enable_mirror(mirror)
            current = get_current_mirror()
            if current:
                print(f"[INFO] Git mirror acceleration enabled")
                print(f"[INFO] Current mirror: {current['url']}")
        
        elif args.action == "disable":
            disable_mirror()
            print("[INFO] Git mirror acceleration disabled")
            print("[INFO] Using direct connection to GitHub")
        
        elif args.action == "status":
            show_status()
        
        elif args.action == "test":
            test_mirrors()
        
        elif args.action == "switch":
            interactive_switch()
        
        elif args.action == "auto":
            result = auto_select_mirror()
            sys.exit(0 if result else 1)
        
        elif args.action == "clone":
            if not args.repo:
                print("[ERROR] --repo is required for clone action")
                sys.exit(1)
            result = clone_with_mirror(args.repo, args.dest, args.depth)
            sys.exit(0 if result else 1)
        
        sys.exit(0)
    
    except SkillError as e:
        print(e.format(), file=sys.stderr)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[WARN] Operation cancelled", file=sys.stderr)
        sys.exit(130)
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"\nSuggestion: Run 'python \"{__file__}\" --action check-env' to diagnose", 
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
