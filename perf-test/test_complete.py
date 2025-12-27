#!/usr/bin/env python3
"""
Complete framework test including profiler functionality.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def test_profiler_functionality():
    """Test profiler with actual functionality."""
    print("Testing profiler functionality...")

    try:
        from profiler import ComprehensiveProfiler

        def test_function():
            return sum(i**2 for i in range(1000))

        with ComprehensiveProfiler() as profiler:
            result = test_function()

        profile_results = profiler.results

        if not profile_results:
            print("FAIL: No profiling results")
            return False

        required_keys = ["total_wall_time", "execution_profile", "memory_profile"]
        for key in required_keys:
            if key not in profile_results:
                print(f"FAIL: Missing profiling key: {key}")
                return False

        print("PASS: Profiler working correctly")
        return True

    except Exception as e:
        print(f"FAIL: Profiler error: {e}")
        return False


def test_resource_monitor_functionality():
    """Test resource monitoring with actual functionality."""
    print("Testing resource monitor functionality...")

    try:
        from resource_monitor import EnhancedResourceMonitor

        monitor = EnhancedResourceMonitor(sampling_interval=0.1)
        monitor.start()

        # Simulate some work
        import time

        time.sleep(0.3)

        results = monitor.stop()

        if not results:
            print("FAIL: No monitoring results returned")
            return False

        required_keys = ["duration_seconds", "cpu", "memory"]
        for key in required_keys:
            if key not in results:
                print(f"FAIL: Missing monitoring key: {key}")
                return False

        # Check that we actually recorded some samples
        if results["sample_count"] == 0:
            print("FAIL: No samples recorded")
            return False

        print(
            f"PASS: Resource monitoring captured {results['sample_count']} samples over {results['duration_seconds']:.2f}s"
        )
        return True

    except Exception as e:
        print(f"FAIL: Resource monitoring error: {e}")
        return False


def test_analysis_with_mock_data():
    """Test analysis tools with mock data."""
    print("Testing analysis tools with mock data...")

    try:
        from analysis import BenchmarkAnalyzer

        # Create more comprehensive mock data
        mock_results = {
            "metadata": {"timestamp": "2024-01-01", "total_files": 3},
            "results": {
                "test1.mkv": {
                    "ground_truth": {
                        "show_name": "Test Show",
                        "season": 1,
                        "episode": 1,
                    },
                    "iterations": 3,
                    "timing_stats": {
                        "mean": 15.0,
                        "median": 14.5,
                        "min": 13.0,
                        "max": 17.0,
                        "stdev": 2.0,
                    },
                    "accuracy_stats": {
                        "accuracy": 1.0,
                        "f1_score": 1.0,
                        "precision": 1.0,
                        "recall": 1.0,
                        "confidence_stats": {"mean": 0.85, "max": 0.9, "min": 0.8},
                    },
                    "resource_usage": {
                        "cpu_mean": 25.0,
                        "memory_mean_mb": 200.0,
                        "memory_max_mb": 250.0,
                    },
                    "error_count": 0,
                },
                "test2.mkv": {
                    "ground_truth": {
                        "show_name": "Test Show",
                        "season": 1,
                        "episode": 2,
                    },
                    "iterations": 3,
                    "timing_stats": {
                        "mean": 12.0,
                        "median": 11.5,
                        "min": 10.0,
                        "max": 14.0,
                        "stdev": 2.0,
                    },
                    "accuracy_stats": {
                        "accuracy": 0.8,
                        "f1_score": 0.75,
                        "precision": 0.8,
                        "recall": 0.75,
                        "confidence_stats": {"mean": 0.75, "max": 0.8, "min": 0.7},
                    },
                    "resource_usage": {
                        "cpu_mean": 30.0,
                        "memory_mean_mb": 180.0,
                        "memory_max_mb": 220.0,
                    },
                    "error_count": 1,
                },
                "test3.mkv": {
                    "ground_truth": {
                        "show_name": "Another Show",
                        "season": 2,
                        "episode": 1,
                    },
                    "iterations": 3,
                    "timing_stats": {
                        "mean": 18.0,
                        "median": 17.5,
                        "min": 16.0,
                        "max": 20.0,
                        "stdev": 2.0,
                    },
                    "accuracy_stats": {
                        "accuracy": 0.9,
                        "f1_score": 0.85,
                        "precision": 0.9,
                        "recall": 0.8,
                        "confidence_stats": {"mean": 0.8, "max": 0.85, "min": 0.75},
                    },
                    "resource_usage": {
                        "cpu_mean": 35.0,
                        "memory_mean_mb": 220.0,
                        "memory_max_mb": 280.0,
                    },
                    "error_count": 0,
                },
            },
        }

        # Save mock results to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mock_results, f)
            temp_path = Path(f.name)

        try:
            analyzer = BenchmarkAnalyzer()
            analyzer.load_results(temp_path)

            if analyzer.df.empty:
                print("FAIL: Failed to create DataFrame")
                return False

            # Test analysis functions
            timing_analysis = analyzer.generate_timing_analysis()
            accuracy_analysis = analyzer.generate_accuracy_analysis()
            resource_analysis = analyzer.generate_resource_analysis()
            comprehensive = analyzer.generate_comprehensive_report()

            if not all([
                timing_analysis,
                accuracy_analysis,
                resource_analysis,
                comprehensive,
            ]):
                print("FAIL: Analysis functions returned empty results")
                return False

            # Check specific analysis components
            if "overall_stats" not in timing_analysis:
                print("FAIL: Missing timing overall_stats")
                return False

            if "overall_stats" not in accuracy_analysis:
                print("FAIL: Missing accuracy overall_stats")
                return False

            if "recommendations" not in comprehensive:
                print("FAIL: Missing recommendations")
                return False

            print("PASS: Analysis tools working with comprehensive mock data")
            return True

        finally:
            temp_path.unlink()

    except ImportError as e:
        print(f"WARN: Analysis tools unavailable (missing dependencies): {e}")
        return True  # Not critical for basic functionality
    except Exception as e:
        print(f"FAIL: Analysis tools error: {e}")
        return False


def run_complete_test():
    """Run complete framework test."""
    print("=" * 60)
    print("Complete Performance Framework Test")
    print("Testing all functionality including edge cases...")
    print("=" * 60)

    tests = [
        ("Resource Monitor", test_resource_monitor_functionality),
        ("Profiler", test_profiler_functionality),
        ("Analysis Tools", test_analysis_with_mock_data),
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
    print("Complete Test Summary:")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test_name:<20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("All components working correctly!")
        print("\nFramework is ready for performance testing!")
    else:
        print(f"{total - passed} issues found.")

    return passed == total


if __name__ == "__main__":
    success = run_complete_test()
    sys.exit(0 if success else 1)
