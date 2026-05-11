#!/usr/bin/env python3
"""
Test Detection Script
Alerts if test_*.py files are not included in Bazel BUILD files.
"""

import pathlib
import re
from dataclasses import dataclass
from typing import List, Set, Dict


class Paths:
    """Defines all paths used in the test detection process."""
    
    def __init__(self, repo_root: pathlib.Path):
        self._repo_root = repo_root
    
    @property
    def repo_root(self) -> pathlib.Path:
        """Root directory of the repository."""
        return self._repo_root
    
    @property
    def tests_dir(self) -> pathlib.Path:
        """Main tests directory."""
        return self._repo_root / "tests"
    
    @property
    def unit_tests_dir(self) -> pathlib.Path:
        """Unit tests directory."""
        return self.tests_dir / "unit"
    
    @property
    def integration_tests_dir(self) -> pathlib.Path:
        """Integration tests directory."""
        return self.tests_dir / "integration"
    
    @property
    def unit_build_file(self) -> pathlib.Path:
        """Unit tests BUILD file."""
        return self.unit_tests_dir / "BUILD"
    
    @property
    def integration_build_file(self) -> pathlib.Path:
        """Integration tests BUILD file."""
        return self.integration_tests_dir / "BUILD"
    
    @property
    def tests_build_file(self) -> pathlib.Path:
        """Main tests BUILD file."""
        return self.tests_dir / "BUILD"


@dataclass
class TestFileInfo:
    """Information about a test file."""
    path: pathlib.Path
    name: str
    directory: str  # 'unit' or 'integration'
    
    @property
    def relative_path(self) -> pathlib.Path:
        """Path relative to tests directory."""
        return self.path.relative_to(self.path.parent.parent)


class BuildFileParser:
    """Parses Bazel BUILD files to extract test targets."""
    
    def __init__(self, paths: Paths):
        self._paths = paths
        self._name_pattern = re.compile(r'name\s*=\s*"([^"]+)"')
    
    def parse_build_file(self, build_file: pathlib.Path) -> Set[str]:
        """Parse a BUILD file and return set of test target names."""
        test_names = set()
        
        try:
            content = build_file.read_text()
            for match in self._name_pattern.finditer(content):
                test_names.add(match.group(1))
        except FileNotFoundError:
            print(f"Warning: BUILD file not found: {build_file}")
        except Exception as e:
            print(f"Error reading {build_file}: {e}")
        
        return test_names
    
    def get_all_test_names(self) -> Dict[str, Set[str]]:
        """Get all test names from all BUILD files.
        
        Returns:
            Dict mapping directory names to sets of test names.
        """
        results = {}
        
        # Parse unit tests BUILD file
        results['unit'] = self.parse_build_file(self._paths.unit_build_file)
        
        # Parse integration tests BUILD file
        results['integration'] = self.parse_build_file(self._paths.integration_build_file)
        
        return results


class TestCollector:
    """Collects all test_*.py files from the repository."""
    
    def __init__(self, paths: Paths):
        self._paths = paths
    
    def collect_test_files(self) -> List[TestFileInfo]:
        """Collect all test files from unit and integration directories.
        
        Returns:
            List of TestFileInfo objects.
        """
        test_files = []
        
        # Collect from unit tests
        test_files.extend(self._collect_from_directory(
            self._paths.unit_tests_dir,
            'unit'
        ))
        
        # Collect from integration tests
        test_files.extend(self._collect_from_directory(
            self._paths.integration_tests_dir,
            'integration'
        ))
        
        return test_files
    
    def _collect_from_directory(self, directory: pathlib.Path, 
                                dir_name: str) -> List[TestFileInfo]:
        """Collect test files from a specific directory."""
        test_files = []
        
        if not directory.exists():
            print(f"Warning: Directory not found: {directory}")
            return test_files
        
        for test_file in sorted(directory.glob("test_*.py")):
            test_files.append(TestFileInfo(
                path=test_file,
                name=test_file.stem,  # filename without extension
                directory=dir_name
            ))
        
        return test_files


class TestComparator:
    """Compares test files with BUILD file entries."""
    
    def __init__(self, test_files: List[TestFileInfo], 
                 build_test_names: Dict[str, Set[str]]):
        self._test_files = test_files
        self._build_test_names = build_test_names
    
    def find_missing_tests(self) -> List[TestFileInfo]:
        """Find test files that are not in BUILD files.
        
        Returns:
            List of TestFileInfo objects for missing tests.
        """
        missing_tests = []
        
        for test_file in self._test_files:
            directory = test_file.directory
            if directory in self._build_test_names:
                if test_file.name not in self._build_test_names[directory]:
                    missing_tests.append(test_file)
            else:
                # No BUILD file entries for this directory
                missing_tests.append(test_file)
        
        return missing_tests
    
    def generate_report(self, missing_tests: List[TestFileInfo]) -> str:
        """Generate a report of missing tests.
        
        Args:
            missing_tests: List of missing test files.
        
        Returns:
            Formatted report string.
        """
        if not missing_tests:
            return
        
        report_lines = [
            "The following test files are NOT in BUILD files:",
            ""
        ]
        
        # Group by directory
        unit_missing = [t for t in missing_tests if t.directory == 'unit']
        integration_missing = [t for t in missing_tests if t.directory == 'integration']
        
        if unit_missing:
            report_lines.append("Unit Tests:")
            for test in sorted(unit_missing, key=lambda x: x.name):
                report_lines.append(f"  - {test.name}")
            report_lines.append("")
        
        if integration_missing:
            report_lines.append("Integration Tests:")
            for test in sorted(integration_missing, key=lambda x: x.name):
                report_lines.append(f"  - {test.name}")
            report_lines.append("")
        
        report_lines.append(f"Total missing: {len(missing_tests)} test(s)")
        
        return "\n".join(report_lines)


def main():
    repo_root = pathlib.Path(__file__).parent.parent
    
    # Initialize paths
    paths = Paths(repo_root)
    
    # Collect all test files
    collector = TestCollector(paths)
    test_files = collector.collect_test_files()
    
    if not test_files:
        print("No test files found.")
        return 0
    
    # Parse BUILD files
    parser = BuildFileParser(paths)
    build_test_names = parser.get_all_test_names()
    
    # Compare and find missing tests
    comparator = TestComparator(test_files, build_test_names)
    missing_tests = comparator.find_missing_tests()
    
    # Generate and print report
    report = comparator.generate_report(missing_tests)

    print(report)
    
    # Return non-zero exit code if tests are missing
    return 1 if missing_tests else 0


if __name__ == "__main__":
    exit(main())
