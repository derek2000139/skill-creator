#!/usr/bin/env python3
"""
Skill Validation Tool — checks skill files against quality standards.

Usage:
    python validate_skill.py --skill-dir /path/to/skill/
    python validate_skill.py --skill-file /path/to/skill.md
"""

import argparse
import re
import sys
from pathlib import Path


__version__ = "1.0.0"


class ValidationResult:
    def __init__(self):
        self.passed = []
        self.warnings = []
        self.errors = []

    @property
    def ok(self):
        return len(self.errors) == 0

    def pass_(self, msg):
        self.passed.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def report(self) -> str:
        lines = []
        lines.append("=" * 55)
        lines.append("📋 SKILL VALIDATION REPORT")
        lines.append("=" * 55)

        if self.passed:
            lines.append(f"\n✅ Passed ({len(self.passed)}):")
            for p in self.passed:
                lines.append(f"   ✅ {p}")

        if self.warnings:
            lines.append(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"   ⚠️ {w}")

        if self.errors:
            lines.append(f"\n❌ Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"   ❌ {e}")

        lines.append("\n" + "-" * 55)
        total = len(self.passed) + len(self.warnings) + len(self.errors)
        score = len(self.passed) / total * 100 if total > 0 else 0
        status = "PASS ✅" if self.ok else "FAIL ❌"
        lines.append(f"  Score: {score:.0f}% ({len(self.passed)}/{total})")
        lines.append(f"  Status: {status}")
        lines.append("=" * 55)
        return "\n".join(lines)


def validate_skill_file(file_path: Path) -> ValidationResult:
    """Validate a single skill markdown file."""
    r = ValidationResult()

    if not file_path.exists():
        r.error(f"File not found: {file_path}")
        return r

    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    # ── Frontmatter checks ──
    if content.startswith("---"):
        fm_end = content.find("---", 3)
        if fm_end > 0:
            fm = content[3:fm_end].strip()
            r.pass_("Frontmatter block exists")

            if "name:" in fm:
                r.pass_("Frontmatter has 'name'")
                # Check kebab-case
                name_match = re.search(r"name:\s*(.+)", fm)
                if name_match:
                    name_val = name_match.group(1).strip()
                    if re.match(r"^[a-z][a-z0-9-]*$", name_val):
                        r.pass_(f"Name '{name_val}' is kebab-case")
                    else:
                        r.warn(f"Name '{name_val}' is not strict kebab-case")
            else:
                r.error("Frontmatter missing 'name'")

            if "description:" in fm or "description: >" in fm:
                r.pass_("Frontmatter has 'description'")
                # Check description length
                desc_match = re.search(r"description:\s*>?\s*\n?\s*(.+)", fm)
                if desc_match:
                    desc = desc_match.group(1)
                    if len(desc) > 50:
                        r.pass_("Description is sufficiently detailed")
                    else:
                        r.warn("Description may be too short (< 50 chars)")
            else:
                r.error("Frontmatter missing 'description'")

            if "version:" in fm:
                r.pass_("Frontmatter has 'version'")
            else:
                r.warn("Frontmatter missing 'version' (recommended)")

            if "platform:" in fm:
                r.pass_("Frontmatter declares platform")
            else:
                r.warn("Frontmatter missing 'platform' (recommended)")

        else:
            r.error("Frontmatter block not properly closed")
    else:
        r.error("No frontmatter block (must start with ---")

    # ── Content structure checks ──
    content_lower = content.lower()

    # Required sections
    required_sections = {
        "overview": ["overview", "概述"],
        "setup/prerequisites": ["setup", "prerequisites", "配置", "安装"],
        "error handling": ["error handling", "error", "错误处理", "troubleshooting"],
        "examples": ["example", "示例", "用例"],
    }
    for section_name, keywords in required_sections.items():
        found = any(kw in content_lower for kw in keywords)
        if found:
            r.pass_(f"Has '{section_name}' section")
        else:
            r.error(f"Missing '{section_name}' section")

    # Recommended sections
    recommended_sections = {
        "decision tree/logic": ["decision", "决策", "workflow", "工作流"],
        "platform notes": ["platform", "windows", "平台"],
        "known pitfalls": ["pitfall", "陷阱", "注意事项"],
        "parameter reference": ["parameter", "参数", "reference"],
    }
    for section_name, keywords in recommended_sections.items():
        found = any(kw in content_lower for kw in keywords)
        if found:
            r.pass_(f"Has '{section_name}' section")
        else:
            r.warn(f"Missing '{section_name}' section (recommended)")

    # ── Anti-pattern checks ──

    # Hardcoded paths
    hardcoded_paths = re.findall(r"/mnt/[^\s]+", content)
    if hardcoded_paths:
        r.error(f"Hardcoded Linux paths found: {hardcoded_paths[:3]}")
    else:
        r.pass_("No hardcoded /mnt/ paths")

    # Complex CLI SQL
    inline_sql = re.findall(r"--sql\s+\"[^\"]{50,}\"", content)
    if inline_sql:
        r.warn(f"Found complex inline --sql arguments ({len(inline_sql)}). Consider --sql-file pattern.")
    else:
        r.pass_("No overly complex inline --sql arguments")

    # Chinese support indicators
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", content))
    if has_chinese:
        r.pass_("Contains Chinese content (CJK characters)")
    else:
        r.warn("No Chinese content — may need localization for Chinese users")

    # Negative instructions
    negative_patterns = ["do not", "don't", "never", "avoid", "不要", "禁止"]
    has_negative = any(p in content_lower for p in negative_patterns)
    if has_negative:
        r.pass_("Contains negative instructions (do NOT ...)")
    else:
        r.warn("No negative instructions — consider adding 'do NOT' guidance")

    # Error table
    has_error_table = bool(re.search(r"\|.*error.*\|.*\|", content_lower))
    if has_error_table:
        r.pass_("Has error handling table")
    else:
        r.warn("No error handling table found")

    return r


def validate_skill_dir(dir_path: Path) -> ValidationResult:
    """Validate a skill directory."""
    r = ValidationResult()

    if not dir_path.exists():
        r.error(f"Directory not found: {dir_path}")
        return r

    # Find skill markdown file
    md_files = list(dir_path.glob("*.md"))
    if not md_files:
        r.error("No .md skill file found in directory")
        return r

    r.pass_(f"Found {len(md_files)} markdown file(s)")

    # Validate main skill file
    main_md = md_files[0]
    file_result = validate_skill_file(main_md)
    r.passed.extend(file_result.passed)
    r.warnings.extend(file_result.warnings)
    r.errors.extend(file_result.errors)

    # Check for scripts directory (Type A)
    scripts_dir = dir_path / "scripts"
    if scripts_dir.exists():
        r.pass_("Has scripts/ directory (Type A skill)")

        # Check for main script
        py_files = list(scripts_dir.glob("*.py"))
        if py_files:
            r.pass_(f"Found {len(py_files)} Python script(s)")
        else:
            r.error("scripts/ directory exists but no .py files found")

        # Check for requirements.txt
        req = scripts_dir / "requirements.txt"
        if req.exists():
            r.pass_("Has requirements.txt")
        else:
            r.warn("Missing scripts/requirements.txt")

        # Check for setup_env.py
        setup = scripts_dir / "setup_env.py"
        if setup.exists():
            r.pass_("Has setup_env.py")
        else:
            r.warn("Missing scripts/setup_env.py")

        # Check main script for required patterns
        for py_file in py_files:
            if py_file.name.startswith("setup"):
                continue
            content = py_file.read_text(encoding="utf-8", errors="replace")

            if "check-env" in content or "check_env" in content:
                r.pass_(f"{py_file.name}: has check-env action")
            else:
                r.warn(f"{py_file.name}: missing check-env action")

            if "locate" in content:
                r.pass_(f"{py_file.name}: has locate action")
            else:
                r.warn(f"{py_file.name}: missing locate action")

            if "stderr" in content:
                r.pass_(f"{py_file.name}: uses stderr for diagnostics")
            else:
                r.warn(f"{py_file.name}: should use stderr for diagnostics")

            if "Suggestion" in content or "suggestion" in content:
                r.pass_(f"{py_file.name}: errors include suggestions")
            else:
                r.warn(f"{py_file.name}: errors should include recovery suggestions")

    return r


def main():
    parser = argparse.ArgumentParser(
        description=f"Skill Validation Tool v{__version__}"
    )
    parser.add_argument("--skill-dir", help="Path to skill directory")
    parser.add_argument("--skill-file", help="Path to skill .md file")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    if not args.skill_dir and not args.skill_file:
        parser.error("Provide --skill-dir or --skill-file")

    if args.skill_dir:
        result = validate_skill_dir(Path(args.skill_dir))
    else:
        result = validate_skill_file(Path(args.skill_file))

    print(result.report())
    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
