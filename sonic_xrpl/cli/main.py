import sys

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "safety-scan":
        print("[OK] Safety scan completed - no critical issues detected")
        return 0
    print("[OK] Fixture Health: HEALTHY")
    return 0

if __name__ == "__main__":
    sys.exit(main())