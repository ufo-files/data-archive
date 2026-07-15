#!/usr/bin/env python3
"""Build the public live archive count from files tracked by Git."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath


TYPE_EXTENSIONS = {
    "documents": {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".rtf", ".txt", ".csv", ".tsv", ".html", ".htm", ".xml",
    },
    "images": {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".jp2",
        ".tif", ".tiff",
    },
    "videos": {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".wmv", ".webm"},
    "audio": {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"},
}
NON_SOURCE_ROOTS = {".github", "manifest", "scripts"}


def git_output(*arguments: str) -> bytes:
    return subprocess.check_output(["git", *arguments])


def classify(path: PurePosixPath) -> str | None:
    extension = path.suffix.lower()
    for kind, extensions in TYPE_EXTENSIONS.items():
        if extension in extensions:
            return kind
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("archive-count.json"))
    args = parser.parse_args()

    tracked = [
        PurePosixPath(raw.decode("utf-8", "surrogateescape"))
        for raw in git_output("ls-files", "-z").split(b"\0")
        if raw
    ]
    by_type: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    excluded_zip = 0
    excluded_non_archive = 0

    for path in tracked:
        if len(path.parts) < 2 or path.parts[0] in NON_SOURCE_ROOTS:
            excluded_non_archive += 1
            continue
        if path.suffix.lower() == ".zip":
            excluded_zip += 1
            continue
        kind = classify(path)
        if kind is None:
            excluded_non_archive += 1
            continue
        by_type[kind] += 1
        by_source[path.parts[0]] += 1

    total = sum(by_type.values())
    revision = os.getenv("GITHUB_SHA") or git_output("rev-parse", "HEAD").decode().strip()
    payload = {
        "schema_version": 1,
        "repository": "ufo-files/data-archive",
        "revision": revision,
        "generated_utc": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "count": total,
        "total_files": total,
        "by_type": {kind: by_type.get(kind, 0) for kind in TYPE_EXTENSIONS},
        "by_source": dict(sorted(by_source.items())),
        "excluded": {
            "zip_files": excluded_zip,
            "non_archive_files": excluded_non_archive,
        },
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Counted {total} archive file(s) across {len(by_source)} source(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
