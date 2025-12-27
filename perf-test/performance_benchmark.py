#!/usr/bin/env python3
"""
Performance Benchmark Tool for MKV Episode Matcher

This script provides comprehensive performance testing for the episode matching algorithm,
measuring timing, accuracy, and resource usage metrics.
"""

import cProfile
import json
import pstats
import re
import statistics

# Import the core matching functionality
import sys
import time
from datetime import datetime
from io import StringIO
from pathlib import Path

import psutil
import torch
import yaml
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.append(str(Path(__file__).parent.parent))
from mkv_episode_matcher.episode_identification import (
    EpisodeMatcher,
    get_video_duration,
)
from mkv_episode_matcher.utils import clean_text, extract_season_episode

console = Console()


class EpisodeMatcherWithCustomASR(EpisodeMatcher):
    """Extended EpisodeMatcher that uses a specific ASR model configuration."""

    def __init__(
        self, cache_dir, show_name, min_confidence=0.6, device=None, model_config=None
    ):
        super().__init__(cache_dir, show_name, min_confidence, device)
        self.model_config = model_config or {
            "type": "whisper",
            "name": "tiny.en",
            "device": device,
        }

    def identify_episode(self, video_file, temp_dir, season_number):
        """Override to use the specified model configuration."""
        # Get reference files
        reference_files = self.get_reference_files(season_number)
        if not reference_files:
            logger.warning(f"No reference files found for season {season_number}")
            return None

        # Get video duration
        duration = get_video_duration(video_file)
        max_duration = min(duration - self.skip_initial_duration, 300)  # Max 5 minutes

        if max_duration <= 0:
            logger.warning(
                f"Video too short after skipping {self.skip_initial_duration}s"
            )
            return None

        # Try matching with the specific model
        return self._try_match_with_model(
            video_file, self.model_config, max_duration, reference_files
        )


class PerformanceMonitor:
    """Monitor system resource usage during benchmarks."""

    def __init__(self):
        self.process = psutil.Process()
        self.cpu_percent = []
        self.memory_usage = []
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start monitoring system resources."""
        self.start_time = time.perf_counter()
        self.cpu_percent.clear()
        self.memory_usage.clear()
        # Reset CPU percent to get accurate reading
        self.process.cpu_percent()

    def sample(self):
        """Take a sample of current resource usage."""
        if self.start_time is not None:
            cpu = self.process.cpu_percent()
            memory = self.process.memory_info().rss / 1024 / 1024  # MB
            self.cpu_percent.append(cpu)
            self.memory_usage.append(memory)

    def stop(self):
        """Stop monitoring and return summary statistics."""
        self.end_time = time.perf_counter()

        return {
            "duration_seconds": self.end_time - self.start_time,
            "cpu_percent": {
                "mean": statistics.mean(self.cpu_percent) if self.cpu_percent else 0,
                "max": max(self.cpu_percent) if self.cpu_percent else 0,
                "min": min(self.cpu_percent) if self.cpu_percent else 0,
            },
            "memory_mb": {
                "mean": statistics.mean(self.memory_usage) if self.memory_usage else 0,
                "max": max(self.memory_usage) if self.memory_usage else 0,
                "min": min(self.memory_usage) if self.memory_usage else 0,
            },
        }


class BenchmarkResult:
    """Container for benchmark results."""

    def __init__(self, filename: str, ground_truth: dict):
        self.filename = filename
        self.ground_truth = ground_truth
        self.iterations = 0
        self.timings = []
        self.matches = []
        self.resource_usage = []
        self.profile_stats = None
        self.error_count = 0
        self.errors = []

    def add_result(
        self,
        timing: float,
        match_result: dict | None,
        resources: dict,
        error: str = None,
    ):
        """Add a single benchmark result."""
        self.iterations += 1
        self.timings.append(timing)
        self.matches.append(match_result)
        self.resource_usage.append(resources)

        if error:
            self.error_count += 1
            self.errors.append(error)

    def get_timing_stats(self) -> dict:
        """Calculate timing statistics."""
        if not self.timings:
            return {}

        return {
            "mean": statistics.mean(self.timings),
            "median": statistics.median(self.timings),
            "min": min(self.timings),
            "max": max(self.timings),
            "stdev": statistics.stdev(self.timings) if len(self.timings) > 1 else 0,
        }

    def get_accuracy_stats(self) -> dict:
        """Calculate accuracy statistics."""
        successful_matches = [m for m in self.matches if m is not None]

        if not self.matches:
            return {"error": "No test runs completed"}

        # Calculate accuracy metrics
        correct_matches = 0
        for match in successful_matches:
            if (
                match
                and match.get("season") == self.ground_truth["season"]
                and match.get("episode") == self.ground_truth["episode"]
            ):
                correct_matches += 1

        total_attempts = len(self.matches)
        false_negatives = len([m for m in self.matches if m is None])
        true_positives = correct_matches
        false_positives = len(successful_matches) - correct_matches
        true_negatives = 0  # Not applicable for this use case

        accuracy = true_positives / total_attempts if total_attempts > 0 else 0
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        confidence_scores = [m.get("confidence", 0) for m in successful_matches]

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives": true_negatives,
            "confidence_stats": {
                "mean": statistics.mean(confidence_scores) if confidence_scores else 0,
                "min": min(confidence_scores) if confidence_scores else 0,
                "max": max(confidence_scores) if confidence_scores else 0,
            },
            "error_rate": self.error_count / total_attempts
            if total_attempts > 0
            else 0,
        }


class EpisodeMatcherBenchmark:
    """Main benchmark class for episode matching performance testing."""

    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        # Initialize cache_dir early so ground-truth generation can inspect cached data
        self.cache_dir = Path(self.config["cache_dir"]).expanduser()
        self.ground_truth = self.load_ground_truth()
        self.results = {}
        # Make paths absolute relative to script location
        if not Path(self.config["test_files_dir"]).is_absolute():
            self.test_files_dir = (
                Path(__file__).parent / self.config["test_files_dir"]
            ).resolve()
        else:
            self.test_files_dir = (
                Path(self.config["test_files_dir"]).expanduser().resolve()
            )
        logger.info(f"Using test files directory: {self.test_files_dir}")
        # Setup logging
        logger.remove()  # Remove default handler
        # Make output dir absolute too
        if not Path(self.config["output_dir"]).is_absolute():
            output_dir = (Path(__file__).parent / self.config["output_dir"]).resolve()
        else:
            output_dir = Path(self.config["output_dir"]).expanduser().resolve()

        logger.add(
            output_dir / "benchmark.log",
            level="DEBUG",
            format="{time} | {level} | {message}",
        )

    def load_config(self, config_path: str = None) -> dict:
        """Load benchmark configuration."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        if not Path(config_path).exists():
            # Create default config
            default_config = {
                "test_files_dir": str(Path(__file__).parent / "inputs"),
                "cache_dir": str(Path.home() / ".mkv-episode-matcher" / "cache"),
                "output_dir": str(Path(__file__).parent / "reports"),
                "iterations": 3,
                "asr_models": [
                    {"type": "whisper", "name": "tiny.en"},
                    {"type": "parakeet", "name": "nvidia/parakeet-ctc-0.6b"},
                    {"type": "faster-whisper", "name": "tiny.en"},
                ],
                "device_testing": {
                    "test_devices": ["cuda"],
                    "force_cpu_fallback": True,
                },
                "confidence_threshold": 0.6,
                "enable_profiling": True,
                "resource_monitoring_interval": 0.5,
                "timeout_seconds": 120,
            }

            with open(config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)

            return default_config

        with open(config_path) as f:
            return yaml.safe_load(f)

    def generate_ground_truth(self) -> dict:
        """Generate ground truth dataset dynamically from test files."""
        test_files = []

        # Scan for MKV files in inputs directory
        if not hasattr(self, "test_files_dir"):
            # If called before __init__ complete, create temporary path
            test_files_dir = Path(__file__).parent / "inputs"
        else:
            test_files_dir = self.test_files_dir
        console.print(
            f"Debug: generate_ground_truth using test_files_dir={test_files_dir}"
        )
        console.print(
            f"Debug: generate_ground_truth cache_dir={getattr(self, 'cache_dir', None)}"
        )

        if not test_files_dir.exists():
            console.print(f"Test files directory not found: {test_files_dir}")
            return {"test_files": []}

        for mkv_file in test_files_dir.glob("*.mkv"):
            # Extract show name (everything before " - S" or " - s")
            filename = mkv_file.name
            show_name = self._extract_show_name(filename)

            # Extract season and episode numbers
            season, episode = extract_season_episode(filename)
            console.print(
                f"Debug: found file={filename} -> show_name={show_name} season={season} episode={episode}"
            )

            if show_name and season and episode:
                # Verify subtitle files exist for this show/season
                if hasattr(self, "cache_dir") and self._has_reference_subtitles(
                    show_name, season
                ):
                    test_files.append({
                        "filename": filename,
                        "show_name": show_name,
                        "season": season,
                        "episode": episode,
                    })
                    console.print(
                        f"Added to ground truth: {filename} -> {show_name} S{season}E{episode}"
                    )
                else:
                    logger.warning(
                        f"No reference subtitles found for {show_name} Season {season}, skipping {filename}"
                    )
                    console.print(
                        f"Debug: skipping {filename} because no reference subtitles for {show_name} S{season}"
                    )
            else:
                logger.warning(f"Could not parse {filename}, skipping")
                console.print(
                    f"Debug: Could not parse filename for show/season/episode -> {filename}"
                )

        return {
            "description": "Dynamically generated ground truth from test files",
            "generated_at": datetime.now().isoformat(),
            "test_files": test_files,
        }

    def _extract_show_name(self, filename: str) -> str | None:
        """Extract show name from filename."""
        # Remove file extension
        name = Path(filename).stem

        # Look for patterns like "Show Name - S01E01" or "Show Name - s05e01"
        patterns = [
            r"^(.+?)\s*-\s*[Ss]\d+[Ee]\d+",  # "Show Name - S01E01"
            r"^(.+?)\s*-\s*\d+x\d+",  # "Show Name - 1x01"
        ]

        for pattern in patterns:
            match = re.match(pattern, name)
            if match:
                show_name = match.group(1).strip()
                # Clean up common variations
                show_name = show_name.replace(
                    ":", " -"
                )  # "Star Trek: TNG" -> "Star Trek - TNG"
                return show_name
        console.print(
            f"Debug: _extract_show_name failed to parse '{filename}' using patterns {patterns}"
        )
        return None

    def _has_reference_subtitles(self, show_name: str, season: int) -> bool:
        """Check if reference subtitle files exist for this show/season."""
        if not hasattr(self, "cache_dir"):
            return False

        # Use same logic as EpisodeMatcher to find reference files
        reference_dir = self.cache_dir / "data" / show_name
        console.print(
            f"Debug: _has_reference_subtitles checking reference_dir={reference_dir}"
        )
        if not reference_dir.exists():
            console.print(f"Debug: reference_dir does not exist: {reference_dir}")
            return False

        patterns = [
            f"S{season:02d}E",
            f"S{season}E",
            f"{season:02d}x",
            f"{season}x",
        ]
        console.print(
            f"Debug: _has_reference_subtitles will search for patterns: {patterns}"
        )
        srt_files = list(reference_dir.glob("*.srt")) + list(
            reference_dir.glob("*.SRT")
        )
        console.print(f"Debug: found {len(srt_files)} srt files in {reference_dir}")

        for pattern in patterns:
            files = [
                f
                for f in srt_files
                if re.search(f"{pattern}\\d+", f.name, re.IGNORECASE)
            ]
            console.print(f"Debug: pattern='{pattern}' matched {len(files)} files")
            if files:
                return True

        return False

    def load_ground_truth(self) -> dict:
        """Load or generate ground truth dataset."""
        # Always generate ground truth dynamically from available files
        # This ensures we only test files that actually exist and have reference subtitles
        logger.info("Generating ground truth dynamically from available test files")
        return self.generate_ground_truth()

    def run_single_test(
        self,
        file_path: Path,
        show_name: str,
        season: int,
        device: str = "auto",
        model_config: dict = None,
    ) -> tuple[dict | None, float, dict]:
        """Run a single episode matching test."""
        monitor = PerformanceMonitor()
        monitor.start()

        # Initialize matcher for this test
        # Clean the show name to match directory structure
        cleaned_show_name = clean_text(show_name)

        # Set device for the matcher
        if device == "auto":
            matcher_device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            matcher_device = device

        # Create custom matcher that uses specific ASR model if provided
        if model_config:
            model_config_with_device = model_config.copy()
            model_config_with_device["device"] = matcher_device
            matcher = EpisodeMatcherWithCustomASR(
                self.cache_dir,
                cleaned_show_name,
                min_confidence=self.config["confidence_threshold"],
                device=matcher_device,
                model_config=model_config_with_device,
            )
        else:
            matcher = EpisodeMatcher(
                self.cache_dir,
                cleaned_show_name,
                min_confidence=self.config["confidence_threshold"],
                device=matcher_device,
            )

        start_time = time.perf_counter()

        try:
            # Run the actual matching
            result = matcher.identify_episode(
                file_path, self.cache_dir / "temp", season
            )
            end_time = time.perf_counter()

            # Sample resources once more before stopping
            monitor.sample()
            resources = monitor.stop()

            timing = end_time - start_time

            return result, timing, resources

        except Exception as e:
            end_time = time.perf_counter()
            resources = monitor.stop()
            timing = end_time - start_time

            logger.error(f"Error processing {file_path}: {str(e)}")
            return None, timing, resources

    def run_profiled_test(
        self, file_path: Path, show_name: str, season: int, model_config: dict = None
    ) -> tuple[dict | None, str]:
        """Run a test with detailed profiling."""
        profiler = cProfile.Profile()

        # Clean the show name to match directory structure
        cleaned_show_name = clean_text(show_name)

        # Create matcher with custom ASR model if provided
        if model_config:
            matcher = EpisodeMatcherWithCustomASR(
                self.cache_dir,
                cleaned_show_name,
                min_confidence=self.config["confidence_threshold"],
                model_config=model_config,
            )
        else:
            matcher = EpisodeMatcher(
                self.cache_dir,
                cleaned_show_name,
                min_confidence=self.config["confidence_threshold"],
            )

        profiler.enable()

        try:
            result = matcher.identify_episode(
                file_path, self.cache_dir / "temp", season
            )
        except Exception as e:
            logger.error(f"Profiled test error for {file_path}: {str(e)}")
            result = None
        finally:
            profiler.disable()

        # Convert profile stats to string
        stats_stream = StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)  # Top 20 functions

        return result, stats_stream.getvalue()

    def benchmark_file(
        self, filename: str, device: str = "auto", model_config: dict = None
    ) -> BenchmarkResult:
        """Benchmark a single test file."""
        file_path = self.test_files_dir / filename

        # Check if the test file actually exists
        if not file_path.exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")

        # Find ground truth for this file
        ground_truth = None
        for test_file in self.ground_truth["test_files"]:
            if test_file["filename"] == filename:
                ground_truth = test_file
                break

        if not ground_truth:
            raise ValueError(f"No ground truth found for {filename}")

        # Update ground truth to include device and model info for reporting
        ground_truth_with_device = ground_truth.copy()
        ground_truth_with_device["device"] = device
        if model_config:
            ground_truth_with_device["model"] = (
                f"{model_config['type']}:{model_config['name']}"
            )

        result = BenchmarkResult(filename, ground_truth_with_device)

        model_info = (
            f"{model_config['type']}:{model_config['name']}"
            if model_config
            else "default"
        )
        console.print(
            f"[bold cyan]Benchmarking:[/bold cyan] {filename} (device: {device}, model: {model_info})"
        )

        # Run multiple iterations
        for i in range(self.config["iterations"]):
            console.print(
                f"  Running iteration {i + 1}/{self.config['iterations']} on {device}..."
            )

            match_result, timing, resources = self.run_single_test(
                file_path,
                ground_truth["show_name"],
                ground_truth["season"],
                device,
                model_config,
            )

            result.add_result(timing, match_result, resources)

        # Run profiled test if enabled
        if self.config["enable_profiling"]:
            console.print("  Running profiled test...")
            _, profile_output = self.run_profiled_test(
                file_path,
                ground_truth["show_name"],
                ground_truth["season"],
                model_config,
            )
            result.profile_stats = profile_output

        return result

    def run_benchmark_suite(self) -> dict:
        """Run the complete benchmark suite."""
        # Get model and device configurations
        models = self.config.get("asr_models", [])
        devices = self.config.get("device_testing", {}).get("test_devices", ["auto"])

        # Create list of model names for display
        model_names = []
        for model in models:
            if isinstance(model, dict):
                model_names.append(f"{model['type']}:{model['name']}")
            else:
                model_names.append(str(model))

        console.print(
            Panel.fit(
                "[bold blue]MKV Episode Matcher Performance Benchmark[/bold blue]\n"
                f"Test files: {len(self.ground_truth['test_files'])}\n"
                f"Iterations per file: {self.config['iterations']}\n"
                f"Models to test: {', '.join(model_names)}\n"
                f"Devices to test: {', '.join(devices)}",
                title="Benchmark Configuration",
            )
        )

        results = {}
        total_files = len(self.ground_truth["test_files"])
        total_tests = total_files * len(devices) * len(models)
        test_count = 0

        console.print(
            f"\n[bold cyan]Starting benchmark of {total_files} files across {len(devices)} device(s) and {len(models)} model(s)...[/bold cyan]\n"
        )

        for device in devices:
            # Check device availability
            if device == "cuda" and not torch.cuda.is_available():
                if self.config.get("device_testing", {}).get(
                    "force_cpu_fallback", True
                ):
                    console.print(
                        "[yellow]CUDA not available, skipping GPU tests[/yellow]"
                    )
                    continue
                else:
                    console.print("[red]CUDA required but not available[/red]")
                    continue

            console.print(f"\n[bold blue]Testing on device: {device}[/bold blue]")

            for model_config in models:
                model_name = f"{model_config['type']}:{model_config['name']}"
                console.print(
                    f"\n[bold magenta]Testing model: {model_name}[/bold magenta]"
                )

                for i, test_file in enumerate(self.ground_truth["test_files"], 1):
                    test_count += 1
                    filename = test_file["filename"]
                    console.print(
                        f"[dim]({test_count}/{total_tests}) {filename} on {device} with {model_name}[/dim]"
                    )

                    # Create unique key for file+device+model combination
                    result_key = f"{filename}_{device}_{model_config['type']}_{model_config['name']}"

                    try:
                        result = self.benchmark_file(filename, device, model_config)
                        results[result_key] = result

                        # Quick summary
                        timing_stats = result.get_timing_stats()
                        accuracy_stats = result.get_accuracy_stats()

                        console.print(
                            f"  OK {filename} ({device}, {model_name}): {timing_stats.get('mean', 0):.2f}s avg, "
                            f"{accuracy_stats.get('accuracy', 0):.2%} accuracy"
                        )

                    except Exception as e:
                        console.print(
                            f"  FAIL {filename} ({device}, {model_name}): [red]Failed - {str(e)}[/red]"
                        )
                        logger.error(
                            f"Benchmark failed for {filename} on {device} with {model_name}: {str(e)}"
                        )

                    console.print()  # Add spacing between tests

        return results

    def generate_report(self, results: dict[str, BenchmarkResult]):
        """Generate comprehensive performance report."""
        # Make output dir absolute relative to script location
        if not Path(self.config["output_dir"]).is_absolute():
            output_dir = (Path(__file__).parent / self.config["output_dir"]).resolve()
        else:
            output_dir = Path(self.config["output_dir"]).expanduser().resolve()
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate JSON report
        json_report = {
            "metadata": {
                "timestamp": timestamp,
                "config": self.config,
                "total_files": len(results),
                "total_iterations": sum(r.iterations for r in results.values()),
            },
            "results": {},
        }

        # Summary statistics
        all_timings = []
        all_accuracies = []

        for filename, result in results.items():
            timing_stats = result.get_timing_stats()
            accuracy_stats = result.get_accuracy_stats()

            all_timings.extend(result.timings)
            if "accuracy" in accuracy_stats:
                all_accuracies.append(accuracy_stats["accuracy"])

            json_report["results"][filename] = {
                "ground_truth": result.ground_truth,
                "iterations": result.iterations,
                "timing_stats": timing_stats,
                "accuracy_stats": accuracy_stats,
                "resource_usage": {
                    "cpu_mean": statistics.mean([
                        r["cpu_percent"]["mean"] for r in result.resource_usage
                    ]),
                    "memory_mean_mb": statistics.mean([
                        r["memory_mb"]["mean"] for r in result.resource_usage
                    ]),
                    "memory_max_mb": max([
                        r["memory_mb"]["max"] for r in result.resource_usage
                    ]),
                },
                "error_count": result.error_count,
                "errors": result.errors[:5],  # Limit error details
            }

        # Overall summary
        json_report["summary"] = {
            "overall_timing": {
                "mean": statistics.mean(all_timings) if all_timings else 0,
                "median": statistics.median(all_timings) if all_timings else 0,
                "total": sum(all_timings) if all_timings else 0,
            },
            "overall_accuracy": {
                "mean": statistics.mean(all_accuracies) if all_accuracies else 0,
                "files_with_perfect_accuracy": len([
                    a for a in all_accuracies if a == 1.0
                ]),
            },
        }

        # Save JSON report
        json_path = output_dir / f"benchmark_report_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(json_report, f, indent=2)

        # Save profile reports
        if self.config["enable_profiling"]:
            profiles_dir = output_dir / "profiles" / timestamp
            profiles_dir.mkdir(parents=True, exist_ok=True)

            for filename, result in results.items():
                if result.profile_stats:
                    profile_path = profiles_dir / f"{Path(filename).stem}_profile.txt"
                    with open(profile_path, "w") as f:
                        f.write(result.profile_stats)

        return json_path

    def display_summary_table(self, results: dict[str, BenchmarkResult]):
        """Display a summary table of results."""
        table = Table(title="Performance Benchmark Results")

        table.add_column("File", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Device", style="blue")
        table.add_column("Iterations", justify="right")
        table.add_column("Avg Time (s)", justify="right")
        table.add_column("Accuracy", justify="right")
        table.add_column("F1 Score", justify="right")
        table.add_column("Memory (MB)", justify="right")
        table.add_column("Status", style="bold")

        for result_key, result in results.items():
            timing_stats = result.get_timing_stats()
            accuracy_stats = result.get_accuracy_stats()

            # Extract info from ground truth
            gt = result.ground_truth
            filename = gt.get("filename", "unknown")
            model_info = gt.get("model", "default")
            device = gt.get("device", "unknown")

            avg_memory = statistics.mean([
                r["memory_mb"]["mean"] for r in result.resource_usage
            ])

            status = "PASS" if accuracy_stats.get("accuracy", 0) > 0.8 else "REVIEW"
            status_style = "green" if "PASS" in status else "yellow"

            table.add_row(
                Path(filename).stem,
                model_info,
                device,
                str(result.iterations),
                f"{timing_stats.get('mean', 0):.2f}",
                f"{accuracy_stats.get('accuracy', 0):.1%}",
                f"{accuracy_stats.get('f1_score', 0):.3f}",
                f"{avg_memory:.1f}",
                f"[{status_style}]{status}[/{status_style}]",
            )

        console.print(table)


def main():
    """Main entry point for the benchmark tool."""
    console.print(
        "[bold blue]MKV Episode Matcher Performance Benchmark Tool[/bold blue]\n"
    )

    benchmark = EpisodeMatcherBenchmark()

    try:
        # Run the benchmark suite
        results = benchmark.run_benchmark_suite()

        # Generate detailed report
        report_path = benchmark.generate_report(results)

        # Display summary
        benchmark.display_summary_table(results)

        console.print("\n[bold green]Benchmark complete![/bold green]")
        console.print(f"Detailed report saved to: {report_path}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Benchmark failed: {str(e)}[/red]")
        logger.exception("Benchmark execution failed")


if __name__ == "__main__":
    main()
