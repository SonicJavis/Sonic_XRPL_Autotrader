import sys
import os

# Force UTF-8 encoding on Windows to prevent charmap errors
def setup_encoding():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

setup_encoding()

def main():
    """Minimal CLI for smoke tests."""
    import sys
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "health"):
        print("[OK] Fixture Health: HEALTHY")
        print("Mode: shadow")
        return 0
    elif args[0] == "safety-scan":
        print("[OK] Safety Scan: No secrets detected")
        return 0
    elif args[0] == "capabilities":
        print("Capabilities: AMM, XRPL, Paper Trading")
        return 0
    else:
        print("[OK] Command executed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
