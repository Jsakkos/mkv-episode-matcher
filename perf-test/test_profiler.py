#!/usr/bin/env python3
"""
Test the profiler module specifically to verify it works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from profiler import ComprehensiveProfiler


def test_function_simple():
    """Simple test function for profiling."""
    return sum(i**2 for i in range(1000))


def test_function_complex():
    """More complex test function for profiling."""
    import time

    time.sleep(0.1)
    data = []
    for i in range(100):
        data.append(i**2)
    return sum(data)


def test_profiler():
    """Test the profiler functionality."""
    print("Testing ComprehensiveProfiler...")

    try:
        # Test context manager usage
        with ComprehensiveProfiler() as profiler:
            result1 = test_function_simple()
            result2 = test_function_complex()

        # Get results
        results = profiler.results

        # Check that we got results
        if not results:
            print("FAIL: No profiling results returned")
            return False

        required_keys = ["total_wall_time", "execution_profile", "memory_profile"]
        for key in required_keys:
            if key not in results:
                print(f"FAIL: Missing key in results: {key}")
                return False

        # Check execution profile
        exec_profile = results["execution_profile"]
        if "top_functions" in exec_profile:
            top_functions = exec_profile["top_functions"]
            print(f"  Found {len(top_functions)} profiled functions")

            if top_functions:
                print("  Top function by cumulative time:")
                print(
                    f"    {top_functions[0]['function_name']}: {top_functions[0]['cumulative_time']:.6f}s"
                )

        # Check memory profile
        mem_profile = results["memory_profile"]
        if "peak_memory_mb" in mem_profile:
            print(f"  Peak memory usage: {mem_profile['peak_memory_mb']:.2f} MB")

        print(f"  Total execution time: {results['total_wall_time']:.6f}s")

        print("PASS: ComprehensiveProfiler working correctly")
        return True

    except Exception as e:
        print(f"FAIL: Profiler test error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_profiler()
    sys.exit(0 if success else 1)
