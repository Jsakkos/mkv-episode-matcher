#!/usr/bin/env python3
"""
Test Framework Verification Script

This script tests the performance testing framework components
without requiring the full episode matching pipeline.
"""

import json
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

console = Console()


def test_ground_truth_loading():
    """Test that ground truth data loads correctly."""
    console.print("[cyan]Testing ground truth loading...[/cyan]")

    ground_truth_path = Path(__file__).parent / "ground_truth.json"

    if not ground_truth_path.exists():
        console.print("[red]❌ Ground truth file not found[/red]")
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
                console.print(f"[red]❌ Missing required key: {key}[/red]")
                return False

        if not data["test_files"]:
            console.print("[red]❌ No test files defined[/red]")
            return False

        console.print(
            f"[green]✅ Ground truth loaded successfully ({len(data['test_files'])} test files)[/green]"
        )
        return True

    except Exception as e:
        console.print(f"[red]❌ Error loading ground truth: {e}[/red]")
        return False


def test_config_loading():
    """Test that configuration loads correctly."""
    console.print("[cyan]Testing configuration loading...[/cyan]")

    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
        console.print("[red]❌ Config file not found[/red]")
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
                console.print(f"[red]❌ Missing required config key: {key}[/red]")
                return False

        console.print("[green]✅ Configuration loaded successfully[/green]")
        return True

    except ImportError:
        console.print("[red]❌ PyYAML not available (pip install pyyaml)[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Error loading config: {e}[/red]")
        return False


def test_resource_monitor():
    """Test resource monitoring functionality."""
    console.print("[cyan]Testing resource monitoring...[/cyan]")

    try:
        from resource_monitor import EnhancedResourceMonitor

        monitor = EnhancedResourceMonitor(sampling_interval=0.1)
        monitor.start()

        # Simulate some work
        import time

        time.sleep(0.5)

        results = monitor.stop()

        if not results:
            console.print("[red]❌ No monitoring results returned[/red]")
            return False

        required_keys = ["duration_seconds", "cpu", "memory"]
        for key in required_keys:
            if key not in results:
                console.print(f"[red]❌ Missing monitoring key: {key}[/red]")
                return False

        console.print("[green]✅ Resource monitoring working[/green]")
        return True

    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Resource monitoring error: {e}[/red]")
        return False


def test_profiler():
    """Test profiling functionality."""
    console.print("[cyan]Testing profiler...[/cyan]")

    try:
        from profiler import ComprehensiveProfiler

        def test_function():
            return sum(i**2 for i in range(1000))

        with ComprehensiveProfiler() as profiler:
            result = test_function()

        profile_results = profiler.results

        if not profile_results:
            console.print("[red]❌ No profiling results[/red]")
            return False

        required_keys = ["total_wall_time", "execution_profile", "memory_profile"]
        for key in required_keys:
            if key not in profile_results:
                console.print(f"[red]❌ Missing profiling key: {key}[/red]")
                return False

        console.print("[green]✅ Profiler working[/green]")
        return True

    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Profiler error: {e}[/red]")
        return False


def test_analysis_tools():
    """Test analysis and visualization tools."""
    console.print("[cyan]Testing analysis tools...[/cyan]")

    try:
        from analysis import BenchmarkAnalyzer

        # Create mock results data
        mock_results = {
            "metadata": {"timestamp": "2024-01-01", "total_files": 2},
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
                    },
                    "accuracy_stats": {
                        "accuracy": 1.0,
                        "f1_score": 1.0,
                        "confidence_stats": {"mean": 0.85},
                    },
                    "resource_usage": {
                        "cpu_mean": 25.0,
                        "memory_mean_mb": 200.0,
                        "memory_max_mb": 250.0,
                    },
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
                    },
                    "accuracy_stats": {
                        "accuracy": 0.8,
                        "f1_score": 0.75,
                        "confidence_stats": {"mean": 0.75},
                    },
                    "resource_usage": {
                        "cpu_mean": 30.0,
                        "memory_mean_mb": 180.0,
                        "memory_max_mb": 220.0,
                    },
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
                console.print("[red]❌ Failed to create DataFrame[/red]")
                return False

            # Test analysis functions
            timing_analysis = analyzer.generate_timing_analysis()
            accuracy_analysis = analyzer.generate_accuracy_analysis()
            resource_analysis = analyzer.generate_resource_analysis()

            if not all([timing_analysis, accuracy_analysis, resource_analysis]):
                console.print("[red]❌ Analysis functions returned empty results[/red]")
                return False

            console.print("[green]✅ Analysis tools working[/green]")
            return True

        finally:
            temp_path.unlink()

    except ImportError as e:
        console.print(
            f"[yellow]⚠️ Analysis tools unavailable (missing dependencies): {e}[/yellow]"
        )
        return True  # Not critical for basic functionality
    except Exception as e:
        console.print(f"[red]❌ Analysis tools error: {e}[/red]")
        return False


def test_input_files():
    """Test that input files are accessible."""
    console.print("[cyan]Testing input files...[/cyan]")

    inputs_dir = Path(__file__).parent / "inputs"

    if not inputs_dir.exists():
        console.print(f"[red]❌ Inputs directory not found: {inputs_dir}[/red]")
        return False

    mkv_files = list(inputs_dir.glob("*.mkv"))

    if not mkv_files:
        console.print("[red]❌ No MKV files found in inputs directory[/red]")
        return False

    # Check file sizes (should be non-zero)
    for mkv_file in mkv_files:
        if mkv_file.stat().st_size == 0:
            console.print(f"[red]❌ Empty file: {mkv_file.name}[/red]")
            return False

    console.print(f"[green]✅ Found {len(mkv_files)} MKV test files[/green]")
    return True


def test_dependencies():
    """Test that required dependencies are available."""
    console.print("[cyan]Testing dependencies...[/cyan]")

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
            console.print(f"[green]OK {description} ({package})[/green]")
        except ImportError:
            console.print(
                f"[red]FAIL Missing required: {description} ({package})[/red]"
            )
            all_good = False

    # Check optional packages
    for package, description in optional_packages:
        try:
            __import__(package)
            console.print(f"[green]OK {description} ({package})[/green]")
        except ImportError:
            console.print(
                f"[yellow]WARN Optional missing: {description} ({package})[/yellow]"
            )

    return all_good


def run_framework_test():
    """Run complete framework test suite."""
    console.print(
        Panel.fit(
            "[bold blue]Performance Testing Framework Verification[/bold blue]\n"
            "Testing all components for basic functionality...",
            title="Framework Test",
        )
    )

    tests = [
        ("Dependencies", test_dependencies),
        ("Ground Truth", test_ground_truth_loading),
        ("Configuration", test_config_loading),
        ("Input Files", test_input_files),
        ("Resource Monitor", test_resource_monitor),
        ("Profiler", test_profiler),
        ("Analysis Tools", test_analysis_tools),
    ]

    results = {}

    for test_name, test_func in tests:
        console.print(f"\n[bold cyan]=== {test_name} ===[/bold cyan]")
        try:
            results[test_name] = test_func()
        except Exception as e:
            console.print(f"[red]FAIL {test_name} test failed: {e}[/red]")
            results[test_name] = False

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Test Summary:[/bold]")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "[green]PASS[/green]" if result else "[red]FAIL[/red]"
        console.print(f"  {test_name:<20} {status}")

    console.print(f"\n[bold]Overall: {passed}/{total} tests passed[/bold]")

    if passed == total:
        console.print("[green]Framework is ready for use![/green]")
    else:
        console.print(
            f"[yellow]{total - passed} issues found. Check installation and dependencies.[/yellow]"
        )

    return passed == total


if __name__ == "__main__":
    success = run_framework_test()
    sys.exit(0 if success else 1)
