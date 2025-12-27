# Performance Testing Framework

A comprehensive performance testing and analysis framework for the MKV Episode Matcher, designed to assess timing, accuracy, and resource usage of the file matching algorithm.

## Overview

This framework provides:

- **Performance Benchmarking**: Measure inference time, accuracy, and resource usage
- **Model Comparison**: Compare different Whisper models (tiny.en, base.en, small.en, etc.)
- **Resource Monitoring**: Track CPU, GPU, and memory usage during processing  
- **Detailed Profiling**: Function-level performance analysis with cProfile and memory profiling
- **Comprehensive Analysis**: Statistical analysis and visualization of results
- **Optimization Insights**: Identify bottlenecks and optimization opportunities

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r perf-test/requirements.txt
   ```

2. **Verify Framework**
   ```bash
   python perf-test/test_framework.py
   ```

3. **Run Basic Benchmark**
   ```bash
   python perf-test/performance_benchmark.py
   ```

4. **Analyze Results**
   ```bash
   python perf-test/analysis.py perf-test/reports/benchmark_report_YYYYMMDD_HHMMSS.json
   ```

## Framework Components

### Core Components

- **`performance_benchmark.py`** - Main benchmark runner
- **`ground_truth.json`** - Test file definitions and expected results
- **`config.yaml`** - Configurable test parameters
- **`resource_monitor.py`** - System resource monitoring
- **`profiler.py`** - Detailed profiling tools
- **`analysis.py`** - Results analysis and visualization
- **`model_comparison.py`** - Model performance comparison

### Test Data

The framework includes test files from different TV series:
- House of the Dragon - S01E01.mkv
- Rick and Morty - S01E01.mkv  
- Seinfeld - S1E01.mkv
- South Park - s05e01.mkv
- Star Trek: The Next Generation - S01E02.mkv
- The Expanse - S01E01.mkv

## Usage Examples

### Basic Performance Test

Run the standard benchmark with default settings:

```bash
python performance_benchmark.py
```

This will:
- Test all files in `inputs/` directory
- Run 3 iterations per file for statistical accuracy
- Measure timing, accuracy, and resource usage
- Generate comprehensive reports in `reports/`

### Custom Configuration

Modify `config.yaml` to customize test parameters:

```yaml
# Example custom configuration
iterations: 5  # More iterations for better statistics
whisper_models:
  - "tiny.en"     # Fast but less accurate
  - "base.en"     # Balanced
  - "small.en"    # Slower but more accurate

confidence_threshold: 0.7  # Higher confidence requirement
enable_profiling: true     # Detailed function profiling
```

### Model Comparison

Compare different Whisper models and configurations:

```bash
python model_comparison.py
```

This generates:
- Speed vs accuracy trade-off analysis
- Resource usage comparison
- Pareto frontier optimization
- Configuration recommendations

### Analysis and Visualization

Analyze existing benchmark results:

```bash
python analysis.py results/benchmark_report_20241201_143022.json --output-dir analysis_output/
```

Generates:
- Performance dashboard
- Timing distribution plots  
- Accuracy analysis charts
- Resource usage visualizations
- Optimization recommendations

## Output Reports

The framework generates several types of reports:

### Benchmark Reports (`reports/`)

- **JSON Report** - Detailed machine-readable results
- **CSV Export** - Spreadsheet-compatible data
- **Profile Reports** - Function-level performance analysis

### Analysis Reports (`analysis/`)

- **Performance Dashboard** - Visual summary charts
- **Timing Analysis** - Processing time distributions
- **Accuracy Metrics** - Success rates and confidence analysis  
- **Resource Usage** - CPU, memory, and GPU utilization
- **Optimization Recommendations** - Data-driven improvement suggestions

### Model Comparison (`model_comparison_results/`)

- **Speed vs Accuracy Plots** - Trade-off visualization
- **Configuration Impact** - Parameter sensitivity analysis
- **Pareto Frontier** - Optimal configuration identification
- **Detailed Recommendations** - Use-case specific model selection

## Performance Metrics

### Timing Metrics
- **Overall inference time** - End-to-end processing duration
- **Component breakdown** - Time spent in audio extraction, speech recognition, text matching
- **Statistical analysis** - Mean, median, standard deviation, outliers

### Accuracy Metrics  
- **True Positives (TP)** - Correctly identified episodes
- **False Positives (FP)** - Incorrectly matched episodes
- **False Negatives (FN)** - Missed correct episodes
- **Precision, Recall, F1-Score** - Standard classification metrics
- **Confidence distribution** - Matching confidence analysis

### Resource Usage
- **CPU utilization** - Per-core and average usage
- **Memory consumption** - Peak and average RAM usage  
- **GPU metrics** - Utilization and VRAM usage (if available)
- **Disk I/O** - Audio chunk extraction overhead

## Configuration Options

### Test Parameters

```yaml
iterations: 3                    # Repetitions per test
timeout_seconds: 120             # Max time per test
confidence_threshold: 0.6        # Minimum match confidence
whisper_models: ["tiny.en", "base.en"]  # Models to test
```

### Performance Monitoring

```yaml
enable_profiling: true           # Detailed function profiling
resource_monitoring_interval: 0.5  # Resource sampling rate
include_raw_profiles: true       # Include cProfile output
```

### Advanced Options

```yaml
experimental:
  parallel_processing:
    enabled: true                # Test parallel processing
    max_workers: 2              # Number of parallel workers
  
  memory_optimization:
    enabled: true                # Test memory optimizations  
    clear_cache_between_tests: true
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **GPU Monitoring Issues**  
   ```bash
   # Install NVIDIA ML Python bindings
   pip install pynvml
   ```

3. **Memory Errors**
   ```yaml
   # Reduce iterations in config.yaml
   iterations: 1
   enable_profiling: false
   ```

4. **Permission Errors**
   - Ensure write access to `reports/` directory
   - Check cache directory permissions

### Validation

Run the framework validation test:

```bash
python test_framework.py
```

This checks:
- ✅ Dependencies installation
- ✅ Configuration loading
- ✅ Test file accessibility  
- ✅ Resource monitoring
- ✅ Profiling functionality
- ✅ Analysis tools

## Adding New Test Files

1. **Add MKV files** to `inputs/` directory

2. **Update ground truth** in `ground_truth.json`:
   ```json
   {
     "filename": "New Show - S01E01.mkv", 
     "show_name": "New Show",
     "season": 1,
     "episode": 1,
     "expected_format": "New Show - S01E01.mkv"
   }
   ```

3. **Run benchmarks** with updated test set

## Performance Optimization Insights

The framework helps identify optimization opportunities:

### Model Selection
- **tiny.en**: 3-5x faster, ~75% accuracy - good for real-time processing
- **base.en**: Balanced performance, ~85% accuracy - recommended default
- **small.en**: 2x slower, ~90% accuracy - for high-accuracy requirements

### Configuration Tuning
- **Confidence threshold**: Lower values increase recall, higher values improve precision
- **Chunk duration**: Longer chunks improve accuracy but increase processing time
- **Skip duration**: Affects initial processing delay vs accuracy trade-off

### Resource Optimization  
- **Memory usage**: Peaks during audio extraction and model loading
- **CPU utilization**: Highest during Whisper inference
- **GPU acceleration**: Significant speedup when available and properly configured

## Integration with Development Workflow

### Performance Regression Testing
```bash
# Run before/after performance comparison
python model_comparison.py --baseline baseline_results.json
```

### Continuous Integration
```bash
# Quick performance check
python performance_benchmark.py --quick --max-time 30
```

### Optimization Workflow
1. Run full benchmark to establish baseline
2. Implement performance improvements  
3. Run comparison to measure impact
4. Analyze results and iterate

## Contributing

When adding new features:

1. **Update ground truth** for new test scenarios
2. **Add configuration options** to `config.yaml`  
3. **Extend analysis tools** for new metrics
4. **Update documentation** with usage examples
5. **Test framework** with `test_framework.py`

## License

This performance testing framework is part of the MKV Episode Matcher project and follows the same license terms.