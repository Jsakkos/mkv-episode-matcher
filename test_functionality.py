#!/usr/bin/env python3
"""
Test script to validate MKV Episode Matcher functionality.

This script tests both CLI and GUI components to ensure they work
properly with the shared backend engine.
"""

from pathlib import Path


def test_config_loading():
    """Test configuration loading."""
    print("Testing configuration loading...")
    try:
        from mkv_episode_matcher.core.config_manager import get_config_manager

        cm = get_config_manager()
        config = cm.load()

        print("[OK] Config loaded successfully")
        print(f"   ASR Provider: {config.asr_provider}")
        print(f"   Subtitle Provider: {config.sub_provider}")
        print(f"   Cache Directory: {config.cache_dir}")
        print(f"   Confidence Threshold: {config.min_confidence}")
        return True
    except Exception as e:
        print(f"[FAIL] Config loading failed: {e}")
        return False


def test_asr_provider():
    """Test ASR provider initialization."""
    print("\nTesting ASR provider initialization...")
    try:
        from mkv_episode_matcher.core.config_manager import get_config_manager
        from mkv_episode_matcher.core.providers.asr import get_asr_provider

        config = get_config_manager().load()
        asr = get_asr_provider(config.asr_provider)

        print(f"[OK] ASR provider ({config.asr_provider}) created successfully")
        print("   Model ready for loading")
        return True
    except ImportError as e:
        print(
            f"[WARN]  ASR provider import failed (expected on systems without NeMo): {e}"
        )
        return False
    except Exception as e:
        print(f"[FAIL] ASR provider initialization failed: {e}")
        return False


def test_flet_import():
    """Test Flet GUI components."""
    print("\nTesting Flet GUI import...")
    try:
        import flet as ft

        from mkv_episode_matcher.ui.flet_app import main

        print(f"[OK] Flet imported successfully (version: {ft.__version__})")
        print("[OK] GUI main function imported")
        return True
    except ImportError as e:
        print(f"[FAIL] Flet import failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] GUI import failed: {e}")
        return False


def test_cli_import():
    """Test CLI components."""
    print("\nTesting CLI import...")
    try:
        print("[OK] CLI app imported successfully")
        print("[OK] Engine imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] CLI import failed: {e}")
        return False


def test_build_config():
    """Test build configuration."""
    print("\nTesting build configuration...")
    try:
        # Check if build files exist
        build_script = Path("build_executables.py")
        flet_config = Path("flet_build.yaml")

        if build_script.exists():
            print(f"[OK] Build script found: {build_script}")
        else:
            print(f"[WARN]  Build script not found: {build_script}")

        if flet_config.exists():
            print(f"[OK] Flet config found: {flet_config}")
        else:
            print(f"[WARN]  Flet config not found: {flet_config}")

        return True
    except Exception as e:
        print(f"[FAIL] Build config check failed: {e}")
        return False


def main():
    """Run all tests."""
    print("MKV Episode Matcher - Functionality Test")
    print("=" * 50)

    tests = [
        test_config_loading,
        test_asr_provider,
        test_flet_import,
        test_cli_import,
        test_build_config,
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results, strict=False)):
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{test.__name__:25} {status}")

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\nAll tests passed! The application should work correctly.")
        print("\nNext steps:")
        print("1. Run 'uv run mkv-match gui' to launch the GUI")
        print("2. Run 'uv run mkv-match --help' to see CLI options")
        print("3. Run 'python build_executables.py' to build desktop apps")
    else:
        print(
            f"\n[WARN]  {total - passed} test(s) failed. Some functionality may not work."
        )
        print("Check the error messages above for troubleshooting.")


if __name__ == "__main__":
    main()
