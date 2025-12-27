#!/usr/bin/env python3
"""
Simple Test Framework Verification Script

This script tests the performance testing framework components
without Unicode characters that might cause encoding issues.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def test_ground_truth_loading():
    """Test that ground truth data loads correctly."""
    print("Testing ground truth loading...")

    ground_truth_path = Path(__file__).parent / "ground_truth.json"

    if not ground_truth_path.exists():
        print("FAIL: Ground truth file not found")
        return False

    try:
        with open(ground_truth_path) as f:
            data = json.load(f)

        required_keys = [
            "description",
            "version",
            "test_files",
            "test_scenarios",
            "performance_expectations",
        ]
        for key in required_keys:
            if key not in data:
                print(f"FAIL: Missing required key: {key}")
                return False

        if not data["test_files"]:
            print("FAIL: No test files defined")
            return False

        print(
            f"PASS: Ground truth loaded successfully ({len(data['test_files'])} test files)"
        )
        return True

    except Exception as e:
        print(f"FAIL: Error loading ground truth: {e}")
        return False


def test_config_loading():
    """Test that configuration loads correctly."""
    print("Testing configuration loading...")

    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
        print("FAIL: Config file not found")
        return False

    try:
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        required_keys = [
            "test_files_dir",
            "cache_dir",
            "output_dir",
            "iterations",
            "whisper_models",
        ]
        for key in required_keys:
            if key not in config:
                print(f"FAIL: Missing required config key: {key}")
                return False

        print("PASS: Configuration loaded successfully")
        return True

    except ImportError:
        print("FAIL: PyYAML not available (pip install pyyaml)")
        return False
    except Exception as e:
        print(f"FAIL: Error loading config: {e}")
        return False


def test_input_files():
    """Test that input files are accessible."""
    print("Testing input files...")

    inputs_dir = Path(__file__).parent / "inputs"

    if not inputs_dir.exists():
        print(f"FAIL: Inputs directory not found: {inputs_dir}")
        return False

    mkv_files = list(inputs_dir.glob("*.mkv"))

    if not mkv_files:
        print("FAIL: No MKV files found in inputs directory")
        return False

    # Check file sizes (should be non-zero)
    for mkv_file in mkv_files:
        if mkv_file.stat().st_size == 0:
            print(f"FAIL: Empty file: {mkv_file.name}")
            return False

    print(f"PASS: Found {len(mkv_files)} MKV test files")
    return True


def test_dependencies():
    """Test that required dependencies are available."""
    print("Testing dependencies...")

    required_packages = [
        ("rich", "Rich console library"),
        ("loguru", "Logging library"),
        ("psutil", "System monitoring"),
        ("yaml", "YAML configuration"),
    ]

    optional_packages = [
        ("pandas", "Data analysis"),
        ("numpy", "Numerical computing"),
        ("matplotlib", "Plotting"),
        ("seaborn", "Statistical visualization"),
        ("pynvml", "GPU monitoring"),
    ]

    all_good = True

    # Check required packages
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"PASS: {description} ({package})")
        except ImportError:
            print(f"FAIL: Missing required: {description} ({package})")
            all_good = False

    # Check optional packages
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"PASS: {description} ({package})")
        except ImportError:
            print(f"WARN: Optional missing: {description} ({package})")

    return all_good


def test_basic_imports():
    """Test that framework modules can be imported."""
    print("Testing framework imports...")

    framework_modules = ["resource_monitor", "profiler", "analysis"]

    all_good = True

    for module in framework_modules:
        try:
            # Try importing the module
            exec(f"from {module} import *")
            print(f"PASS: {module} module imports successfully")
        except ImportError as e:
            print(f"FAIL: Cannot import {module}: {e}")
            all_good = False
        except Exception as e:
            print(f"WARN: Import issue with {module}: {e}")
            # Don't fail for other exceptions as they might be expected

    return all_good


def run_simple_test():
    """Run basic framework test suite."""
    print("=" * 60)
    print("Performance Testing Framework Verification")
    print("Testing basic functionality...")
    print("=" * 60)

    tests = [
        ("Dependencies", test_dependencies),
        ("Ground Truth", test_ground_truth_loading),
        ("Configuration", test_config_loading),
        ("Input Files", test_input_files),
        ("Framework Imports", test_basic_imports),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n=== {test_name} ===")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"FAIL: {test_name} test failed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test_name:<20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("Framework basic functionality verified!")
    else:
        print(f"{total - passed} issues found. Check installation and dependencies.")

    return passed == total


if __name__ == "__main__":
    success = run_simple_test()
    sys.exit(0 if success else 1)
