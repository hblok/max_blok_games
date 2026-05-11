#!/usr/bin/env python3
"""Script to identify source modules without unit tests."""

from pathlib import Path

WHITELIST = [
    "main",
    "compat_sdl",
    "version",
]

EXCLUDED_GAMES = [
    "template",
]


def get_source_modules():
    """Get all Python source modules from maxbloks directory."""
    repo_root = Path(__file__).parent.parent
    source_dir = repo_root / "maxbloks"
    modules = []

    for py_file in source_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        rel_path = py_file.relative_to(source_dir)

        if "tests" in rel_path.parts:
            continue
        if rel_path.parts[0] in EXCLUDED_GAMES:
            continue
        if py_file.stem in WHITELIST:
            continue

        module_name = str(rel_path.with_suffix("")).replace("/", ".")
        modules.append(module_name)

    return sorted(modules)


def get_test_coverage():
    """Return set of (game, stem_without_test_prefix) pairs for existing tests."""
    repo_root = Path(__file__).parent.parent
    source_dir = repo_root / "maxbloks"
    covered = set()

    for py_file in source_dir.rglob("test_*.py"):
        rel_parts = py_file.relative_to(source_dir).parts
        # Only collect from <game>/tests/ directories
        if len(rel_parts) >= 3 and rel_parts[1] == "tests":
            game = rel_parts[0]
            covered.add((game, py_file.stem[5:]))  # strip "test_" prefix

    return covered


def test_name_candidates(dotted_module):
    """Return possible test name stems for a dotted module path.

    For 'tankbattle.network.connection_monitor' returns:
        ['connection_monitor', 'network_connection_monitor']
    """
    parts = dotted_module.split(".")
    subpath = parts[1:]  # skip game name
    return ["_".join(subpath[i:]) for i in range(len(subpath))]


def find_missing_tests():
    """Find source modules that don't have corresponding tests."""
    source_modules = get_source_modules()
    test_coverage = get_test_coverage()
    missing = []

    for module in source_modules:
        game = module.split(".")[0]
        if not any((game, c) in test_coverage for c in test_name_candidates(module)):
            missing.append(module)

    return sorted(missing)


def main():
    missing_modules = find_missing_tests()

    if missing_modules:
        print(f"Found {len(missing_modules)} source modules without tests:")
        for module in missing_modules:
            print(f"  - {module}")


if __name__ == "__main__":
    main()
