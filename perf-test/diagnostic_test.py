#!/usr/bin/env python3
"""
Diagnostic Test Script for MKV Episode Matcher Models

This script performs detailed diagnostics on different ASR model configurations
to identify why parakeet models show 0% accuracy in benchmarks.
"""

import json
import sys
import time
from pathlib import Path

import torch
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path to import the modules
sys.path.append(str(Path(__file__).parent.parent))
from mkv_episode_matcher.asr_models import create_asr_model
from mkv_episode_matcher.episode_identification import (
    EpisodeMatcher,
)
from mkv_episode_matcher.utils import clean_text, extract_season_episode

# Import the custom matcher from benchmark
sys.path.append(str(Path(__file__).parent))
from performance_benchmark import EpisodeMatcherWithCustomASR

console = Console()


class ModelDiagnostics:
    """Comprehensive diagnostics for different ASR model configurations."""

    def __init__(self, test_file: str, cache_dir: str):
        self.test_file = Path(test_file)
        self.cache_dir = Path(cache_dir).expanduser()
        self.temp_dir = self.cache_dir / "temp_diagnostics"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract show info from filename
        self.show_name = self._extract_show_name(self.test_file.name)
        self.season, self.episode = extract_season_episode(self.test_file.name)

        console.print("[bold cyan]Diagnostic Test Setup[/bold cyan]")
        console.print(f"Test File: {self.test_file.name}")
        console.print(
            f"Show: {self.show_name}, Season: {self.season}, Episode: {self.episode}"
        )
        console.print(f"Cache Dir: {self.cache_dir}")

    def _extract_show_name(self, filename: str) -> str:
        """Extract show name from filename - same logic as benchmark."""
        import re

        name = Path(filename).stem
        patterns = [
            r"^(.+?)\s*-\s*[Ss]\d+[Ee]\d+",  # "Show Name - S01E01"
            r"^(.+?)\s*-\s*\d+x\d+",  # "Show Name - 1x01"
        ]

        for pattern in patterns:
            match = re.match(pattern, name)
            if match:
                show_name = match.group(1).strip()
                show_name = show_name.replace(":", " -")
                return show_name
        return None

    def test_model_loading(self) -> dict:
        """Test if models load correctly."""
        console.print("\n[bold yellow]Testing Model Loading[/bold yellow]")
        results = {}

        # Test model configurations
        configs = [
            {"type": "whisper", "name": "tiny.en", "device": "cpu"},
            {"type": "whisper", "name": "tiny.en", "device": "cuda"},
            {
                "type": "parakeet",
                "name": "nvidia/parakeet-tdt-0.6b-v2",
                "device": "cpu",
            },
            {
                "type": "parakeet",
                "name": "nvidia/parakeet-tdt-0.6b-v2",
                "device": "cuda",
            },
        ]

        for config in configs:
            model_key = f"{config['type']}_{config['name']}_{config['device']}"
            console.print(f"  Testing: {model_key}")

            try:
                start_time = time.time()
                model = create_asr_model(config)
                model.load()
                load_time = time.time() - start_time

                results[model_key] = {
                    "status": "success",
                    "load_time": load_time,
                    "device": model.device,
                    "is_loaded": model.is_loaded,
                }
                console.print(f"    OK Loaded in {load_time:.2f}s on {model.device}")

            except Exception as e:
                results[model_key] = {"status": "failed", "error": str(e)}
                console.print(f"    FAIL Failed: {e}")

        return results

    def test_audio_extraction(self) -> dict:
        """Test audio extraction from video file."""
        console.print("\n[bold yellow]Testing Audio Extraction[/bold yellow]")

        # Create a temporary matcher to test audio extraction
        matcher = EpisodeMatcher(self.cache_dir, clean_text(self.show_name))

        try:
            # Test extracting first audio chunk
            start_time = 300  # Skip initial 5 minutes like in matching
            audio_path = matcher.extract_audio_chunk(self.test_file, start_time)
            audio_size = Path(audio_path).stat().st_size

            console.print(f"  OK Audio extracted: {audio_path}")
            console.print(f"  INFO File size: {audio_size} bytes")

            return {
                "status": "success",
                "audio_path": str(audio_path),
                "file_size": audio_size,
                "chunk_duration": matcher.chunk_duration,
            }

        except Exception as e:
            console.print(f"  FAIL Audio extraction failed: {e}")
            return {"status": "failed", "error": str(e)}

    def test_transcription_comparison(self, audio_path: str) -> dict:
        """Test transcription with different models."""
        console.print("\n[bold yellow]Testing Transcription Comparison[/bold yellow]")
        results = {}

        configs = [
            {"type": "whisper", "name": "tiny.en", "device": "cpu"},
            {"type": "whisper", "name": "tiny.en", "device": "cuda"},
            {
                "type": "parakeet",
                "name": "nvidia/parakeet-tdt-0.6b-v2",
                "device": "cpu",
            },
            {
                "type": "parakeet",
                "name": "nvidia/parakeet-tdt-0.6b-v2",
                "device": "cuda",
            },
        ]

        for config in configs:
            model_key = f"{config['type']}_{config['name']}_{config['device']}"
            console.print(f"  Testing transcription: {model_key}")

            try:
                model = create_asr_model(config)
                model.load()

                start_time = time.time()
                result = model.transcribe(audio_path)
                transcription_time = time.time() - start_time

                raw_text = result.get("text", "")
                cleaned_text = clean_text(raw_text)

                results[model_key] = {
                    "status": "success",
                    "transcription_time": transcription_time,
                    "raw_text": raw_text,
                    "cleaned_text": cleaned_text,
                    "text_length": len(raw_text),
                    "cleaned_length": len(cleaned_text),
                    "segments": len(result.get("segments", [])),
                    "language": result.get("language", "unknown"),
                }

                console.print(f"    TIME: {transcription_time:.2f}s")
                console.print(
                    f"    RAW text ({len(raw_text)} chars): {raw_text[:100]}{'...' if len(raw_text) > 100 else ''}"
                )
                console.print(
                    f"    CLEAN text ({len(cleaned_text)} chars): {cleaned_text[:100]}{'...' if len(cleaned_text) > 100 else ''}"
                )

            except Exception as e:
                results[model_key] = {"status": "failed", "error": str(e)}
                console.print(f"    FAIL Transcription failed: {e}")

        return results

    def test_matching_pipeline(self) -> dict:
        """Test the full matching pipeline with different matchers."""
        console.print("\n[bold yellow]Testing Matching Pipeline[/bold yellow]")
        results = {}

        # Test configurations
        test_configs = [
            {
                "name": "Original_Whisper_CPU",
                "matcher_type": "original",
                "device": "cpu",
                "model_config": None,
            },
            {
                "name": "Custom_Whisper_CPU",
                "matcher_type": "custom",
                "device": "cpu",
                "model_config": {"type": "whisper", "name": "tiny.en", "device": "cpu"},
            },
            {
                "name": "Custom_Whisper_CUDA",
                "matcher_type": "custom",
                "device": "cuda",
                "model_config": {
                    "type": "whisper",
                    "name": "tiny.en",
                    "device": "cuda",
                },
            },
            {
                "name": "Custom_Parakeet_CPU",
                "matcher_type": "custom",
                "device": "cpu",
                "model_config": {
                    "type": "parakeet",
                    "name": "nvidia/parakeet-tdt-0.6b-v2",
                    "device": "cpu",
                },
            },
            {
                "name": "Custom_Parakeet_CUDA",
                "matcher_type": "custom",
                "device": "cuda",
                "model_config": {
                    "type": "parakeet",
                    "name": "nvidia/parakeet-tdt-0.6b-v2",
                    "device": "cuda",
                },
            },
        ]

        for test_config in test_configs:
            name = test_config["name"]
            console.print(f"  Testing matcher: {name}")

            try:
                # Create appropriate matcher
                if test_config["matcher_type"] == "original":
                    matcher = EpisodeMatcher(
                        self.cache_dir,
                        clean_text(self.show_name),
                        device=test_config["device"],
                    )
                else:
                    matcher = EpisodeMatcherWithCustomASR(
                        self.cache_dir,
                        clean_text(self.show_name),
                        device=test_config["device"],
                        model_config=test_config["model_config"],
                    )

                # Run identification
                start_time = time.time()
                match_result = matcher.identify_episode(
                    self.test_file, self.temp_dir, self.season
                )
                matching_time = time.time() - start_time

                # Check if match is correct
                is_correct = False
                if match_result:
                    is_correct = (
                        match_result.get("season") == self.season
                        and match_result.get("episode") == self.episode
                    )

                results[name] = {
                    "status": "success",
                    "matching_time": matching_time,
                    "match_result": match_result,
                    "is_correct": is_correct,
                    "confidence": match_result.get("confidence", 0)
                    if match_result
                    else 0,
                }

                console.print(f"    TIME: {matching_time:.2f}s")
                console.print(f"    MATCH: {match_result}")
                console.print(f"    CORRECT: {is_correct}")

            except Exception as e:
                results[name] = {"status": "failed", "error": str(e)}
                console.print(f"    FAIL Matching failed: {e}")

        return results

    def test_reference_files(self) -> dict:
        """Test reference file loading."""
        console.print("\n[bold yellow]Testing Reference Files[/bold yellow]")

        matcher = EpisodeMatcher(self.cache_dir, clean_text(self.show_name))

        try:
            ref_files = matcher.get_reference_files(self.season)
            console.print(
                f"  INFO Found {len(ref_files)} reference files for season {self.season}"
            )

            if ref_files:
                # Test loading first reference chunk
                first_ref = ref_files[0]
                chunk_text = matcher.load_reference_chunk(first_ref, 0)
                console.print(
                    f"  SAMPLE reference text: {chunk_text[:100]}{'...' if len(chunk_text) > 100 else ''}"
                )

                return {
                    "status": "success",
                    "reference_count": len(ref_files),
                    "reference_files": [str(Path(f).name) for f in ref_files],
                    "sample_text": chunk_text,
                }
            else:
                return {"status": "no_references", "reference_count": 0}

        except Exception as e:
            console.print(f"  FAIL Reference file loading failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_diagnostics(self) -> dict:
        """Run comprehensive diagnostics."""
        console.print(
            Panel.fit(
                "[bold blue]MKV Episode Matcher Model Diagnostics[/bold blue]\n"
                f"Analyzing: {self.test_file.name}\n"
                f"Target: {self.show_name} S{self.season}E{self.episode}",
                title="Diagnostic Test",
            )
        )

        results = {
            "test_file": str(self.test_file),
            "show_info": {
                "show_name": self.show_name,
                "season": self.season,
                "episode": self.episode,
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": {
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count()
                if torch.cuda.is_available()
                else 0,
            },
        }

        # Run all diagnostic tests
        results["model_loading"] = self.test_model_loading()
        results["reference_files"] = self.test_reference_files()

        audio_test = self.test_audio_extraction()
        results["audio_extraction"] = audio_test

        if audio_test["status"] == "success":
            results["transcription_comparison"] = self.test_transcription_comparison(
                audio_test["audio_path"]
            )

        results["matching_pipeline"] = self.test_matching_pipeline()

        return results

    def generate_report(self, results: dict):
        """Generate diagnostic report."""
        console.print("\n" + "=" * 80)
        console.print("[bold green]DIAGNOSTIC REPORT SUMMARY[/bold green]")
        console.print("=" * 80)

        # Model Loading Summary
        loading_results = results["model_loading"]
        table = Table(title="Model Loading Results")
        table.add_column("Model", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Load Time", justify="right")
        table.add_column("Device", style="blue")

        for model_name, result in loading_results.items():
            status = "SUCCESS" if result["status"] == "success" else "FAILED"
            load_time = (
                f"{result.get('load_time', 0):.2f}s"
                if result["status"] == "success"
                else "N/A"
            )
            device = result.get("device", "N/A")
            table.add_row(model_name, status, load_time, device)

        console.print(table)

        # Matching Pipeline Summary
        matching_results = results["matching_pipeline"]
        table = Table(title="Matching Pipeline Results")
        table.add_column("Matcher", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Time", justify="right")
        table.add_column("Correct", style="bold")
        table.add_column("Confidence", justify="right")

        for matcher_name, result in matching_results.items():
            status = "SUCCESS" if result["status"] == "success" else "FAILED"
            match_time = (
                f"{result.get('matching_time', 0):.2f}s"
                if result["status"] == "success"
                else "N/A"
            )
            correct = "YES" if result.get("is_correct", False) else "NO"
            confidence = (
                f"{result.get('confidence', 0):.3f}"
                if result["status"] == "success"
                else "N/A"
            )
            table.add_row(matcher_name, status, match_time, correct, confidence)

        console.print(table)

        # Save detailed results
        output_file = (
            Path(__file__).parent
            / "reports"
            / f"diagnostic_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        console.print(f"\nDetailed report saved to: {output_file}")


def main():
    """Main diagnostic function."""
    # Test both available files
    test_files = [
        "D:/mkv-episode-matcher/perf-test/inputs/Rick and Morty - S01E01.mkv",
        "D:/mkv-episode-matcher/perf-test/inputs/The Expanse - S01E01.mkv",
    ]

    cache_dir = "~/.mkv-episode-matcher/cache"

    all_results = {}

    for test_file in test_files:
        if not Path(test_file).exists():
            console.print(f"[red]Test file not found: {test_file}[/red]")
            continue

        console.print(f"\n{'=' * 80}")
        console.print(f"[bold cyan]Testing: {Path(test_file).name}[/bold cyan]")
        console.print(f"{'=' * 80}")

        diagnostics = ModelDiagnostics(test_file, cache_dir)
        results = diagnostics.run_diagnostics()
        diagnostics.generate_report(results)

        all_results[Path(test_file).name] = results

    console.print("\n[bold green]All diagnostics complete![/bold green]")


if __name__ == "__main__":
    main()
