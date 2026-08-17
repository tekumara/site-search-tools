# Site search tools

Export, import and inspect Arc site-search shortcuts on macOS.

The scripts read and write Chromium's `keywords` table in each Arc profile's `Web Data` SQLite database. They use only the Python standard library.

## Requirements

- macOS
- Arc
- Python 3

Run each command from this directory, or include the path to the script.

## List profiles

```bash
./list-profiles.py
```

Use either the profile name or directory in the other commands. For example, `Personal`, `Work`, `Default` or `Profile 1`.

You can also pass a profile directory or the full path to its `Web Data` file.

## List site-search entries

```bash
./list-site-search.py PROFILE
```

For example:

```bash
./list-site-search.py Work
```

This prints each entry's ID, keyword, name and URL.

## Export site-search entries

```bash
./export-site-search.py PROFILE OUTPUT KEYWORD [KEYWORD ...]
```

For example:

```bash
./export-site-search.py Work work-search.json gh co gl mag
```

The command writes complete rows from the `keywords` table to JSON. It stops without creating the output if any keyword does not exist.

## Import site-search entries

Preview an import first:

```bash
./import-site-search.py PROFILE EXPORT [EXPORT ...] --dry-run
```

Import one or more files:

```bash
./import-site-search.py Personal work-search.json personal-search.json
```

The importer:

- skips entries whose keywords already exist
- adds entries whose keywords do not exist
- accepts more than one export file
- creates a timestamped backup of `Web Data` before writing
- applies all database changes in one transaction

Use `--replace` to replace entries whose keywords already exist:

```bash
./import-site-search.py Personal work-search.json --replace
```

Quit Arc before running an import that would change the database. Dry runs and imports where every entry is skipped do not require Arc to be closed.

## Export format

The export and import scripts use the same JSON format:

```json
{
  "source_profile": "Work",
  "source_database": "/Users/example/Library/Application Support/Arc/User Data/Profile 1/Web Data",
  "table": "keywords",
  "columns": ["id", "short_name", "keyword", "url"],
  "site_search": [
    {
      "id": 17,
      "short_name": "GitHub",
      "keyword": "gh",
      "url": "https://github.com/search?q={searchTerms}"
    }
  ]
}
```

The actual export includes every column in the source `keywords` table. The importer ignores the exported `id` so SQLite can assign an ID in the destination profile.
