from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.live.xrpl_live_soak import run_soak_fixture


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline XRPL live-shadow soak readiness runner")
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    print(json.dumps(run_soak_fixture(Path(args.fixture)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
