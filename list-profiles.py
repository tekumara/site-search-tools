#!/usr/bin/env python3
"""List Arc/Chromium profiles."""

import json
import sys
from pathlib import Path

LOCAL_STATE = Path.home() / "Library/Application Support/Arc/User Data/Local State"


def main() -> None:
    profiles = json.loads(LOCAL_STATE.read_text()).get("profile", {}).get("info_cache", {})
    if not profiles:
        raise SystemExit(f"No profiles found in {LOCAL_STATE}")

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
