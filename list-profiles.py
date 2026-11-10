#!/usr/bin/env python3
"""List Arc or Dia profiles."""

import argparse
import json
import sys
from pathlib import Path

BROWSERS = {
    "Arc": Path.home() / "Library/Application Support/Arc/User Data",
    "Dia": Path.home() / "Library/Application Support/Dia/User Data",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--browser", choices=BROWSERS, default="Arc", help="Browser to list (default: Arc)"
    )
    args = parser.parse_args()

    local_state = BROWSERS[args.browser] / "Local State"
    profiles = json.loads(local_state.read_text()).get("profile", {}).get("info_cache", {})
    if not profiles:
        raise SystemExit(f"No profiles found in {local_state}")

    width = max(len("DIRECTORY"), *(len(directory) for directory in profiles))
    print(f"{'DIRECTORY':<{width}}  NAME")
    for directory, details in profiles.items():
        print(f"{directory:<{width}}  {details.get('name', '')}")
    print(f"\n{len(profiles)} profile(s)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"List failed: {error}")
