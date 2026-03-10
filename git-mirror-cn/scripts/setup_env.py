#!/usr/bin/env python3
"""
Environment setup helper for Git Mirror CN skill.
Checks and validates dependencies.
"""

import subprocess
import sys
from pathlib import Path

MIN_PY = (3, 9)


def check_git():
    """Check if Git is installed and accessible."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip().replace("git version", "").strip()
            return True, version
        return False, None
    except Exception:
        return False, None


def main():
    print("=" * 50)
    print("Git Mirror CN - Environment Setup")
    print("=" * 50)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Path: {sys.executable}")
    print("-" * 50)
    
    if sys.version_info < MIN_PY:
        print(f"[ERROR] Python {MIN_PY[0]}.{MIN_PY[1]}+ required")
        sys.exit(1)
    else:
        print(f"[OK] Python version >= {MIN_PY[0]}.{MIN_PY[1]}")
    
    git_ok, git_ver = check_git()
    if git_ok:
        print(f"[OK] Git: {git_ver}")
    else:
        print("[ERROR] Git not found!")
        print("       Install Git from: https://git-scm.com")
        print("       After installation, restart your terminal and try again.")
    
    print("-" * 50)
    
    if git_ok:
        print("\n[OK] Environment is ready!")
        print("\nQuick start:")
        print("  python git_mirror.py --action status   # Check current config")
        print("  python git_mirror.py --action test     # Test mirror speeds")
        print("  python git_mirror.py --action enable   # Enable mirror")
    else:
        print("\n[ERROR] Please install Git first.")
        sys.exit(1)
    
    print("=" * 50)


if __name__ == "__main__":
    main()
