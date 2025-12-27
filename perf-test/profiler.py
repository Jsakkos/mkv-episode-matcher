"""
Enhanced Profiling Tools for Performance Analysis

This module provides comprehensive profiling capabilities including
execution time, memory usage, and function call analysis.
"""

import cProfile
import functools
import pstats
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.tree import Tree


@dataclass
class FunctionProfile:
    """Profile data for a single function."""

    function_name: str
    call_count: int
    total_time: float
    cumulative_time: float
    per_call_time: float
    memory_peak_mb: float | None = None
    memory_growth_mb: float | None = None


@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""

    timestamp: float
    current_mb: float
    peak_mb: float
    traced_blocks: int


class MemoryProfiler:
    """Memory profiler using tracemalloc."""

    def __init__(self):
        self.snapshots: list[MemorySnapshot] = []
        self.start_snapshot: tracemalloc.Snapshot | None = None
        self.peak_memory_mb = 0
        self.is_tracing = False

    def start(self):
        """Start memory tracing."""
        if not self.is_tracing:
            tracemalloc.start()
            self.is_tracing = True
            self.start_snapshot = tracemalloc.take_snapshot()
            self.snapshots.clear()
            self.peak_memory_mb = 0

    def take_snapshot(self):
        """Take a memory usage snapshot."""
        if self.is_tracing:
            current, peak = tracemalloc.get_traced_memory()
            current_mb = current / 1024 / 1024
            peak_mb = peak / 1024 / 1024

            self.peak_memory_mb = max(self.peak_memory_mb, peak_mb)

            snapshot = MemorySnapshot(
                timestamp=time.perf_counter(),
                current_mb=current_mb,
                peak_mb=peak_mb,
                traced_blocks=tracemalloc.get_tracemalloc_memory() // 1024 // 1024,
            )
            self.snapshots.append(snapshot)
            return snapshot
        return None

    def stop(self) -> dict:
        """Stop memory tracing and return summary."""
        if not self.is_tracing:
            return {}

        final_snapshot = tracemalloc.take_snapshot()
        self.is_tracing = False
        tracemalloc.stop()

        # Calculate memory growth
        memory_growth_mb = 0
        if self.start_snapshot and final_snapshot:
            top_stats = final_snapshot.compare_to(self.start_snapshot, "lineno")
            memory_growth_mb = sum(stat.size_diff for stat in top_stats) / 1024 / 1024

        # Get top memory consuming functions
        top_stats = final_snapshot.statistics("lineno")[:20]
        top_functions = []

        for stat in top_stats:
            # Handle traceback format properly
            if hasattr(stat.traceback, "format"):
                traceback_info = stat.traceback.format()
                file_info = traceback_info[0] if traceback_info else "unknown"
                line_info = 0
            else:
                # Fallback for different traceback formats
                file_info = str(stat.traceback)
                line_info = 0

            top_functions.append({
                "file": file_info,
                "line": line_info,
                "size_mb": stat.size / 1024 / 1024,
                "count": stat.count,
            })

        return {
            "peak_memory_mb": self.peak_memory_mb,
            "memory_growth_mb": memory_growth_mb,
            "snapshot_count": len(self.snapshots),
            "top_functions": top_functions,
            "final_current_mb": final_snapshot.statistics("filename")[0].size
            / 1024
            / 1024
            if final_snapshot.statistics("filename")
            else 0,
        }

    def get_memory_timeline(self) -> list[dict]:
        """Get memory usage over time."""
        return [asdict(snapshot) for snapshot in self.snapshots]


class ExecutionProfiler:
    """Enhanced execution profiler with function-level statistics."""

    def __init__(self):
        self.profiler = cProfile.Profile()
        self.is_profiling = False
        self.start_time = 0
        self.end_time = 0

    def start(self):
        """Start execution profiling."""
        if not self.is_profiling:
            self.is_profiling = True
            self.start_time = time.perf_counter()
            self.profiler.enable()

    def stop(self) -> dict:
        """Stop profiling and return statistics."""
        if not self.is_profiling:
            return {}

        self.profiler.disable()
        self.end_time = time.perf_counter()
        self.is_profiling = False

        # Get statistics
        stats = pstats.Stats(self.profiler)

        # Get top functions by cumulative time
        stats.sort_stats("cumulative")
        top_functions = []

        for func_key, func_stats in stats.stats.items():
            filename, line_number, function_name = func_key

            # Skip built-in and library functions for cleaner output
            if "site-packages" in filename or filename.startswith("<"):
                continue

            # Handle different pstats formats
            if len(func_stats) == 4:
                call_count, total_time, cumulative_time, callers = func_stats
            elif len(func_stats) >= 3:
                call_count, total_time, cumulative_time = func_stats[:3]
            else:
                continue  # Skip malformed entries

            per_call_time = total_time / call_count if call_count > 0 else 0

            profile = FunctionProfile(
                function_name=f"{Path(filename).name}:{function_name}",
                call_count=call_count,
                total_time=total_time,
                cumulative_time=cumulative_time,
                per_call_time=per_call_time,
            )
            top_functions.append(profile)

            # Limit to top 50 functions
            if len(top_functions) >= 50:
                break

        return {
            "total_execution_time": self.end_time - self.start_time,
            "profiled_function_count": len(stats.stats),
            "top_functions": [asdict(func) for func in top_functions],
            "stats_summary": self._get_stats_summary(stats),
        }

    def _get_stats_summary(self, stats: pstats.Stats) -> dict:
        """Get summary statistics from pstats."""
        # Capture stats output
        output = StringIO()
        stats.print_stats(20)  # Top 20 functions
        stats_text = output.getvalue()

        return {
            "stats_text": stats_text,
            "total_calls": stats.total_calls,
            "primitive_calls": stats.prim_calls,
            "total_time": stats.total_tt,
        }


class ComprehensiveProfiler:
    """Combined profiler for execution time and memory usage."""

    def __init__(self):
        self.execution_profiler = ExecutionProfiler()
        self.memory_profiler = MemoryProfiler()
        self.custom_timings = {}
        self.start_time = 0

    def start(self):
        """Start comprehensive profiling."""
        self.start_time = time.perf_counter()
        self.execution_profiler.start()
        self.memory_profiler.start()

    def stop(self) -> dict:
        """Stop profiling and return combined results."""
        end_time = time.perf_counter()

        execution_results = self.execution_profiler.stop()
        memory_results = self.memory_profiler.stop()

        return {
            "total_wall_time": end_time - self.start_time,
            "execution_profile": execution_results,
            "memory_profile": memory_results,
            "custom_timings": self.custom_timings,
        }

    def time_function(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Time a specific function call."""
        start = time.perf_counter()
        self.memory_profiler.take_snapshot()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end = time.perf_counter()
            self.memory_profiler.take_snapshot()

            self.custom_timings[name] = {"duration": end - start, "timestamp": start}

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.results = self.stop()


def profile_function(name: str = None):
    """Decorator for profiling individual functions."""

    def decorator(func: Callable):
        func_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with ComprehensiveProfiler() as profiler:
                result = func(*args, **kwargs)

            # Store results in function attribute for later retrieval
            wrapper._profile_results = profiler.results
            wrapper._profile_name = func_name

            return result

        return wrapper

    return decorator


class ProfileReporter:
    """Generate human-readable profiling reports."""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def generate_execution_report(self, profile_data: dict) -> Table:
        """Generate a table showing execution profiling results."""
        table = Table(title="Execution Profile - Top Functions")

        table.add_column("Function", style="cyan")
        table.add_column("Calls", justify="right")
        table.add_column("Total Time (s)", justify="right")
        table.add_column("Cumulative (s)", justify="right")
        table.add_column("Per Call (ms)", justify="right")

        if "top_functions" in profile_data:
            for func_data in profile_data["top_functions"][:15]:  # Top 15
                table.add_row(
                    func_data["function_name"],
                    str(func_data["call_count"]),
                    f"{func_data['total_time']:.4f}",
                    f"{func_data['cumulative_time']:.4f}",
                    f"{func_data['per_call_time'] * 1000:.2f}",
                )

        return table

    def generate_memory_report(self, memory_data: dict) -> Table:
        """Generate a table showing memory profiling results."""
        table = Table(title="Memory Profile")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        if "peak_memory_mb" in memory_data:
            table.add_row(
                "Peak Memory Usage", f"{memory_data['peak_memory_mb']:.2f} MB"
            )

        if "memory_growth_mb" in memory_data:
            growth = memory_data["memory_growth_mb"]
            color = "red" if growth > 100 else "yellow" if growth > 50 else "green"
            table.add_row("Memory Growth", f"[{color}]{growth:.2f} MB[/{color}]")

        if "final_current_mb" in memory_data:
            table.add_row("Final Usage", f"{memory_data['final_current_mb']:.2f} MB")

        return table

    def generate_summary_report(self, profile_data: dict) -> Tree:
        """Generate a tree view of the complete profile summary."""
        tree = Tree("🔍 Performance Profile Summary")

        # Overall timing
        if "total_wall_time" in profile_data:
            timing_branch = tree.add("⏱️ Timing")
            timing_branch.add(
                f"Total Wall Time: {profile_data['total_wall_time']:.4f}s"
            )

        # Execution profile
        if "execution_profile" in profile_data:
            exec_data = profile_data["execution_profile"]
            exec_branch = tree.add("🎯 Execution Profile")

            if "profiled_function_count" in exec_data:
                exec_branch.add(
                    f"Functions Profiled: {exec_data['profiled_function_count']}"
                )

            if "top_functions" in exec_data and exec_data["top_functions"]:
                top_func = exec_data["top_functions"][0]
                exec_branch.add(
                    f"Slowest Function: {top_func['function_name']} ({top_func['cumulative_time']:.4f}s)"
                )

        # Memory profile
        if "memory_profile" in profile_data:
            mem_data = profile_data["memory_profile"]
            mem_branch = tree.add("💾 Memory Profile")

            if "peak_memory_mb" in mem_data:
                mem_branch.add(f"Peak Memory: {mem_data['peak_memory_mb']:.2f} MB")

            if "memory_growth_mb" in mem_data:
                growth = mem_data["memory_growth_mb"]
                mem_branch.add(f"Memory Growth: {growth:.2f} MB")

        # Custom timings
        if "custom_timings" in profile_data and profile_data["custom_timings"]:
            custom_branch = tree.add("🔧 Custom Timings")
            for name, timing in profile_data["custom_timings"].items():
                custom_branch.add(f"{name}: {timing['duration']:.4f}s")

        return tree

    def save_detailed_report(self, profile_data: dict, output_path: Path):
        """Save detailed profiling report to file."""
        with open(output_path, "w") as f:
            f.write("# Detailed Performance Profile Report\n\n")
            f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Execution profile
            if "execution_profile" in profile_data:
                exec_data = profile_data["execution_profile"]
                f.write("## Execution Profile\n\n")

                if (
                    "stats_summary" in exec_data
                    and "stats_text" in exec_data["stats_summary"]
                ):
                    f.write("### cProfile Output\n")
                    f.write("```\n")
                    f.write(exec_data["stats_summary"]["stats_text"])
                    f.write("\n```\n\n")

                if "top_functions" in exec_data:
                    f.write("### Top Functions by Cumulative Time\n\n")
                    f.write(
                        "| Function | Calls | Total Time (s) | Cumulative (s) | Per Call (ms) |\n"
                    )
                    f.write(
                        "|----------|-------|----------------|----------------|---------------|\n"
                    )

                    for func in exec_data["top_functions"][:25]:
                        f.write(
                            f"| {func['function_name']} | {func['call_count']} | "
                            f"{func['total_time']:.4f} | {func['cumulative_time']:.4f} | "
                            f"{func['per_call_time'] * 1000:.2f} |\n"
                        )

            # Memory profile
            if "memory_profile" in profile_data:
                mem_data = profile_data["memory_profile"]
                f.write("\n## Memory Profile\n\n")

                f.write(
                    f"- **Peak Memory Usage**: {mem_data.get('peak_memory_mb', 0):.2f} MB\n"
                )
                f.write(
                    f"- **Memory Growth**: {mem_data.get('memory_growth_mb', 0):.2f} MB\n"
                )
                f.write(
                    f"- **Final Memory Usage**: {mem_data.get('final_current_mb', 0):.2f} MB\n\n"
                )

                if "top_functions" in mem_data:
                    f.write("### Top Memory Consumers\n\n")
                    f.write("| File:Line | Size (MB) | Objects |\n")
                    f.write("|-----------|-----------|----------|\n")

                    for func in mem_data["top_functions"][:15]:
                        file_line = f"{Path(func['file']).name}:{func['line']}"
                        f.write(
                            f"| {file_line} | {func['size_mb']:.4f} | {func['count']} |\n"
                        )
