#!/usr/bin/env python3
"""
Simplified Performance Benchmark

This script runs a basic performance test without requiring the full
episode matching pipeline to be configured with reference subtitles.
"""

import json
import time
from pathlib import Path

from profiler import ComprehensiveProfiler

# Import our monitoring components
from resource_monitor import EnhancedResourceMonitor
from rich.console import Console
from rich.panel import Panel

console = Console()


def simulate_episode_processing(file_path: Path, duration: float = 2.0) -> dict:
    """
    Simulate episode processing for testing framework components.

    This simulates the actual workload without requiring subtitles.
    """
    import random

    # Simulate some work that resembles the actual processing
    result = {}

    # Simulate audio extraction (I/O intensive)
    time.sleep(duration * 0.3)

    # Simulate speech recognition (CPU intensive)
    data = []
    for i in range(int(duration * 1000)):
        data.append(i**2)

    # Simulate text matching (memory intensive)
    text_data = " ".join([f"word{i}" for i in range(int(duration * 100))])

    # Generate mock results
    file_size = file_path.stat().st_size if file_path.exists() else 1000000
    mock_accuracy = 0.75 + (random.random() * 0.25)  # 75-100% accuracy
    mock_confidence = 0.6 + (random.random() * 0.3)  # 60-90% confidence

    result = {
        "season": 1,
        "episode": 1,
        "confidence": mock_confidence,
        "reference_file": "mock_reference_S01E01.srt",
        "matched_at": duration * 0.8,
        "file_size_mb": file_size / 1024 / 1024,
    }

    return result


def run_single_benchmark(file_path: Path, iterations: int = 3) -> dict:
    """Run benchmark for a single file."""
    console.print(f"[cyan]Testing:[/cyan] {file_path.name}")

    timings = []
    results = []
    resource_data = []

    for i in range(iterations):
        console.print(f"  Iteration {i + 1}/{iterations}...")

        # Start monitoring
        monitor = EnhancedResourceMonitor(sampling_interval=0.2)

        with ComprehensiveProfiler() as profiler:
            monitor.start()
            start_time = time.perf_counter()

            # Simulate processing
            result = simulate_episode_processing(file_path, duration=1.5)

            end_time = time.perf_counter()
            resources = monitor.stop()

        timing = end_time - start_time
        profile_data = profiler.results

        timings.append(timing)
        results.append(result)
        resource_data.append(resources)

        console.print(
            f"    Time: {timing:.3f}s, Confidence: {result.get('confidence', 0):.2f}"
        )

    # Calculate statistics
    mean_time = sum(timings) / len(timings)
    mean_confidence = sum(r.get("confidence", 0) for r in results) / len(results)
    mean_cpu = sum(
        r.get("cpu", {}).get("mean_percent", 0) for r in resource_data
    ) / len(resource_data)
    mean_memory = sum(
        r.get("memory", {}).get("max_used_mb", 0) for r in resource_data
    ) / len(resource_data)

    return {
        "file": file_path.name,
        "iterations": iterations,
        "timing": {
            "mean": mean_time,
            "min": min(timings),
            "max": max(timings),
            "all": timings,
        },
        "accuracy": {
            "mean_confidence": mean_confidence,
            "success_rate": 1.0,  # Simulated success
        },
        "resources": {"cpu_percent": mean_cpu, "memory_mb": mean_memory},
        "profile_available": bool(profile_data),
    }


def run_simple_benchmark():
    """Run simplified benchmark on test files."""
    console.print(
        Panel.fit(
            "[bold blue]Simplified Performance Benchmark[/bold blue]\n"
            "Testing framework components with simulated workload",
            title="Simple Benchmark",
        )
    )

    # Load test files
    ground_truth_path = Path(__file__).parent / "ground_truth.json"
    if not ground_truth_path.exists():
        console.print("[red]Ground truth file not found[/red]")
        return

    with open(ground_truth_path) as f:
        ground_truth = json.load(f)

    inputs_dir = Path(__file__).parent / "inputs"
    test_files = []

    for test_file_info in ground_truth["test_files"]:
        file_path = inputs_dir / test_file_info["filename"]
        if file_path.exists():
            test_files.append(file_path)
        else:
            console.print(
                f"[yellow]Warning: {test_file_info['filename']} not found[/yellow]"
            )

    if not test_files:
        console.print("[red]No test files found[/red]")
        return

    console.print(f"\nFound {len(test_files)} test files")

    # Run benchmarks
    results = []
    total_files = len(test_files)

    for i, file_path in enumerate(test_files, 1):
        console.print(f"\n[bold]File {i}/{total_files}[/bold]")

        try:
            result = run_single_benchmark(
                file_path, iterations=2
            )  # Reduced iterations for speed
            results.append(result)
            console.print(f"  OK Completed: {result['timing']['mean']:.2f}s avg")

        except Exception as e:
            console.print(f"  FAIL Failed: {e}")
            continue

    # Generate summary
    console.print(f"\n{'-' * 60}")
    console.print("[bold]Benchmark Results Summary[/bold]")
    console.print(f"{'-' * 60}")

    if results:
        # Overall statistics
        all_times = []
        all_cpu = []
        all_memory = []

        for result in results:
            all_times.extend(result["timing"]["all"])
            all_cpu.append(result["resources"]["cpu_percent"])
            all_memory.append(result["resources"]["memory_mb"])

        mean_time = sum(all_times) / len(all_times)
        mean_cpu = sum(all_cpu) / len(all_cpu)
        mean_memory = sum(all_memory) / len(all_memory)

        console.print(f"Files processed: {len(results)}")
        console.print(f"Total test runs: {len(all_times)}")
        console.print(f"Average processing time: {mean_time:.3f}s")
        console.print(f"Average CPU usage: {mean_cpu:.1f}%")
        console.print(f"Average memory usage: {mean_memory:.1f}MB")

        # Individual file results
        console.print("\nPer-file breakdown:")
        for result in results:
            console.print(f"  {result['file']:<40} {result['timing']['mean']:.3f}s")

        # Save results
        output_dir = Path(__file__).parent / "reports"
        output_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"simple_benchmark_{timestamp}.json"

        summary = {
            "timestamp": timestamp,
            "test_type": "simple_benchmark",
            "files_processed": len(results),
            "total_runs": len(all_times),
            "overall_stats": {
                "mean_time": mean_time,
                "mean_cpu": mean_cpu,
                "mean_memory": mean_memory,
            },
            "individual_results": results,
        }

        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)

        console.print(f"\nResults saved to: {output_file}")
        console.print(
            "\n[bold green]Simple benchmark completed successfully![/bold green]"
        )
    else:
        console.print("[red]No successful test runs[/red]")


if __name__ == "__main__":
    run_simple_benchmark()
