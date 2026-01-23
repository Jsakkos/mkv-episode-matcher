"""
Quick script to test if FFmpeg is properly installed and accessible.
Run this to diagnose FFmpeg installation issues on Windows.
"""
import subprocess
import sys
from pathlib import Path


def test_command(cmd: str) -> tuple[bool, str]:
    """Test if a command is available in PATH."""
    try:
        result = subprocess.run(
            [cmd, "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Get first line of output (version info)
            version = result.stdout.split('\n')[0]
            return True, version
        else:
            return False, f"Command failed with exit code {result.returncode}"
    except FileNotFoundError:
        return False, "Command not found in PATH"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    print("=" * 70)
    print("FFmpeg Installation Test for mkv-episode-matcher")
    print("=" * 70)
    print()

    # Test ffmpeg
    print("[1/2] Testing 'ffmpeg' command...")
    ffmpeg_ok, ffmpeg_msg = test_command("ffmpeg")
    if ffmpeg_ok:
        print(f"    ✓ FFmpeg found: {ffmpeg_msg}")
    else:
        print(f"    ✗ FFmpeg NOT found: {ffmpeg_msg}")
    print()

    # Test ffprobe
    print("[2/2] Testing 'ffprobe' command...")
    ffprobe_ok, ffprobe_msg = test_command("ffprobe")
    if ffprobe_ok:
        print(f"    ✓ FFprobe found: {ffprobe_msg}")
    else:
        print(f"✗ FFprobe NOT found: {ffprobe_msg}")
    print()

    # Summary
    print("=" * 70)
    if ffmpeg_ok and ffprobe_ok:
        print("✓ SUCCESS: FFmpeg is properly installed and accessible!")
        print()
        print("You can now use mkv-episode-matcher.")
        return 0
    else:
        print("✗ PROBLEM: FFmpeg is not properly installed or not in PATH")
        print()
        print("How to fix this on Windows:")
        print()
        print("Option 1: Install via winget (recommended)")
        print("  1. Open PowerShell or Command Prompt as Administrator")
        print("  2. Run: winget install Gyan.FFmpeg")
        print("  3. Restart your terminal/IDE")
        print("  4. Run this script again to verify")
        print()
        print("Option 2: Install via Chocolatey")
        print("  1. Install Chocolatey: https://chocolatey.org/install")
        print("  2. Run: choco install ffmpeg")
        print("  3. Restart your terminal/IDE")
        print()
        print("Option 3: Manual installation")
        print("  1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/")
        print("  2. Extract to C:\\ffmpeg (or another location)")
        print("  3. Add C:\\ffmpeg\\bin to your PATH environment variable:")
        print("     - Search 'Environment Variables' in Windows Start")
        print("     - Edit 'Path' in System Variables")
        print("     - Add the path to ffmpeg\\bin folder")
        print("     - Click OK and restart your terminal/IDE")
        print()
        print("After installation, you MUST restart your terminal/IDE for PATH")
        print("changes to take effect.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
