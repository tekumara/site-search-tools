#!/usr/bin/env python3
"""Export selected Arc/Chromium site-search entries to JSON."""

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


def encode(value):
    if isinstance(value, bytes):
        return {"__type__": "bytes", "hex": value.hex()}
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", help="Profile name, directory, or Web Data path")
    parser.add_argument("output", type=Path, help="Destination JSON file")
    parser.add_argument("keywords", nargs="+", help="Site-search keyword(s) to export")
    args = parser.parse_args()

    database = profile_database(args.profile)
    if not database.exists():
        raise SystemExit(f"Web Data database not found: {database}")

    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        columns = [row[1] for row in connection.execute("PRAGMA table_info(keywords)")]
        rows = connection.execute(
            "SELECT * FROM keywords WHERE keyword IN (%s) ORDER BY id"
            % ",".join("?" * len(args.keywords)),
            args.keywords,
        ).fetchall()

    found = {row["keyword"] for row in rows}
    missing = sorted(set(args.keywords) - found)
    if missing:
        raise SystemExit("Keywords not found: " + ", ".join(missing))

    payload = {
        "source_profile": args.profile,
        "source_database": str(database),
        "table": "keywords",
        "columns": columns,
        "site_search": [
            {column: encode(row[column]) for column in columns} for row in rows
        ],
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Exported {len(rows)} site-search entries to {args.output}")
    for row in rows:
        print(f"Exported {row['keyword']}: {row['short_name']}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, sqlite3.Error, ValueError, KeyError) as error:
        sys.exit(f"Export failed: {error}")
