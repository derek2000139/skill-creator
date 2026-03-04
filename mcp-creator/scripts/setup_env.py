#!/usr/bin/env python3
"""
MCP Server Environment Setup

Helps set up the environment for MCP servers.

Usage:
    python setup_env.py --action install-deps
    python setup_env.py --action create-env
    python setup_env.py --action check
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list, cwd: Path = None) -> bool:
    """Run a command and return success."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False
        )
        if result.returncode == 0:
            print(f"✅ Command succeeded: {' '.join(cmd)}")
            return True
        else:
            print(f"❌ Command failed: {' '.join(cmd)}")
            print(f"   Stderr: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("\n🔧 Installing dependencies...")
    deps = ["mcp>=1.0.0", "httpx>=0.27.0"]
    cmd = [sys.executable, "-m", "pip", "install"] + deps
    return run_command(cmd)


def create_env_file(server_dir: Path):
    """Create .env file from template."""
    print("\n🔧 Creating environment file...")
    env_example = server_dir / ".env.example"
    env_file = server_dir / ".env"
    
    if not env_example.exists():
        print(f"❌ .env.example not found in {server_dir}")
        return False
    
    if env_file.exists():
        print(f"⚠️  .env already exists, skipping")
        return True
    
    try:
        content = env_example.read_text(encoding="utf-8")
        env_file.write_text(content, encoding="utf-8")
        print(f"✅ Created .env file from .env.example")
        return True
    except Exception as e:
        print(f"❌ Error creating .env: {e}")
        return False


def check_environment():
    """Check current environment."""
    print("\n🔍 Checking environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        return False
    else:
        print("✅ Python version: OK")
    
    # Check dependencies
    print("\nChecking installed packages...")
    try:
        import mcp
        import httpx
        print(f"✅ mcp: v{mcp.__version__}")
        print(f"✅ httpx: v{httpx.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MCP Server Environment Setup")
    parser.add_argument("--action", required=True, choices=["install-deps", "create-env", "check"])
    parser.add_argument("--path", help="Path to server directory (for create-env)")
    args = parser.parse_args()

    if args.action == "install-deps":
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    elif args.action == "create-env":
        if not args.path:
            print("❌ --path is required for create-env")
            sys.exit(1)
        server_dir = Path(args.path).resolve()
        if not server_dir.exists():
            print(f"❌ Directory not found: {server_dir}")
            sys.exit(1)
        success = create_env_file(server_dir)
        sys.exit(0 if success else 1)
    
    elif args.action == "check":
        success = check_environment()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
