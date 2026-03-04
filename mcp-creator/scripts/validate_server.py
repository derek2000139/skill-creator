#!/usr/bin/env python3
"""
MCP Server Validator

Validates generated MCP server projects for correctness and security.

Usage:
    python validate_server.py --path ./my-server
"""

import argparse
import os
import sys
import json
from pathlib import Path


def check_file_exists(path: Path, filename: str) -> bool:
    """Check if file exists."""
    file_path = path / filename
    if file_path.exists():
        print(f"✅ {filename}: Found")
        return True
    else:
        print(f"❌ {filename}: Missing")
        return False


def check_core_files(server_dir: Path) -> bool:
    """Check core files."""
    print("\n🔍 Checking core files...")
    files = [
        "server.py",
        "tools.py",
        "security.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
    ]
    all_found = True
    for file in files:
        if not check_file_exists(server_dir, file):
            all_found = False
    return all_found


def check_ide_configs(server_dir: Path) -> bool:
    """Check IDE configs."""
    print("\n🔍 Checking IDE configs...")
    ide_dir = server_dir / "ide_configs"
    if not ide_dir.exists():
        print("❌ ide_configs/: Missing")
        return False
    
    configs = ["trae_config.json", "cursor_mcp.json", "claude_config.json"]
    all_found = True
    for config in configs:
        if not check_file_exists(ide_dir, config):
            all_found = False
    return all_found


def check_skill_file(server_dir: Path) -> bool:
    """Check companion skill file."""
    print("\n🔍 Checking companion skill...")
    skill_dir = server_dir / "skill"
    if not skill_dir.exists():
        print("❌ skill/: Missing")
        return False
    
    skill_files = list(skill_dir.glob("*.md"))
    if skill_files:
        print(f"✅ Companion skill: Found ({skill_files[0].name})")
        return True
    else:
        print("❌ Companion skill: Missing")
        return False


def check_test_file(server_dir: Path) -> bool:
    """Check test file."""
    print("\n🔍 Checking test file...")
    return check_file_exists(server_dir, "test_server.py")


def check_requirements(server_dir: Path) -> bool:
    """Check requirements.txt."""
    print("\n🔍 Checking dependencies...")
    req_file = server_dir / "requirements.txt"
    if not req_file.exists():
        return False
    
    content = req_file.read_text(encoding="utf-8")
    required = ["mcp", "httpx"]
    all_found = True
    for dep in required:
        if dep in content:
            print(f"✅ Dependency: {dep}")
        else:
            print(f"❌ Dependency: {dep} (missing)")
            all_found = False
    return all_found


def check_security(server_dir: Path) -> bool:
    """Check security.py."""
    print("\n🔍 Checking security utilities...")
    sec_file = server_dir / "security.py"
    if not sec_file.exists():
        return False
    
    content = sec_file.read_text(encoding="utf-8")
    checks = [
        ("sanitize_string", "Input sanitization"),
        ("mask_secret", "Secret masking"),
        ("is_safe_sql", "SQL injection protection"),
        ("validate_path", "Path traversal protection"),
    ]
    
    all_found = True
    for func, desc in checks:
        if func in content:
            print(f"✅ Security: {desc}")
        else:
            print(f"❌ Security: {desc} (missing)")
            all_found = False
    return all_found


def check_env_template(server_dir: Path) -> bool:
    """Check .env.example template."""
    print("\n🔍 Checking environment template...")
    env_file = server_dir / ".env.example"
    if not env_file.exists():
        return False
    
    content = env_file.read_text(encoding="utf-8")
    if "your-" in content and "-here" in content:
        print("✅ Environment template: Contains placeholders")
        return True
    else:
        print("❌ Environment template: Missing placeholders")
        return False


def main():
    parser = argparse.ArgumentParser(description="MCP Server Validator")
    parser.add_argument("--path", required=True, help="Path to generated server directory")
    args = parser.parse_args()

    server_dir = Path(args.path).resolve()
    if not server_dir.exists():
        print(f"❌ Server directory not found: {server_dir}")
        sys.exit(1)

    print(f"🚀 Validating MCP server at: {server_dir}")
    print("=" * 60)

    checks = [
        check_core_files(server_dir),
        check_ide_configs(server_dir),
        check_skill_file(server_dir),
        check_test_file(server_dir),
        check_requirements(server_dir),
        check_security(server_dir),
        check_env_template(server_dir),
    ]

    print("=" * 60)
    if all(checks):
        print("🎉 All checks passed! Server is ready for use.")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
