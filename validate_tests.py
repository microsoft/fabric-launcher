"""
Test validation script - verifies tests can be imported and discovered.
Run this to check if the test suite is properly configured.
"""

import sys
import unittest
from pathlib import Path

def main():
    """Validate test suite configuration."""
    print("=" * 70)
    print("fabric-launcher Test Suite Validation")
    print("=" * 70)
    print()
    
    # Check if tests directory exists
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("❌ ERROR: tests/ directory not found")
        return 1
    print("✅ tests/ directory found")
    
    # Check for test files
    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        print("❌ ERROR: No test files (test_*.py) found")
        return 1
    
    print(f"✅ Found {len(test_files)} test file(s):")
    for test_file in sorted(test_files):
        print(f"   - {test_file.name}")
    print()
    
    # Try to discover tests
    print("Discovering tests...")
    loader = unittest.TestLoader()
    try:
        suite = loader.discover("tests", pattern="test_*.py")
        test_count = suite.countTestCases()
        if test_count == 0:
            print("⚠️  WARNING: No test cases discovered")
            return 1
        print(f"✅ Discovered {test_count} test case(s)")
        print()
    except Exception as e:
        print(f"❌ ERROR discovering tests: {e}")
        return 1
    
    # List all test cases
    print("Test Cases:")
    print("-" * 70)
    for test_group in suite:
        for test_case in test_group:
            if hasattr(test_case, '__iter__'):
                for test in test_case:
                    print(f"  {test.id()}")
            else:
                print(f"  {test_case.id()}")
    print()
    
    # Summary
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    print(f"✅ Test files: {len(test_files)}")
    print(f"✅ Test cases: {test_count}")
    print()
    print("The test suite is properly configured!")
    print()
    print("To run tests:")
    print("  python -m unittest discover tests -v")
    print("  OR")
    print("  pytest tests/ -v")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
