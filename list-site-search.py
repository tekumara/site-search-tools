#!/usr/bin/env python3
"""List all site-search entries in an Arc/Chromium profile."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

USER_DATA = Path.home() / "Library/Application Support/Arc/User Data"


def profile_database(profile: str) -> Path:
    path = Path(profile).expanduser()
    if path.is_file():
        return path
    if path.is_dir():
        return path / "Web Data"

    directory = {"personal": "Default", "default": "Default"}.get(profile.lower(), profile)
    database = USER_DATA / directory / "Web Data"
    if database.exists():
        return database

    local_state = USER_DATA / "Local State"
    if local_state.exists():
        profiles = json.loads(local_state.read_text()).get("profile", {}).get("info_cache", {})
        for directory, details in profiles.items():
            if details.get("name", "").lower() == profile.lower():
                return USER_DATA / directory / "Web Data"

    raise SystemExit(f"Arc profile not found: {profile}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", help="Profile name, directory, or Web Data path")
    args = parser.parse_args()

    database = profile_database(args.profile)
    if not database.exists():
        raise SystemExit(f"Web Data database not found: {database}")

    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        rows = connection.execute(
            "SELECT id, keyword, short_name, url FROM keywords ORDER BY id"
        ).fetchall()

    width = max([len("KEYWORD"), *(len(row[1]) for row in rows)])
    print(f"{'ID':>4}  {'KEYWORD':<{width}}  NAME — URL")
    for engine_id, keyword, name, url in rows:
        print(f"{engine_id:>4}  {keyword:<{width}}  {name} — {url}")
    print(f"\n{len(rows)} site-search entries")


if __name__ == "__main__":
    try:
        main()
    except (OSError, sqlite3.Error, ValueError, KeyError) as error:
        sys.exit(f"List failed: {error}")
