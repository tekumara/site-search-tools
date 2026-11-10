#!/usr/bin/env python3
"""Import exported site-search entries into an Arc or Dia profile."""

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BROWSERS = {
    "Arc": {
        "user_data": Path.home() / "Library/Application Support/Arc/User Data",
        "process": "Arc",
    },
    "Dia": {
        "user_data": Path.home() / "Library/Application Support/Dia/User Data",
        "process": "Dia",
    },
}


def profile_database(profile: str, browser: str = "Arc") -> Path:
    path = Path(profile).expanduser()
    if path.is_file():
        return path
    if path.is_dir():
        return path / "Web Data"

    user_data = BROWSERS[browser]["user_data"]
    aliases = {"personal": "Default", "default": "Default"}
    directory = aliases.get(profile.lower(), profile)
    database = user_data / directory / "Web Data"
    if database.exists():
        return database

    local_state = user_data / "Local State"
    if local_state.exists():
        profiles = json.loads(local_state.read_text()).get("profile", {}).get("info_cache", {})
        for directory, details in profiles.items():
            if details.get("name", "").lower() == profile.lower():
                return user_data / directory / "Web Data"

    raise SystemExit(f"{browser} profile not found: {profile}")


def decode(value):
    if isinstance(value, dict) and value.get("__type__") == "bytes":
        return bytes.fromhex(value["hex"])
    return value


def browser_is_running(browser: str) -> bool:
    return subprocess.run(
        ["pgrep", "-x", BROWSERS[browser]["process"]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", help="Profile name, directory, or Web Data path")
    parser.add_argument("exports", nargs="+", type=Path, help="Exported JSON file(s)")
    parser.add_argument(
        "--browser",
        choices=BROWSERS,
        default="Arc",
        help="Browser to import into (default: Arc)",
    )
    parser.add_argument("--replace", action="store_true", help="Replace entries with matching keywords")
    parser.add_argument("--dry-run", action="store_true", help="Validate and show changes only")
    args = parser.parse_args()

    database = profile_database(args.profile, args.browser)
    if not database.exists():
        raise SystemExit(f"Web Data database not found: {database}")

    engines = []
    for export in args.exports:
        data = json.loads(export.read_text())
        entries = data.get("site_search")
        if data.get("table") != "keywords" or not isinstance(entries, list):
            raise SystemExit(f"Not a site-search export: {export}")
        engines.extend(entries)
    if not engines:
        raise SystemExit("No site-search entries found in the export files.")

    with sqlite3.connect(database) as connection:
        target_columns = {row[1] for row in connection.execute("PRAGMA table_info(keywords)")}
        existing = {
            keyword for (keyword,) in connection.execute(
                "SELECT keyword FROM keywords WHERE keyword IN (%s)"
                % ",".join("?" * len(engines)),
                [engine["keyword"] for engine in engines],
            )
        }

    changes = []
    for engine in engines:
        exists = engine["keyword"] in existing
        if exists and not args.replace:
            print(f"Skip {engine['keyword']}: {engine['short_name']}")
        else:
            changes.append(("Replace" if exists else "Add", engine))
    if args.dry_run:
        for action, engine in changes:
            print(f"Would {action.lower()} {engine['keyword']}: {engine['short_name']}")
        return
    if not changes:
        print("Nothing to import.")
        return
    if browser_is_running(args.browser):
        raise SystemExit(f"{args.browser} is running. Quit {args.browser} before importing.")

    backup = database.with_name(f"Web Data.backup-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(database, backup)

    with sqlite3.connect(database) as connection:
        for action, engine in changes:
            if action == "Replace":
                connection.execute("DELETE FROM keywords WHERE keyword = ?", (engine["keyword"],))
            values = {
                key: decode(value)
                for key, value in engine.items()
                if key != "id" and key in target_columns
            }
            columns = list(values)
            connection.execute(
                f"INSERT INTO keywords ({','.join(columns)}) VALUES ({','.join('?' * len(columns))})",
                [values[column] for column in columns],
            )

    for action, engine in changes:
        past_tense = "Replaced" if action == "Replace" else "Added"
        print(f"{past_tense} {engine['keyword']}: {engine['short_name']}")
    print(f"Imported {len(changes)} site-search entries into {database}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, sqlite3.Error, ValueError, KeyError) as error:
        sys.exit(f"Import failed: {error}")
