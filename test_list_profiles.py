import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("list-profiles.py")


def write_local_state(home: Path, browser: str, profiles: dict) -> None:
    local_state = home / "Library" / "Application Support" / browser / "User Data" / "Local State"
    local_state.parent.mkdir(parents=True)
    local_state.write_text(json.dumps({"profile": {"info_cache": profiles}}))


class ListProfilesCommandTests(unittest.TestCase):
    def test_lists_profiles_from_the_selected_browser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            write_local_state(
                home,
                "Arc",
                {
                    "Default": {"name": "Personal"},
                    "Profile 1": {"name": "Work"},
                },
            )
            write_local_state(
                home,
                "Dia",
                {
                    "Default": {"name": "Dia Personal"},
                    "Profile 3": {"name": "Xero"},
                },
            )

            cases = [
                ([], [("Default", "Personal"), ("Profile 1", "Work")]),
                (
                    ["--browser", "Dia"],
                    [("Default", "Dia Personal"), ("Profile 3", "Xero")],
                ),
            ]
            for options, expected_profiles in cases:
                with self.subTest(options=options):
                    environment = os.environ.copy()
                    environment["HOME"] = str(home)
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), *options],
                        capture_output=True,
                        check=False,
                        env=environment,
                        text=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    lines = result.stdout.splitlines()
                    self.assertEqual(lines[0].split(), ["DIRECTORY", "NAME"])
                    rows = [
                        tuple(column.strip() for column in line.split("  ", maxsplit=1))
                        for line in lines[1:-2]
                    ]
                    self.assertEqual(rows, expected_profiles)
                    self.assertEqual(lines[-1], f"{len(expected_profiles)} profile(s)")


if __name__ == "__main__":
    unittest.main()
