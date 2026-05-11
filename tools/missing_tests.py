#!/usr/bin/env python3
"""Script to identify source modules without unit tests."""

import os
import json
from pathlib import Path

WHITE_LIST = [
    "main",
    "version",
]

def get_source_modules():
    """Get all Python source modules from directory."""
    repo_root = Path(__file__).parent.parent
    source_dir = repo_root / "maxbloks"
    modules = []
    
    for py_file in source_dir.rglob("*.py"):
        # Skip __init__.py files
        if py_file.name == "__init__.py":
            continue
        
        # Get relative path from
        rel_path = py_file.relative_to(source_dir)
        # Convert to module notation (e.g., core/application.py -> core.application)
        module_name = str(rel_path.with_suffix('')).replace('/', '.')
        modules.append(module_name)
    
    return sorted(modules)

def get_test_modules():
    """Get all unit test modules from tests/unit directory."""
    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / "tests/unit"
    modules = []
    
    for py_file in test_dir.rglob("test_*.py"):
        rel_path = py_file.relative_to(test_dir)
        # Convert test filename to potential source module name
        # test_config_loader.py -> config_loader or config.loader
        test_name = py_file.stem  # test_config_loader
        module_part = test_name.replace("test_", "")  # config_loader
        
        # Try different conventions: underscore and dot notation
        potential_modules = [
            module_part.replace('_', '.'),  # config.loader
            module_part  # config_loader
        ]
        
        modules.extend(potential_modules)
    
    return sorted(set(modules))

def normalize_module_name(module_name):
    """Normalize module name for comparison (handle underscores and dots)."""
    # Common patterns
    normalized = module_name.replace('_', '.')
    return normalized.lower()

def find_missing_tests():
    """Find source modules that don't have corresponding tests."""
    source_modules = get_source_modules()
    test_modules = get_test_modules()
    
    # Normalize for comparison
    normalized_test_modules = [normalize_module_name(m) for m in test_modules]
    
    missing = []
    
    for source_module in source_modules:
        normalized_source = normalize_module_name(source_module)
        
        # Check if there's a test module
        has_test = False
        for test_normalized in normalized_test_modules:
            # Check if test module name matches or contains the source module name
            if test_normalized == normalized_source or \
               test_normalized.endswith('.' + normalized_source) or \
               normalized_source.endswith('.' + test_normalized):
                has_test = True
                break
        
        if not has_test and source_module not in WHITE_LIST:
            missing.append(source_module)
    
    return sorted(missing)

def main():
    """Main function to identify and save missing tests."""
    missing_modules = find_missing_tests()
    
    # Create output directory if needed
    os.makedirs("tests", exist_ok=True)
    
    # Save to JSON file
    #output_file = "tests/missing.json"
    #with open(output_file, 'w') as f:
    #    json.dump({
    #        "missing_tests": missing_modules,
    #        "count": len(missing_modules),
    #        "total_source_modules": len(get_source_modules()),
    #        "tested_modules": len(get_source_modules()) - len(missing_modules)
    #    }, f, indent=2)

    if missing_modules:
        print(f"Found {len(missing_modules)} source modules without tests:")
        for module in missing_modules:
            print(f"  - {module}")
        
        #print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
