"""
Baseline ASR Model Loading Time Measurement Script

This script measures the time it takes to:
1. Import required modules
2. Initialize and load the ASR model (Parakeet)
3. Report GPU/CPU availability and loading times
"""
import time
import sys

print("=" * 60)
print("ASR Model Baseline Loading Time Measurement")
print("=" * 60)

# Step 1: Measure import time
print("\n[1/4] Measuring import time...")
import_start = time.perf_counter()

import torch
from loguru import logger
from mkv_episode_matcher.core.models import Config, ConfigManager

import_end = time.perf_counter()
print(f"    Import time: {import_end - import_start:.2f}s")

# Step 2: Check device availability
print("\n[2/4] Checking device availability...")
cuda_available = torch.cuda.is_available()
device_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
print(f"    CUDA available: {cuda_available}")
if cuda_available:
    print(f"    GPU Device: {device_name}")
else:
    print("    Will use CPU mode")

# Step 3: Load configuration
print("\n[3/4] Loading configuration...")
config_start = time.perf_counter()
manager = ConfigManager()
config = manager.config
config_end = time.perf_counter()
print(f"    Config load time: {config_end - config_start:.2f}s")
print(f"    ASR Provider: {config.asr_provider}")
print(f"    ASR Model: {config.asr_model_name}")

# Step 4: Load ASR model
print("\n[4/4] Loading ASR model (this is the slow part)...")
model_start = time.perf_counter()

from mkv_episode_matcher.core.providers.asr import get_asr_provider

asr = get_asr_provider(
    model_type=config.asr_provider,
    model_name=config.asr_model_name,
)
asr.load()

model_end = time.perf_counter()
model_time = model_end - model_start

print(f"    ASR model load time: {model_time:.2f}s")

# Summary
total_time = model_end - import_start
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"    Total startup time: {total_time:.2f}s")
print(f"    ASR model load time: {model_time:.2f}s")
print(f"    Device used: {'CUDA' if cuda_available else 'CPU'}")
print("=" * 60)
