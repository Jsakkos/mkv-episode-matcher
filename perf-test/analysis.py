"""
Performance Analysis and Visualization Tools

This module provides tools for analyzing benchmark results and generating
visualizations to understand performance characteristics and identify bottlenecks.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console
from rich.table import Table

# Configure matplotlib for better plots
plt.style.use("default")
sns.set_palette("husl")


class BenchmarkAnalyzer:
    """Analyze benchmark results and generate insights."""

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.results_data = None
        self.df = None

    def load_results(self, results_path: Path) -> dict:
        """Load benchmark results from JSON file."""
        with open(results_path) as f:
            self.results_data = json.load(f)

        # Convert to DataFrame for easier analysis
        self.df = self._create_dataframe()
        return self.results_data

    def _create_dataframe(self) -> pd.DataFrame:
        """Create a pandas DataFrame from benchmark results."""
        if not self.results_data or "results" not in self.results_data:
            return pd.DataFrame()

        rows = []
        for filename, result in self.results_data["results"].items():
            timing_stats = result.get("timing_stats", {})
            accuracy_stats = result.get("accuracy_stats", {})
            resource_usage = result.get("resource_usage", {})

            row = {
                "filename": filename,
                "show": result.get("ground_truth", {}).get("show_name", "Unknown"),
                "season": result.get("ground_truth", {}).get("season", 0),
                "episode": result.get("ground_truth", {}).get("episode", 0),
                "iterations": result.get("iterations", 0),
                "mean_time": timing_stats.get("mean", 0),
                "median_time": timing_stats.get("median", 0),
                "min_time": timing_stats.get("min", 0),
                "max_time": timing_stats.get("max", 0),
                "time_std": timing_stats.get("stdev", 0),
                "accuracy": accuracy_stats.get("accuracy", 0),
                "precision": accuracy_stats.get("precision", 0),
                "recall": accuracy_stats.get("recall", 0),
                "f1_score": accuracy_stats.get("f1_score", 0),
                "confidence_mean": accuracy_stats.get("confidence_stats", {}).get(
                    "mean", 0
                ),
                "confidence_max": accuracy_stats.get("confidence_stats", {}).get(
                    "max", 0
                ),
                "cpu_mean": resource_usage.get("cpu_mean", 0),
                "memory_mean_mb": resource_usage.get("memory_mean_mb", 0),
                "memory_max_mb": resource_usage.get("memory_max_mb", 0),
                "error_count": result.get("error_count", 0),
                "success_rate": 1.0
                - (result.get("error_count", 0) / max(result.get("iterations", 1), 1)),
            }
            rows.append(row)

        return pd.DataFrame(rows)

    def generate_timing_analysis(self) -> dict:
        """Analyze timing performance across all tests."""
        if self.df.empty:
            return {}

        timing_analysis = {
            "overall_stats": {
                "mean_processing_time": self.df["mean_time"].mean(),
                "median_processing_time": self.df["median_time"].median(),
                "fastest_file": self.df.loc[self.df["mean_time"].idxmin(), "filename"],
                "slowest_file": self.df.loc[self.df["mean_time"].idxmax(), "filename"],
                "time_range": self.df["mean_time"].max() - self.df["mean_time"].min(),
                "coefficient_of_variation": self.df["mean_time"].std()
                / self.df["mean_time"].mean()
                if self.df["mean_time"].mean() > 0
                else 0,
            },
            "timing_by_show": self.df
            .groupby("show")["mean_time"]
            .agg(["mean", "std", "min", "max"])
            .to_dict("index"),
            "performance_outliers": self._identify_performance_outliers(),
        }

        return timing_analysis

    def generate_accuracy_analysis(self) -> dict:
        """Analyze accuracy metrics across all tests."""
        if self.df.empty:
            return {}

        accuracy_analysis = {
            "overall_stats": {
                "mean_accuracy": self.df["accuracy"].mean(),
                "perfect_accuracy_count": len(self.df[self.df["accuracy"] == 1.0]),
                "failed_matches_count": len(self.df[self.df["accuracy"] == 0.0]),
                "mean_f1_score": self.df["f1_score"].mean(),
                "mean_confidence": self.df["confidence_mean"].mean(),
            },
            "accuracy_by_show": self.df
            .groupby("show")["accuracy"]
            .agg(["mean", "std", "count"])
            .to_dict("index"),
            "confidence_analysis": {
                "high_confidence_accurate": len(
                    self.df[
                        (self.df["confidence_mean"] > 0.8)
                        & (self.df["accuracy"] == 1.0)
                    ]
                ),
                "high_confidence_inaccurate": len(
                    self.df[
                        (self.df["confidence_mean"] > 0.8) & (self.df["accuracy"] < 1.0)
                    ]
                ),
                "low_confidence_accurate": len(
                    self.df[
                        (self.df["confidence_mean"] <= 0.8)
                        & (self.df["accuracy"] == 1.0)
                    ]
                ),
            },
        }

        return accuracy_analysis

    def generate_resource_analysis(self) -> dict:
        """Analyze resource usage patterns."""
        if self.df.empty:
            return {}

        resource_analysis = {
            "cpu_stats": {
                "mean_cpu_usage": self.df["cpu_mean"].mean(),
                "max_cpu_usage": self.df["cpu_mean"].max(),
                "high_cpu_files": self.df[
                    self.df["cpu_mean"] > self.df["cpu_mean"].quantile(0.9)
                ]["filename"].tolist(),
            },
            "memory_stats": {
                "mean_memory_mb": self.df["memory_mean_mb"].mean(),
                "peak_memory_mb": self.df["memory_max_mb"].max(),
                "high_memory_files": self.df[
                    self.df["memory_max_mb"] > self.df["memory_max_mb"].quantile(0.9)
                ]["filename"].tolist(),
            },
            "efficiency_metrics": {
                "time_per_mb": (
                    self.df["mean_time"] / self.df["memory_mean_mb"]
                ).mean(),
                "most_efficient_file": self.df.loc[
                    (self.df["mean_time"] / self.df["memory_mean_mb"]).idxmin(),
                    "filename",
                ]
                if self.df["memory_mean_mb"].min() > 0
                else None,
            },
        }

        return resource_analysis

    def _identify_performance_outliers(self) -> dict:
        """Identify performance outliers using statistical methods."""
        if self.df.empty:
            return {}

        # Calculate z-scores for timing
        mean_time = self.df["mean_time"].mean()
        std_time = self.df["mean_time"].std()

        if std_time == 0:
            return {"outliers": [], "threshold": 0}

        z_scores = abs((self.df["mean_time"] - mean_time) / std_time)
        outlier_threshold = 2.0  # 2 standard deviations

        outliers = self.df[z_scores > outlier_threshold]

        return {
            "outliers": outliers[["filename", "mean_time", "accuracy"]].to_dict(
                "records"
            ),
            "threshold": outlier_threshold,
            "outlier_count": len(outliers),
        }

    def generate_comprehensive_report(self) -> dict:
        """Generate a comprehensive analysis report."""
        return {
            "metadata": self.results_data.get("metadata", {}),
            "summary": self.results_data.get("summary", {}),
            "timing_analysis": self.generate_timing_analysis(),
            "accuracy_analysis": self.generate_accuracy_analysis(),
            "resource_analysis": self.generate_resource_analysis(),
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate performance improvement recommendations based on analysis."""
        recommendations = []

        if self.df.empty:
            return recommendations

        # Check for timing issues
        mean_time = self.df["mean_time"].mean()
        if mean_time > 30:  # More than 30 seconds average
            recommendations.append(
                "Consider using faster Whisper models (tiny.en) for initial processing"
            )

        # Check for accuracy issues
        mean_accuracy = self.df["accuracy"].mean()
        if mean_accuracy < 0.8:
            recommendations.append(
                "Accuracy is below 80% - consider using more accurate Whisper models or adjusting confidence thresholds"
            )

        # Check for memory usage
        max_memory = self.df["memory_max_mb"].max()
        if max_memory > 1000:  # More than 1GB
            recommendations.append(
                "High memory usage detected - consider implementing more aggressive caching strategies"
            )

        # Check for consistency
        time_cv = (
            self.df["mean_time"].std() / self.df["mean_time"].mean()
            if self.df["mean_time"].mean() > 0
            else 0
        )
        if time_cv > 0.5:  # High coefficient of variation
            recommendations.append(
                "High timing variability detected - investigate file-specific performance issues"
            )

        # Check success rate
        mean_success = self.df["success_rate"].mean()
        if mean_success < 0.95:
            recommendations.append(
                "Error rate is high - implement better error handling and recovery mechanisms"
            )

        return recommendations


class PerformanceVisualizer:
    """Create visualizations for performance analysis."""

    def __init__(self, figsize: tuple[int, int] = (12, 8)):
        self.figsize = figsize
        plt.rcParams["figure.figsize"] = figsize
        plt.rcParams["font.size"] = 10

    def plot_timing_distribution(
        self, df: pd.DataFrame, output_path: Path | None = None
    ) -> plt.Figure:
        """Create timing distribution plots."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize)

        # Histogram of processing times
        ax1.hist(
            df["mean_time"], bins=20, alpha=0.7, color="skyblue", edgecolor="black"
        )
        ax1.set_xlabel("Processing Time (seconds)")
        ax1.set_ylabel("Frequency")
        ax1.set_title("Distribution of Processing Times")
        ax1.grid(True, alpha=0.3)

        # Box plot by show
        if len(df["show"].unique()) > 1:
            df.boxplot(column="mean_time", by="show", ax=ax2)
            ax2.set_title("Processing Time by Show")
            ax2.set_xlabel("Show")
            ax2.set_ylabel("Processing Time (seconds)")
        else:
            ax2.text(
                0.5,
                0.5,
                "Single Show Dataset",
                ha="center",
                va="center",
                transform=ax2.transAxes,
            )
            ax2.set_title("Processing Time by Show (Single Show)")

        # Time vs Accuracy scatter
        scatter = ax3.scatter(
            df["mean_time"],
            df["accuracy"],
            alpha=0.6,
            c=df["confidence_mean"],
            cmap="viridis",
        )
        ax3.set_xlabel("Processing Time (seconds)")
        ax3.set_ylabel("Accuracy")
        ax3.set_title("Processing Time vs Accuracy")
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax3, label="Mean Confidence")

        # Timing variability
        ax4.scatter(df["mean_time"], df["time_std"], alpha=0.6)
        ax4.set_xlabel("Mean Processing Time (seconds)")
        ax4.set_ylabel("Time Standard Deviation")
        ax4.set_title("Timing Consistency")
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_accuracy_metrics(
        self, df: pd.DataFrame, output_path: Path | None = None
    ) -> plt.Figure:
        """Create accuracy analysis plots."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize)

        # Accuracy distribution
        accuracy_counts = df["accuracy"].value_counts().sort_index()
        ax1.bar(
            accuracy_counts.index,
            accuracy_counts.values,
            alpha=0.7,
            color="lightgreen",
            edgecolor="black",
        )
        ax1.set_xlabel("Accuracy Score")
        ax1.set_ylabel("Count")
        ax1.set_title("Accuracy Distribution")
        ax1.grid(True, alpha=0.3)

        # F1 Score vs Accuracy
        ax2.scatter(df["accuracy"], df["f1_score"], alpha=0.6)
        ax2.set_xlabel("Accuracy")
        ax2.set_ylabel("F1 Score")
        ax2.set_title("Accuracy vs F1 Score")
        ax2.grid(True, alpha=0.3)

        # Confidence vs Accuracy
        ax3.scatter(
            df["confidence_mean"],
            df["accuracy"],
            alpha=0.6,
            c=df["mean_time"],
            cmap="plasma",
        )
        ax3.set_xlabel("Mean Confidence")
        ax3.set_ylabel("Accuracy")
        ax3.set_title("Confidence vs Accuracy")
        ax3.grid(True, alpha=0.3)
        plt.colorbar(ax3.collections[0], ax=ax3, label="Processing Time (s)")

        # Success rate by show
        if len(df["show"].unique()) > 1:
            success_by_show = (
                df.groupby("show")["accuracy"].mean().sort_values(ascending=False)
            )
            ax4.bar(range(len(success_by_show)), success_by_show.values, alpha=0.7)
            ax4.set_xticks(range(len(success_by_show)))
            ax4.set_xticklabels(success_by_show.index, rotation=45, ha="right")
            ax4.set_ylabel("Mean Accuracy")
            ax4.set_title("Accuracy by Show")
        else:
            ax4.text(
                0.5,
                0.5,
                "Single Show Dataset",
                ha="center",
                va="center",
                transform=ax4.transAxes,
            )
            ax4.set_title("Accuracy by Show (Single Show)")

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_resource_usage(
        self, df: pd.DataFrame, output_path: Path | None = None
    ) -> plt.Figure:
        """Create resource usage visualizations."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize)

        # Memory usage distribution
        ax1.hist(
            df["memory_mean_mb"], bins=20, alpha=0.7, color="coral", edgecolor="black"
        )
        ax1.set_xlabel("Memory Usage (MB)")
        ax1.set_ylabel("Frequency")
        ax1.set_title("Memory Usage Distribution")
        ax1.grid(True, alpha=0.3)

        # CPU vs Memory
        ax2.scatter(df["cpu_mean"], df["memory_mean_mb"], alpha=0.6)
        ax2.set_xlabel("CPU Usage (%)")
        ax2.set_ylabel("Memory Usage (MB)")
        ax2.set_title("CPU vs Memory Usage")
        ax2.grid(True, alpha=0.3)

        # Resource efficiency (time per MB)
        efficiency = df["mean_time"] / df["memory_mean_mb"]
        ax3.scatter(df["memory_mean_mb"], efficiency, alpha=0.6)
        ax3.set_xlabel("Memory Usage (MB)")
        ax3.set_ylabel("Time per MB (s/MB)")
        ax3.set_title("Memory Efficiency")
        ax3.grid(True, alpha=0.3)

        # Resource usage vs accuracy
        scatter = ax4.scatter(
            df["memory_mean_mb"],
            df["accuracy"],
            alpha=0.6,
            c=df["mean_time"],
            cmap="coolwarm",
        )
        ax4.set_xlabel("Memory Usage (MB)")
        ax4.set_ylabel("Accuracy")
        ax4.set_title("Memory Usage vs Accuracy")
        ax4.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax4, label="Processing Time (s)")

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")

        return fig

    def create_performance_dashboard(self, df: pd.DataFrame, output_dir: Path):
        """Create a comprehensive performance dashboard."""
        output_dir.mkdir(exist_ok=True)

        # Generate all plots
        timing_fig = self.plot_timing_distribution(
            df, output_dir / "timing_analysis.png"
        )
        accuracy_fig = self.plot_accuracy_metrics(
            df, output_dir / "accuracy_analysis.png"
        )
        resource_fig = self.plot_resource_usage(
            df, output_dir / "resource_analysis.png"
        )

        # Create summary dashboard
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # Key metrics summary
        ax1.axis("off")
        summary_text = f"""
Performance Summary

Total Files: {len(df)}
Mean Processing Time: {df["mean_time"].mean():.2f}s
Mean Accuracy: {df["accuracy"].mean():.1%}
Mean Memory Usage: {df["memory_mean_mb"].mean():.1f} MB
Success Rate: {df["success_rate"].mean():.1%}

Best File: {df.loc[df["accuracy"].idxmax(), "filename"]}
Fastest File: {df.loc[df["mean_time"].idxmin(), "filename"]}
        """
        ax1.text(
            0.1,
            0.5,
            summary_text,
            fontsize=12,
            verticalalignment="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
        )
        ax1.set_title("Performance Summary", fontsize=16, fontweight="bold")

        # Processing time overview
        ax2.bar(range(len(df)), df["mean_time"], alpha=0.7, color="skyblue")
        ax2.set_xlabel("File Index")
        ax2.set_ylabel("Processing Time (s)")
        ax2.set_title("Processing Time by File")
        ax2.grid(True, alpha=0.3)

        # Accuracy overview
        colors = [
            "green" if acc == 1.0 else "yellow" if acc > 0.5 else "red"
            for acc in df["accuracy"]
        ]
        ax3.bar(range(len(df)), df["accuracy"], alpha=0.7, color=colors)
        ax3.set_xlabel("File Index")
        ax3.set_ylabel("Accuracy")
        ax3.set_title("Accuracy by File")
        ax3.grid(True, alpha=0.3)

        # Performance vs Accuracy scatter
        scatter = ax4.scatter(
            df["mean_time"],
            df["accuracy"],
            s=df["memory_mean_mb"] / 10,
            alpha=0.6,
            c=df["confidence_mean"],
            cmap="viridis",
        )
        ax4.set_xlabel("Processing Time (s)")
        ax4.set_ylabel("Accuracy")
        ax4.set_title("Performance vs Accuracy\n(size=memory, color=confidence)")
        ax4.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax4, label="Mean Confidence")

        plt.tight_layout()
        plt.savefig(
            output_dir / "performance_dashboard.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        # Close other figures to save memory
        plt.close(timing_fig)
        plt.close(accuracy_fig)
        plt.close(resource_fig)


def analyze_benchmark_results(results_path: Path, output_dir: Path = None):
    """Main function to analyze benchmark results and generate reports."""
    console = Console()

    if not results_path.exists():
        console.print(f"[red]Error: Results file not found: {results_path}[/red]")
        return

    if output_dir is None:
        output_dir = results_path.parent / "analysis"

    output_dir.mkdir(exist_ok=True)

    # Load and analyze results
    analyzer = BenchmarkAnalyzer(console)
    analyzer.load_results(results_path)

    if analyzer.df.empty:
        console.print("[red]Error: No valid data found in results file[/red]")
        return

    console.print(
        f"[bold cyan]Analyzing {len(analyzer.df)} test results...[/bold cyan]"
    )

    # Generate comprehensive analysis
    analysis = analyzer.generate_comprehensive_report()

    # Save analysis to JSON
    analysis_path = output_dir / "analysis_report.json"
    with open(analysis_path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    # Generate visualizations
    visualizer = PerformanceVisualizer()
    visualizer.create_performance_dashboard(analyzer.df, output_dir)

    # Display summary
    _display_analysis_summary(analysis, console)

    console.print("[bold green]Analysis complete![/bold green]")
    console.print(f"Reports saved to: {output_dir}")
    console.print(f"- Analysis report: {analysis_path}")
    console.print(f"- Visualizations: {output_dir}/*.png")


def _display_analysis_summary(analysis: dict, console: Console):
    """Display a summary of the analysis results."""
    timing = analysis.get("timing_analysis", {}).get("overall_stats", {})
    accuracy = analysis.get("accuracy_analysis", {}).get("overall_stats", {})
    resource = analysis.get("resource_analysis", {})

    # Summary table
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    if timing:
        table.add_row(
            "Mean Processing Time", f"{timing.get('mean_processing_time', 0):.2f}s"
        )
        table.add_row("Fastest File", timing.get("fastest_file", "N/A"))
        table.add_row("Slowest File", timing.get("slowest_file", "N/A"))

    if accuracy:
        table.add_row("Mean Accuracy", f"{accuracy.get('mean_accuracy', 0):.1%}")
        table.add_row("Perfect Matches", str(accuracy.get("perfect_accuracy_count", 0)))
        table.add_row("Failed Matches", str(accuracy.get("failed_matches_count", 0)))

    if resource:
        cpu_stats = resource.get("cpu_stats", {})
        memory_stats = resource.get("memory_stats", {})
        table.add_row("Mean CPU Usage", f"{cpu_stats.get('mean_cpu_usage', 0):.1f}%")
        table.add_row(
            "Peak Memory Usage", f"{memory_stats.get('peak_memory_mb', 0):.1f} MB"
        )

    console.print(table)

    # Recommendations
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"  {i}. {rec}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze benchmark results")
    parser.add_argument(
        "results_file", type=Path, help="Path to benchmark results JSON file"
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory for analysis")

    args = parser.parse_args()

    analyze_benchmark_results(args.results_file, args.output_dir)
