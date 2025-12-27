"""
Enhanced Resource Monitoring for Performance Benchmarking

This module provides comprehensive monitoring of system resources including
CPU, memory, disk I/O, and GPU usage during performance tests.
"""

import queue
import statistics
import threading
import time
from dataclasses import asdict, dataclass

import psutil


@dataclass
class ResourceSnapshot:
    """Single point-in-time resource usage snapshot."""

    timestamp: float
    cpu_percent: float
    cpu_per_core: list[float]
    memory_used_mb: float
    memory_available_mb: float
    memory_percent: float
    disk_read_mb: float
    disk_write_mb: float
    gpu_utilization: float | None = None
    gpu_memory_used_mb: float | None = None
    gpu_memory_total_mb: float | None = None
    gpu_temperature_c: float | None = None


class GPUMonitor:
    """GPU monitoring functionality with graceful fallback."""

    def __init__(self):
        self.gpu_available = False
        self.torch_available = False
        self.nvidia_ml_available = False

        # Try to import and initialize GPU monitoring libraries
        try:
            import torch

            if torch.cuda.is_available():
                self.torch_available = True
                self.device_count = torch.cuda.device_count()
        except ImportError:
            pass

        try:
            import pynvml

            pynvml.nvmlInit()
            self.nvidia_ml_available = True
        except (ImportError, Exception):
            pass

        self.gpu_available = self.torch_available or self.nvidia_ml_available

    def get_gpu_stats(self) -> dict:
        """Get current GPU statistics."""
        if not self.gpu_available:
            return {}

        stats = {}

        # Try PyTorch monitoring first
        if self.torch_available:
            try:
                import torch

                if torch.cuda.is_available():
                    device = torch.cuda.current_device()
                    memory_used = (
                        torch.cuda.memory_allocated(device) / 1024 / 1024
                    )  # MB
                    memory_total = (
                        torch.cuda.get_device_properties(device).total_memory
                        / 1024
                        / 1024
                    )  # MB

                    stats.update({
                        "gpu_memory_used_mb": memory_used,
                        "gpu_memory_total_mb": memory_total,
                        "gpu_memory_percent": (memory_used / memory_total) * 100
                        if memory_total > 0
                        else 0,
                    })
            except Exception:
                pass

        # Try NVIDIA ML for additional metrics
        if self.nvidia_ml_available:
            try:
                import pynvml

                handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Primary GPU

                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                stats["gpu_utilization"] = util.gpu

                # Temperature
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
                stats["gpu_temperature_c"] = temp

                # Memory info (if not already from PyTorch)
                if "gpu_memory_used_mb" not in stats:
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    stats.update({
                        "gpu_memory_used_mb": mem_info.used / 1024 / 1024,
                        "gpu_memory_total_mb": mem_info.total / 1024 / 1024,
                        "gpu_memory_percent": (mem_info.used / mem_info.total) * 100,
                    })
            except Exception:
                pass

        return stats


class EnhancedResourceMonitor:
    """Enhanced resource monitoring with detailed metrics and GPU support."""

    def __init__(self, sampling_interval: float = 0.5):
        self.sampling_interval = sampling_interval
        self.snapshots: list[ResourceSnapshot] = []
        self.monitoring = False
        self.monitor_thread = None
        self.snapshot_queue = queue.Queue()

        # Initialize monitors
        self.process = psutil.Process()
        self.gpu_monitor = GPUMonitor()

        # Baseline measurements
        self.baseline_disk_read = 0
        self.baseline_disk_write = 0

        # Reset CPU percent to get accurate initial reading
        psutil.cpu_percent()
        self.process.cpu_percent()

    def _get_disk_io(self) -> tuple:
        """Get current disk I/O statistics."""
        try:
            io_counters = psutil.disk_io_counters()
            if io_counters:
                return io_counters.read_bytes, io_counters.write_bytes
        except Exception:
            pass
        return 0, 0

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a single resource usage snapshot."""
        timestamp = time.perf_counter()

        # CPU metrics
        cpu_percent = self.process.cpu_percent()
        cpu_per_core = psutil.cpu_percent(percpu=True)

        # Memory metrics
        memory_info = self.process.memory_info()
        virtual_memory = psutil.virtual_memory()

        memory_used_mb = memory_info.rss / 1024 / 1024
        memory_available_mb = virtual_memory.available / 1024 / 1024
        memory_percent = virtual_memory.percent

        # Disk I/O metrics
        disk_read, disk_write = self._get_disk_io()
        disk_read_mb = (disk_read - self.baseline_disk_read) / 1024 / 1024
        disk_write_mb = (disk_write - self.baseline_disk_write) / 1024 / 1024

        # GPU metrics
        gpu_stats = self.gpu_monitor.get_gpu_stats()

        return ResourceSnapshot(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            cpu_per_core=cpu_per_core,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            memory_percent=memory_percent,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb,
            gpu_utilization=gpu_stats.get("gpu_utilization"),
            gpu_memory_used_mb=gpu_stats.get("gpu_memory_used_mb"),
            gpu_memory_total_mb=gpu_stats.get("gpu_memory_total_mb"),
            gpu_temperature_c=gpu_stats.get("gpu_temperature_c"),
        )

    def _monitor_loop(self):
        """Main monitoring loop running in separate thread."""
        while self.monitoring:
            try:
                snapshot = self._take_snapshot()
                self.snapshot_queue.put(snapshot)
                time.sleep(self.sampling_interval)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.sampling_interval)

    def start(self):
        """Start resource monitoring."""
        if self.monitoring:
            return

        # Record baseline disk I/O
        self.baseline_disk_read, self.baseline_disk_write = self._get_disk_io()

        # Clear any existing snapshots
        self.snapshots.clear()
        while not self.snapshot_queue.empty():
            self.snapshot_queue.get()

        # Start monitoring
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self) -> dict:
        """Stop monitoring and return summary statistics."""
        if not self.monitoring:
            return {}

        self.monitoring = False

        # Wait for thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        # Collect all snapshots from queue
        while not self.snapshot_queue.empty():
            snapshot = self.snapshot_queue.get()
            self.snapshots.append(snapshot)

        if not self.snapshots:
            return {}

        return self._calculate_summary_statistics()

    def _calculate_summary_statistics(self) -> dict:
        """Calculate summary statistics from collected snapshots."""
        if not self.snapshots:
            return {}

        # Extract time series data
        cpu_percents = [s.cpu_percent for s in self.snapshots]
        memory_used_mbs = [s.memory_used_mb for s in self.snapshots]
        memory_percents = [s.memory_percent for s in self.snapshots]
        disk_reads = [s.disk_read_mb for s in self.snapshots]
        disk_writes = [s.disk_write_mb for s in self.snapshots]

        # GPU metrics (may be None)
        gpu_utilizations = [
            s.gpu_utilization for s in self.snapshots if s.gpu_utilization is not None
        ]
        gpu_memory_used = [
            s.gpu_memory_used_mb
            for s in self.snapshots
            if s.gpu_memory_used_mb is not None
        ]
        gpu_temperatures = [
            s.gpu_temperature_c
            for s in self.snapshots
            if s.gpu_temperature_c is not None
        ]

        duration = self.snapshots[-1].timestamp - self.snapshots[0].timestamp

        summary = {
            "duration_seconds": duration,
            "sample_count": len(self.snapshots),
            "sampling_rate": len(self.snapshots) / duration if duration > 0 else 0,
            "cpu": {
                "mean_percent": statistics.mean(cpu_percents),
                "max_percent": max(cpu_percents),
                "min_percent": min(cpu_percents),
                "std_percent": statistics.stdev(cpu_percents)
                if len(cpu_percents) > 1
                else 0,
            },
            "memory": {
                "mean_used_mb": statistics.mean(memory_used_mbs),
                "max_used_mb": max(memory_used_mbs),
                "min_used_mb": min(memory_used_mbs),
                "mean_percent": statistics.mean(memory_percents),
                "max_percent": max(memory_percents),
            },
            "disk_io": {
                "total_read_mb": max(disk_reads) if disk_reads else 0,
                "total_write_mb": max(disk_writes) if disk_writes else 0,
                "read_rate_mb_per_sec": max(disk_reads) / duration
                if duration > 0 and disk_reads
                else 0,
                "write_rate_mb_per_sec": max(disk_writes) / duration
                if duration > 0 and disk_writes
                else 0,
            },
        }

        # Add GPU stats if available
        if gpu_utilizations:
            summary["gpu"] = {
                "mean_utilization_percent": statistics.mean(gpu_utilizations),
                "max_utilization_percent": max(gpu_utilizations),
                "min_utilization_percent": min(gpu_utilizations),
            }

        if gpu_memory_used:
            summary.setdefault("gpu", {}).update({
                "mean_memory_used_mb": statistics.mean(gpu_memory_used),
                "max_memory_used_mb": max(gpu_memory_used),
                "memory_total_mb": self.snapshots[-1].gpu_memory_total_mb,
            })

        if gpu_temperatures:
            summary.setdefault("gpu", {}).update({
                "mean_temperature_c": statistics.mean(gpu_temperatures),
                "max_temperature_c": max(gpu_temperatures),
            })

        return summary

    def get_system_info(self) -> dict:
        """Get static system information."""
        cpu_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        }

        memory_info = psutil.virtual_memory()
        memory = {
            "total_gb": memory_info.total / 1024 / 1024 / 1024,
            "available_gb": memory_info.available / 1024 / 1024 / 1024,
            "percent_used": memory_info.percent,
        }

        system_info = {
            "cpu": cpu_info,
            "memory": memory,
            "gpu_available": self.gpu_monitor.gpu_available,
            "platform": psutil.platform,
        }

        # Add GPU information if available
        if self.gpu_monitor.gpu_available:
            try:
                if self.gpu_monitor.torch_available:
                    import torch

                    system_info["gpu"] = {
                        "device_count": torch.cuda.device_count(),
                        "current_device": torch.cuda.current_device(),
                        "device_name": torch.cuda.get_device_name(),
                        "cuda_version": torch.version.cuda,
                    }
            except Exception:
                pass

        return system_info

    def get_raw_snapshots(self) -> list[dict]:
        """Get raw snapshot data for detailed analysis."""
        return [asdict(snapshot) for snapshot in self.snapshots]


class ResourceProfiler:
    """Simple context manager for profiling resource usage of code blocks."""

    def __init__(self, sampling_interval: float = 0.1):
        self.monitor = EnhancedResourceMonitor(sampling_interval)
        self.results = None

    def __enter__(self):
        self.monitor.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.results = self.monitor.stop()

    def get_results(self) -> dict:
        """Get profiling results."""
        return self.results or {}


# Convenience function for quick profiling
def profile_resources(func, *args, sampling_interval=0.1, **kwargs):
    """Profile resource usage of a function call."""
    with ResourceProfiler(sampling_interval) as profiler:
        result = func(*args, **kwargs)

    return result, profiler.get_results()
