#!/usr/bin/env python3
"""
Build script for creating cross-platform executables using Flet.

This script automates the process of building desktop applications for
Windows, Linux, and macOS platforms.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str):
    """Run a command and handle errors."""
    print(f"🔨 {description}")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def build_for_platform(platform: str):
    """Build executable for specific platform."""
    print(f"\n{'=' * 50}")
    print(f"Building for {platform.upper()}")
    print(f"{'=' * 50}")

    command = [
        sys.executable,
        "-m",
        "flet",
        "pack",
        "--target-platform",
        platform,
        "mkv_episode_matcher/ui/flet_app.py",
    ]

    return run_command(command, f"Building {platform} executable")


def main():
    """Main build script."""
    print("🚀 MKV Episode Matcher - Executable Build Script")
    print("Building desktop applications for multiple platforms...")

    # Check if flet is installed
    try:
        import flet

        print(f"✅ Flet {flet.__version__} is installed")
    except ImportError:
        print("❌ Flet is not installed. Please run: pip install flet")
        sys.exit(1)

    # Check if we're in the right directory
    if not Path("mkv_episode_matcher").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    platforms = ["windows", "linux", "macos"]
    results = {}

    for platform in platforms:
        print(f"\n📦 Starting build for {platform}...")
        results[platform] = build_for_platform(platform)

    # Summary
    print(f"\n{'=' * 50}")
    print("BUILD SUMMARY")
    print(f"{'=' * 50}")

    success_count = 0
    for platform, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{platform.upper():10} {status}")
        if success:
            success_count += 1

    print(f"\nBuilds completed: {success_count}/{len(platforms)}")

    if success_count > 0:
        print("\n📁 Built executables can be found in:")
        print("   - dist/ directory")
        print("\n💡 Note: Cross-platform builds may require platform-specific tools")
        print("   Consider building on native platforms for best results")

    if success_count < len(platforms):
        print("\n⚠️  Some builds failed. This is normal when cross-compiling.")
        print("   Build on the target platform for best compatibility.")


if __name__ == "__main__":
    main()
