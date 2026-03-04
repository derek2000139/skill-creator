#!/usr/bin/env python3
"""Environment setup helper. Checks and installs dependencies."""
import subprocess, sys
from pathlib import Path

REQUIRED = {
    "python-docx": {"pip": "python-docx", "desc": "For reading Word documents"},
    "openpyxl": {"pip": "openpyxl", "desc": "For reading Excel files"},
    "python-pptx": {"pip": "python-pptx", "desc": "For reading PowerPoint files"},
    "PyPDF2": {"pip": "PyPDF2", "desc": "For reading PDF files"},
    "pandas": {"pip": "pandas", "desc": "For data analysis"}
}
MIN_PY = (3, 9)

def check_pkg(name):
    try:
        mod = __import__(name)
        return True, str(getattr(mod, "__version__", "?"))
    except ImportError:
        return False, None

def install(spec):
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "install", spec, "--quiet"],
                          capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except Exception:
        return False

def main():
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} @ {sys.executable}")
    if sys.version_info < MIN_PY:
        print(f"❌ Need Python {MIN_PY[0]}.{MIN_PY[1]}+")
        sys.exit(1)

    missing = []
    for pkg, info in REQUIRED.items():
        ok, ver = check_pkg(pkg)
        print(f"  {'✅' if ok else '❌'} {pkg}: {ver or 'MISSING'}")
        if not ok:
            missing.append(info["pip"])

    if missing and "--check-only" not in sys.argv:
        print("\nInstalling missing packages...")
        for spec in missing:
            print(f"  Installing {spec}...")
            if not install(spec):
                print(f"  ❌ Failed. Run manually: pip install {spec}")
                sys.exit(1)
        print("✅ All installed!")
    elif missing:
        print(f"\n❌ Missing: pip install {' '.join(missing)}")
        sys.exit(1)
    else:
        print("\n✅ Ready!")

if __name__ == "__main__":
    main()
