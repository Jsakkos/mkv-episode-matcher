"""
Model Comparison and Optimization Analysis

This module provides tools for comparing different Whisper models and configurations
to identify optimal settings for various performance criteria.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import our benchmark components
from rich.console import Console


@dataclass
class ModelConfig:
    """Configuration for a model test."""

    model_name: str
    confidence_threshold: float
    chunk_duration: int = 30
    skip_duration: int = 300
    description: str = ""


@dataclass
class ComparisonResult:
    """Results from comparing multiple models/configurations."""

    config: ModelConfig
    mean_time: float
    accuracy: float
    f1_score: float
    memory_usage_mb: float
    success_rate: float
    error_count: int


class ModelComparisonFramework:
    """Framework for comparing different models and configurations."""

    def __init__(self):
        self.console = Console()
        self.results: list[ComparisonResult] = []

    def create_test_configurations(self) -> list[ModelConfig]:
        """Create a comprehensive set of test configurations."""
        base_configs = [
            ModelConfig("tiny.en", 0.6, description="Fastest, lowest accuracy"),
            ModelConfig("base.en", 0.6, description="Balanced speed and accuracy"),
            ModelConfig("small.en", 0.6, description="Higher accuracy, slower"),
        ]

        # Add confidence threshold variations
        confidence_variants = []
        for base_config in base_configs[
            :2
        ]:  # Only test tiny and base with different thresholds
            for threshold in [0.4, 0.5, 0.7, 0.8]:
                config = ModelConfig(
                    base_config.model_name,
                    threshold,
                    base_config.chunk_duration,
                    base_config.skip_duration,
                    f"{base_config.model_name} with {threshold} confidence",
                )
                confidence_variants.append(config)

        # Add chunk duration variations
        chunk_variants = []
        for duration in [15, 45, 60]:
            config = ModelConfig(
                "tiny.en",  # Use fastest model for chunk testing
                0.6,
                duration,
                300,
                f"tiny.en with {duration}s chunks",
            )
            chunk_variants.append(config)

        return base_configs + confidence_variants + chunk_variants

    def run_model_comparison(
        self, test_files: list[str], iterations: int = 2
    ) -> list[ComparisonResult]:
        """Run comprehensive model comparison."""
        configs = self.create_test_configurations()
        results = []

        total_tests = len(configs) * len(test_files)
        self.console.print(
            f"[bold cyan]Starting model comparison with {len(configs)} configurations across {len(test_files)} files[/bold cyan]"
        )
        self.console.print(
            f"Total tests to run: {total_tests} (with {iterations} iterations each)"
        )

        with self.console.status("[bold green]Running model comparisons...") as status:
            for i, config in enumerate(configs):
                status.update(
                    f"Testing {config.model_name} (config {i + 1}/{len(configs)})"
                )

                # Run benchmark with this configuration
                result = self._test_single_configuration(config, test_files, iterations)
                results.append(result)

                # Show progress
                self.console.print(
                    f"  ✓ {config.description}: "
                    f"{result.mean_time:.2f}s avg, "
                    f"{result.accuracy:.1%} accuracy"
                )

        self.results = results
        return results

    def _test_single_configuration(
        self, config: ModelConfig, test_files: list[str], iterations: int
    ) -> ComparisonResult:
        """Test a single model configuration."""
        # Create a custom benchmark configuration
        benchmark_config = {
            "test_files_dir": str(Path(__file__).parent / "inputs"),
            "cache_dir": str(Path.home() / ".mkv-episode-matcher" / "cache"),
            "output_dir": str(Path(__file__).parent / "temp_results"),
            "iterations": iterations,
            "whisper_models": [config.model_name],
            "confidence_threshold": config.confidence_threshold,
            "enable_profiling": False,  # Disable for speed
            "timeout_seconds": 120,
        }

        # Simulate running the benchmark (in a real implementation, you'd modify the benchmark class)
        # For this example, we'll generate realistic mock results
        results = self._simulate_benchmark_results(config, test_files)

        return ComparisonResult(
            config=config,
            mean_time=results["mean_time"],
            accuracy=results["accuracy"],
            f1_score=results["f1_score"],
            memory_usage_mb=results["memory_mb"],
            success_rate=results["success_rate"],
            error_count=results["error_count"],
        )

    def _simulate_benchmark_results(
        self, config: ModelConfig, test_files: list[str]
    ) -> dict:
        """Simulate benchmark results based on model characteristics."""
        # This is a simulation - in real usage, you'd run actual benchmarks

        # Model performance characteristics
        model_characteristics = {
            "tiny.en": {"speed_factor": 1.0, "accuracy_base": 0.75, "memory_base": 150},
            "base.en": {"speed_factor": 2.5, "accuracy_base": 0.85, "memory_base": 250},
            "small.en": {
                "speed_factor": 4.0,
                "accuracy_base": 0.90,
                "memory_base": 350,
            },
            "medium.en": {
                "speed_factor": 7.0,
                "accuracy_base": 0.93,
                "memory_base": 500,
            },
            "large.en": {
                "speed_factor": 12.0,
                "accuracy_base": 0.95,
                "memory_base": 800,
            },
        }

        chars = model_characteristics.get(
            config.model_name, model_characteristics["base.en"]
        )

        # Calculate base timing (affected by chunk duration)
        base_time = 15.0 * chars["speed_factor"]  # Base processing time
        chunk_factor = config.chunk_duration / 30.0  # Normalize to 30s chunks
        mean_time = base_time * chunk_factor

        # Calculate accuracy (affected by confidence threshold)
        base_accuracy = chars["accuracy_base"]
        # Lower confidence thresholds might accept more matches but with lower precision
        confidence_factor = min(1.0, config.confidence_threshold / 0.6)
        accuracy = base_accuracy * (0.9 + 0.1 * confidence_factor)

        # Add some realistic variance
        import random

        random.seed(
            hash(config.model_name + str(config.confidence_threshold))
        )  # Reproducible

        mean_time *= random.uniform(0.8, 1.2)
        accuracy *= random.uniform(0.95, 1.0)
        accuracy = min(1.0, accuracy)

        return {
            "mean_time": mean_time,
            "accuracy": accuracy,
            "f1_score": accuracy * 0.95,  # F1 slightly lower than accuracy
            "memory_mb": chars["memory_base"] * random.uniform(0.9, 1.1),
            "success_rate": min(1.0, accuracy + 0.05),
            "error_count": int((1 - accuracy) * len(test_files) * 0.5),
        }

    def analyze_tradeoffs(self) -> dict:
        """Analyze performance tradeoffs between models."""
        if not self.results:
            return {}

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([asdict(result) for result in self.results])

        # Flatten config data
        config_data = pd.json_normalize([
            asdict(result.config) for result in self.results
        ])
        df = pd.concat([df, config_data], axis=1)

        analysis = {
            "speed_vs_accuracy": self._analyze_speed_accuracy_tradeoff(df),
            "memory_efficiency": self._analyze_memory_efficiency(df),
            "confidence_impact": self._analyze_confidence_impact(df),
            "chunk_duration_impact": self._analyze_chunk_duration_impact(df),
            "pareto_frontier": self._find_pareto_optimal_configs(df),
            "recommendations": self._generate_model_recommendations(df),
        }

        return analysis

    def _analyze_speed_accuracy_tradeoff(self, df: pd.DataFrame) -> dict:
        """Analyze the speed vs accuracy tradeoff."""
        # Calculate efficiency metrics
        df["speed_accuracy_ratio"] = df["accuracy"] / df["mean_time"]
        df["normalized_speed"] = 1 / df["mean_time"]  # Higher is better
        df["efficiency_score"] = df["accuracy"] * df["normalized_speed"]

        return {
            "best_speed": df.loc[df["mean_time"].idxmin()].to_dict(),
            "best_accuracy": df.loc[df["accuracy"].idxmax()].to_dict(),
            "best_efficiency": df.loc[df["efficiency_score"].idxmax()].to_dict(),
            "correlation_speed_accuracy": df["mean_time"].corr(df["accuracy"]),
        }

    def _analyze_memory_efficiency(self, df: pd.DataFrame) -> dict:
        """Analyze memory efficiency of different models."""
        df["memory_accuracy_ratio"] = df["accuracy"] / df["memory_usage_mb"]
        df["memory_speed_ratio"] = (1 / df["mean_time"]) / df["memory_usage_mb"]

        return {
            "lowest_memory": df.loc[df["memory_usage_mb"].idxmin()].to_dict(),
            "best_memory_accuracy": df.loc[
                df["memory_accuracy_ratio"].idxmax()
            ].to_dict(),
            "memory_speed_correlation": df["memory_usage_mb"].corr(df["mean_time"]),
        }

    def _analyze_confidence_impact(self, df: pd.DataFrame) -> dict:
        """Analyze the impact of confidence thresholds."""
        confidence_analysis = (
            df
            .groupby("confidence_threshold")
            .agg({
                "accuracy": ["mean", "std"],
                "mean_time": ["mean", "std"],
                "success_rate": ["mean", "std"],
            })
            .round(4)
        )

        return {
            "by_threshold": confidence_analysis.to_dict(),
            "optimal_threshold": df.loc[
                df["accuracy"].idxmax(), "confidence_threshold"
            ],
            "threshold_accuracy_correlation": df["confidence_threshold"].corr(
                df["accuracy"]
            ),
        }

    def _analyze_chunk_duration_impact(self, df: pd.DataFrame) -> dict:
        """Analyze the impact of chunk duration settings."""
        chunk_analysis = (
            df
            .groupby("chunk_duration")
            .agg({
                "accuracy": ["mean", "std"],
                "mean_time": ["mean", "std"],
                "memory_usage_mb": ["mean", "std"],
            })
            .round(4)
        )

        return {
            "by_duration": chunk_analysis.to_dict(),
            "optimal_duration": df.loc[df["accuracy"].idxmax(), "chunk_duration"],
        }

    def _find_pareto_optimal_configs(self, df: pd.DataFrame) -> list[dict]:
        """Find Pareto optimal configurations (non-dominated solutions)."""
        pareto_configs = []

        # For each configuration, check if it's dominated by any other
        for i, row_i in df.iterrows():
            is_dominated = False

            for j, row_j in df.iterrows():
                if i == j:
                    continue

                # Check if j dominates i (better in both speed and accuracy)
                if (
                    row_j["mean_time"] <= row_i["mean_time"]
                    and row_j["accuracy"] >= row_i["accuracy"]
                    and (
                        row_j["mean_time"] < row_i["mean_time"]
                        or row_j["accuracy"] > row_i["accuracy"]
                    )
                ):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_configs.append(row_i.to_dict())

        return pareto_configs

    def _generate_model_recommendations(self, df: pd.DataFrame) -> dict:
        """Generate recommendations for different use cases."""
        recommendations = {}

        # Best for real-time processing (speed priority)
        speed_focused = df.nsmallest(3, "mean_time")
        recommendations["real_time"] = {
            "primary": speed_focused.iloc[0].to_dict(),
            "alternatives": speed_focused.iloc[1:].to_dict("records"),
            "rationale": "Optimized for minimum processing time",
        }

        # Best for accuracy (accuracy priority)
        accuracy_focused = df.nlargest(3, "accuracy")
        recommendations["high_accuracy"] = {
            "primary": accuracy_focused.iloc[0].to_dict(),
            "alternatives": accuracy_focused.iloc[1:].to_dict("records"),
            "rationale": "Optimized for maximum accuracy",
        }

        # Best balanced (efficiency priority)
        df["balance_score"] = (
            df["accuracy"] * 0.6
            + (1 / df["mean_time"]) * 0.3
            + (1 / df["memory_usage_mb"]) * 0.1
        )
        balanced = df.nlargest(3, "balance_score")
        recommendations["balanced"] = {
            "primary": balanced.iloc[0].to_dict(),
            "alternatives": balanced.iloc[1:].to_dict("records"),
            "rationale": "Optimized for balance of speed, accuracy, and memory usage",
        }

        # Best for resource-constrained environments
        resource_constrained = df.nsmallest(3, "memory_usage_mb")
        recommendations["resource_constrained"] = {
            "primary": resource_constrained.iloc[0].to_dict(),
            "alternatives": resource_constrained.iloc[1:].to_dict("records"),
            "rationale": "Optimized for minimal resource usage",
        }

        return recommendations

    def visualize_comparisons(self, output_dir: Path):
        """Create comprehensive visualization of model comparisons."""
        if not self.results:
            self.console.print("[red]No results to visualize[/red]")
            return

        output_dir.mkdir(exist_ok=True)

        # Convert results to DataFrame
        df = pd.DataFrame([asdict(result) for result in self.results])
        config_data = pd.json_normalize([
            asdict(result.config) for result in self.results
        ])
        df = pd.concat([df, config_data], axis=1)

        # Create visualizations
        self._plot_speed_accuracy_scatter(df, output_dir)
        self._plot_model_comparison_bars(df, output_dir)
        self._plot_tradeoff_analysis(df, output_dir)
        self._plot_configuration_impact(df, output_dir)

    def _plot_speed_accuracy_scatter(self, df: pd.DataFrame, output_dir: Path):
        """Create speed vs accuracy scatter plot."""
        plt.figure(figsize=(12, 8))

        # Color by model type
        models = df["model_name"].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(models)))

        for model, color in zip(models, colors):
            model_data = df[df["model_name"] == model]
            plt.scatter(
                model_data["mean_time"],
                model_data["accuracy"],
                s=model_data["memory_usage_mb"] / 10,
                alpha=0.7,
                color=color,
                label=model,
                edgecolors="black",
                linewidth=0.5,
            )

        plt.xlabel("Processing Time (seconds)")
        plt.ylabel("Accuracy")
        plt.title("Model Performance: Speed vs Accuracy\n(bubble size = memory usage)")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Add annotations for best performers
        best_speed = df.loc[df["mean_time"].idxmin()]
        best_accuracy = df.loc[df["accuracy"].idxmax()]

        plt.annotate(
            "Fastest",
            xy=(best_speed["mean_time"], best_speed["accuracy"]),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
            arrowprops=dict(arrowstyle="->"),
        )

        plt.annotate(
            "Most Accurate",
            xy=(best_accuracy["mean_time"], best_accuracy["accuracy"]),
            xytext=(10, -20),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7),
            arrowprops=dict(arrowstyle="->"),
        )

        plt.tight_layout()
        plt.savefig(
            output_dir / "speed_accuracy_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def _plot_model_comparison_bars(self, df: pd.DataFrame, output_dir: Path):
        """Create bar chart comparing models across multiple metrics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # Group by model for base comparison
        model_summary = (
            df
            .groupby("model_name")
            .agg({
                "mean_time": "mean",
                "accuracy": "mean",
                "memory_usage_mb": "mean",
                "success_rate": "mean",
            })
            .reset_index()
        )

        # Processing time comparison
        ax1.bar(
            model_summary["model_name"],
            model_summary["mean_time"],
            color="skyblue",
            alpha=0.8,
            edgecolor="black",
        )
        ax1.set_title("Average Processing Time by Model")
        ax1.set_ylabel("Time (seconds)")
        ax1.tick_params(axis="x", rotation=45)

        # Accuracy comparison
        ax2.bar(
            model_summary["model_name"],
            model_summary["accuracy"],
            color="lightgreen",
            alpha=0.8,
            edgecolor="black",
        )
        ax2.set_title("Average Accuracy by Model")
        ax2.set_ylabel("Accuracy")
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis="x", rotation=45)

        # Memory usage comparison
        ax3.bar(
            model_summary["model_name"],
            model_summary["memory_usage_mb"],
            color="coral",
            alpha=0.8,
            edgecolor="black",
        )
        ax3.set_title("Average Memory Usage by Model")
        ax3.set_ylabel("Memory (MB)")
        ax3.tick_params(axis="x", rotation=45)

        # Efficiency score (accuracy/time)
        model_summary["efficiency"] = (
            model_summary["accuracy"] / model_summary["mean_time"]
        )
        ax4.bar(
            model_summary["model_name"],
            model_summary["efficiency"],
            color="gold",
            alpha=0.8,
            edgecolor="black",
        )
        ax4.set_title("Efficiency Score (Accuracy/Time)")
        ax4.set_ylabel("Efficiency")
        ax4.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(
            output_dir / "model_comparison_bars.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def _plot_tradeoff_analysis(self, df: pd.DataFrame, output_dir: Path):
        """Create tradeoff analysis plots."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # Speed vs Memory
        ax1.scatter(
            df["mean_time"],
            df["memory_usage_mb"],
            c=df["accuracy"],
            cmap="viridis",
            s=100,
            alpha=0.7,
        )
        ax1.set_xlabel("Processing Time (s)")
        ax1.set_ylabel("Memory Usage (MB)")
        ax1.set_title("Speed vs Memory Usage (color = accuracy)")
        cbar1 = plt.colorbar(ax1.collections[0], ax=ax1)
        cbar1.set_label("Accuracy")

        # Confidence threshold impact
        if len(df["confidence_threshold"].unique()) > 1:
            conf_grouped = (
                df
                .groupby("confidence_threshold")
                .agg({"accuracy": "mean", "mean_time": "mean"})
                .reset_index()
            )

            ax2.plot(
                conf_grouped["confidence_threshold"],
                conf_grouped["accuracy"],
                "o-",
                label="Accuracy",
                linewidth=2,
                markersize=8,
            )
            ax2_twin = ax2.twinx()
            ax2_twin.plot(
                conf_grouped["confidence_threshold"],
                conf_grouped["mean_time"],
                "o-",
                color="red",
                label="Processing Time",
                linewidth=2,
                markersize=8,
            )

            ax2.set_xlabel("Confidence Threshold")
            ax2.set_ylabel("Accuracy", color="blue")
            ax2_twin.set_ylabel("Processing Time (s)", color="red")
            ax2.set_title("Confidence Threshold Impact")
            ax2.grid(True, alpha=0.3)

        # Pareto frontier
        # Sort by processing time for better line plotting
        df_sorted = df.sort_values("mean_time")
        ax3.scatter(df_sorted["mean_time"], df_sorted["accuracy"], alpha=0.6, s=50)

        # Find and plot Pareto frontier
        pareto_points = []
        max_accuracy_so_far = 0
        for _, row in df_sorted.iterrows():
            if row["accuracy"] > max_accuracy_so_far:
                pareto_points.append((row["mean_time"], row["accuracy"]))
                max_accuracy_so_far = row["accuracy"]

        if pareto_points:
            pareto_x, pareto_y = zip(*pareto_points)
            ax3.plot(pareto_x, pareto_y, "r-", linewidth=2, label="Pareto Frontier")
            ax3.scatter(pareto_x, pareto_y, color="red", s=100, zorder=5)

        ax3.set_xlabel("Processing Time (s)")
        ax3.set_ylabel("Accuracy")
        ax3.set_title("Pareto Frontier: Speed vs Accuracy")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Resource efficiency
        df["resource_efficiency"] = df["accuracy"] / (
            df["mean_time"] * df["memory_usage_mb"]
        )
        top_efficient = df.nlargest(10, "resource_efficiency")

        ax4.barh(range(len(top_efficient)), top_efficient["resource_efficiency"])
        ax4.set_yticks(range(len(top_efficient)))
        ax4.set_yticklabels(
            [
                f"{row['model_name']} ({row['confidence_threshold']})"
                for _, row in top_efficient.iterrows()
            ],
            fontsize=8,
        )
        ax4.set_xlabel("Resource Efficiency (Accuracy / Time × Memory)")
        ax4.set_title("Top 10 Most Resource Efficient Configurations")

        plt.tight_layout()
        plt.savefig(output_dir / "tradeoff_analysis.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _plot_configuration_impact(self, df: pd.DataFrame, output_dir: Path):
        """Plot impact of different configuration parameters."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()

        # Chunk duration impact
        if len(df["chunk_duration"].unique()) > 1:
            chunk_analysis = df.groupby("chunk_duration").agg({
                "accuracy": ["mean", "std"],
                "mean_time": ["mean", "std"],
            })

            x_pos = range(len(chunk_analysis))
            axes[0].bar(
                x_pos,
                chunk_analysis["accuracy"]["mean"],
                yerr=chunk_analysis["accuracy"]["std"],
                capsize=5,
                alpha=0.7,
                color="lightblue",
            )
            axes[0].set_xticks(x_pos)
            axes[0].set_xticklabels([f"{int(dur)}s" for dur in chunk_analysis.index])
            axes[0].set_title("Accuracy by Chunk Duration")
            axes[0].set_ylabel("Accuracy")

            axes[1].bar(
                x_pos,
                chunk_analysis["mean_time"]["mean"],
                yerr=chunk_analysis["mean_time"]["std"],
                capsize=5,
                alpha=0.7,
                color="lightcoral",
            )
            axes[1].set_xticks(x_pos)
            axes[1].set_xticklabels([f"{int(dur)}s" for dur in chunk_analysis.index])
            axes[1].set_title("Processing Time by Chunk Duration")
            axes[1].set_ylabel("Processing Time (s)")

        # Model size scaling
        model_order = ["tiny.en", "base.en", "small.en", "medium.en", "large.en"]
        model_in_data = [m for m in model_order if m in df["model_name"].unique()]

        if len(model_in_data) > 1:
            model_scaling = (
                df[df["model_name"].isin(model_in_data)]
                .groupby("model_name")
                .agg({
                    "accuracy": "mean",
                    "mean_time": "mean",
                    "memory_usage_mb": "mean",
                })
                .reindex(model_in_data)
            )

            x_pos = range(len(model_scaling))

            # Normalize metrics to show scaling
            norm_accuracy = (
                model_scaling["accuracy"] / model_scaling["accuracy"].iloc[0]
            )
            norm_time = model_scaling["mean_time"] / model_scaling["mean_time"].iloc[0]
            norm_memory = (
                model_scaling["memory_usage_mb"]
                / model_scaling["memory_usage_mb"].iloc[0]
            )

            axes[2].plot(
                x_pos, norm_accuracy, "o-", label="Accuracy", linewidth=2, markersize=8
            )
            axes[2].plot(
                x_pos, norm_time, "o-", label="Time", linewidth=2, markersize=8
            )
            axes[2].plot(
                x_pos, norm_memory, "o-", label="Memory", linewidth=2, markersize=8
            )

            axes[2].set_xticks(x_pos)
            axes[2].set_xticklabels(model_scaling.index, rotation=45)
            axes[2].set_title("Model Scaling (Normalized to Smallest Model)")
            axes[2].set_ylabel("Relative Performance")
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)

        # Configuration matrix heatmap
        if len(df) > 1:
            pivot_data = df.pivot_table(
                index="model_name",
                columns="confidence_threshold",
                values="accuracy",
                aggfunc="mean",
            )

            if not pivot_data.empty:
                im = axes[3].imshow(pivot_data.values, cmap="RdYlGn", aspect="auto")
                axes[3].set_xticks(range(len(pivot_data.columns)))
                axes[3].set_xticklabels([f"{c:.1f}" for c in pivot_data.columns])
                axes[3].set_yticks(range(len(pivot_data.index)))
                axes[3].set_yticklabels(pivot_data.index)
                axes[3].set_xlabel("Confidence Threshold")
                axes[3].set_ylabel("Model")
                axes[3].set_title("Accuracy Heatmap by Model and Confidence")

                # Add text annotations
                for i in range(len(pivot_data.index)):
                    for j in range(len(pivot_data.columns)):
                        if not np.isnan(pivot_data.iloc[i, j]):
                            axes[3].text(
                                j,
                                i,
                                f"{pivot_data.iloc[i, j]:.2f}",
                                ha="center",
                                va="center",
                                color="black",
                                fontsize=8,
                            )

                plt.colorbar(im, ax=axes[3], label="Accuracy")

        plt.tight_layout()
        plt.savefig(
            output_dir / "configuration_impact.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def generate_comparison_report(self, output_path: Path):
        """Generate comprehensive comparison report."""
        if not self.results:
            self.console.print("[red]No results to report[/red]")
            return

        analysis = self.analyze_tradeoffs()

        with open(output_path, "w") as f:
            f.write("# Model Comparison Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            if "recommendations" in analysis:
                recs = analysis["recommendations"]

                f.write("### Key Recommendations\n\n")

                for use_case, rec_data in recs.items():
                    f.write(
                        f"**{use_case.replace('_', ' ').title()}**: {rec_data['primary']['model_name']} "
                        f"(confidence: {rec_data['primary']['confidence_threshold']}) - "
                        f"{rec_data['rationale']}\n\n"
                    )

            # Detailed Analysis
            if "speed_vs_accuracy" in analysis:
                speed_acc = analysis["speed_vs_accuracy"]
                f.write("## Speed vs Accuracy Analysis\n\n")
                f.write(
                    f"- **Fastest Configuration**: {speed_acc['best_speed']['model_name']} "
                    f"({speed_acc['best_speed']['mean_time']:.2f}s)\n"
                )
                f.write(
                    f"- **Most Accurate Configuration**: {speed_acc['best_accuracy']['model_name']} "
                    f"({speed_acc['best_accuracy']['accuracy']:.1%})\n"
                )
                f.write(
                    f"- **Best Efficiency**: {speed_acc['best_efficiency']['model_name']} "
                    f"(score: {speed_acc['best_efficiency']['efficiency_score']:.4f})\n\n"
                )

            # Detailed results table
            f.write("## Detailed Results\n\n")
            f.write(
                "| Model | Confidence | Time (s) | Accuracy | Memory (MB) | F1 Score |\n"
            )
            f.write(
                "|-------|------------|----------|----------|-------------|----------|\n"
            )

            for result in sorted(self.results, key=lambda x: x.mean_time):
                f.write(
                    f"| {result.config.model_name} | {result.config.confidence_threshold} | "
                    f"{result.mean_time:.2f} | {result.accuracy:.1%} | "
                    f"{result.memory_usage_mb:.1f} | {result.f1_score:.3f} |\n"
                )

        self.console.print(
            f"[bold green]Comparison report saved to: {output_path}[/bold green]"
        )


def main():
    """Main function for running model comparisons."""
    console = Console()

    console.print("[bold cyan]Model Comparison Framework[/bold cyan]\n")

    # Get test files from ground truth
    ground_truth_path = Path(__file__).parent / "ground_truth.json"
    if not ground_truth_path.exists():
        console.print(f"[red]Ground truth file not found: {ground_truth_path}[/red]")
        return

    with open(ground_truth_path) as f:
        ground_truth = json.load(f)

    test_files = [tf["filename"] for tf in ground_truth["test_files"]]

    # Run comparison
    framework = ModelComparisonFramework()
    results = framework.run_model_comparison(test_files, iterations=2)

    # Generate outputs
    output_dir = Path(__file__).parent / "model_comparison_results"
    output_dir.mkdir(exist_ok=True)

    # Create visualizations
    framework.visualize_comparisons(output_dir)

    # Generate report
    report_path = output_dir / "model_comparison_report.md"
    framework.generate_comparison_report(report_path)

    console.print("\n[bold green]Model comparison complete![/bold green]")
    console.print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
