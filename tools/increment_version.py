#!/usr/bin/env python3
"""Increment the patch version for a game."""

import argparse
import json
import pathlib
import sys


class Version:
    """Semantic version (major.minor.patch)."""

    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def parse(cls, s: str) -> "Version":
        print(s)
        parts = s.strip().split(".")
        print(parts)
        if len(parts) != 3:
            raise ValueError(f"Invalid version: {s}")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def increment(self) -> "Version":
        """Return new version with patch incremented."""
        return Version(self.major, self.minor, self.patch + 1)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def find_repo_root() -> pathlib.Path:
    """Find repository root by looking for .git directory."""
    return pathlib.Path(__file__).parent.parent


def increment_version(game: str) -> tuple[str, str]:
    """Increment patch version for a game."""
    repo_root = find_repo_root()
    version_file = repo_root / "maxbloks" / game / "version.json"

    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")

    with open(version_file) as f:
        data = json.load(f)

    old_version = Version.parse(data["version"])
    new_version = old_version.increment()

    data["version"] = str(new_version)
    with open(version_file, "w") as f:
        json.dump(data, f, indent=2)
        print(f"Wrote {version_file}")

    return old_version, new_version


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Increment patch version for a game")
    parser.add_argument("game", help="Game name (e.g., fish, terminal)")
    args = parser.parse_args()

    old, new = increment_version(args.game)
    print(f"Incremented {args.game} version: {old} -> {new}")


if __name__ == "__main__":
    sys.exit(main())
