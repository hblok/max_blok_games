#!/usr/bin/env python3
"""
Test Detection Script
Alerts if test_*.py files are not included in Bazel BUILD files.
"""

import pathlib
import re
from dataclasses import dataclass
from typing import List, Set, Dict


@dataclass
class TestFileInfo:
    """Information about a test file."""
    path: pathlib.Path
    name: str   # stem, e.g. "test_camera"
    game: str   # game name, e.g. "tanks"

    @property
    def relative_path(self) -> pathlib.Path:
        """Path relative to the maxbloks directory."""
        return self.path.relative_to(self.path.parent.parent.parent)


class BuildFileParser:
    """Parses Bazel BUILD files to extract test target names."""

    def __init__(self, repo_root: pathlib.Path):
        self._source_dir = repo_root / "maxbloks"
        self._name_pattern = re.compile(r'name\s*=\s*"([^"]+)"')

    def parse_build_file(self, build_file: pathlib.Path) -> Set[str]:
        """Parse a BUILD file and return set of target names."""
        names = set()
        try:
            content = build_file.read_text()
            for match in self._name_pattern.finditer(content):
                names.add(match.group(1))
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error reading {build_file}: {e}")
        return names

    def get_all_test_names(self) -> Dict[str, Set[str]]:
        """Return dict mapping game name to set of target names in its tests/BUILD."""
        results = {}
        for tests_dir in sorted(self._source_dir.glob("*/tests")):
            if tests_dir.is_dir():
                game = tests_dir.parent.name
                results[game] = self.parse_build_file(tests_dir / "BUILD")
        return results


class TestCollector:
    """Collects all test_*.py files from game test directories."""

    def __init__(self, repo_root: pathlib.Path):
        self._source_dir = repo_root / "maxbloks"

    def collect_test_files(self) -> List[TestFileInfo]:
        """Collect all test files from <game>/tests/ directories."""
        test_files = []
        for py_file in sorted(self._source_dir.rglob("test_*.py")):
            rel_parts = py_file.relative_to(self._source_dir).parts
            if len(rel_parts) >= 3 and rel_parts[1] == "tests":
                test_files.append(TestFileInfo(
                    path=py_file,
                    name=py_file.stem,
                    game=rel_parts[0],
                ))
        return test_files


class TestComparator:
    """Compares test files with BUILD file entries."""

    def __init__(self, test_files: List[TestFileInfo],
                 build_test_names: Dict[str, Set[str]]):
        self._test_files = test_files
        self._build_test_names = build_test_names

    def find_missing_tests(self) -> List[TestFileInfo]:
        """Find test files not listed in their game's BUILD file."""
        missing = []
        for test_file in self._test_files:
            game_names = self._build_test_names.get(test_file.game, set())
            if test_file.name not in game_names:
                missing.append(test_file)
        return missing

    def generate_report(self, missing_tests: List[TestFileInfo]) -> str:
        """Generate a report of missing tests."""
        if not missing_tests:
            return ""

        report_lines = [
            "The following test files are NOT in BUILD files:",
            "",
        ]

        by_game: Dict[str, List[TestFileInfo]] = {}
        for t in missing_tests:
            by_game.setdefault(t.game, []).append(t)

        for game in sorted(by_game):
            report_lines.append(f"{game}:")
            for test in sorted(by_game[game], key=lambda x: x.name):
                report_lines.append(f"  - {test.name}")
            report_lines.append("")

        report_lines.append(f"Total missing: {len(missing_tests)} test(s)")
        return "\n".join(report_lines)


def main():
    repo_root = pathlib.Path(__file__).parent.parent

    collector = TestCollector(repo_root)
    test_files = collector.collect_test_files()

    if not test_files:
        print("No test files found.")
        return 0

    parser = BuildFileParser(repo_root)
    build_test_names = parser.get_all_test_names()

    comparator = TestComparator(test_files, build_test_names)
    missing_tests = comparator.find_missing_tests()

    report = comparator.generate_report(missing_tests)
    if report:
        print(report)

    return 1 if missing_tests else 0


if __name__ == "__main__":
    exit(main())
