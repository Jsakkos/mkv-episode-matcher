import sys
from pathlib import Path

import flet as ft
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))


def test_flet_attributes():
    print(f"Testing Flet version: {ft.version}")

    # Check for Colors class (used in app)
    assert hasattr(ft, "Colors"), "ft.Colors missing"
    print("PASS: ft.Colors exists")

    # Check for FileDropEvent - optional/missing in this version
    if not hasattr(ft, "FileDropEvent"):
        print("INFO: ft.FileDropEvent missing (Expected for this version)")
    else:
        print("PASS: ft.FileDropEvent exists")


def test_components():
    print("Testing component instantiation...")
    try:
        # Test TextField
        tf = ft.TextField(label="Test", expand=True, border_color=ft.Colors.BLUE_400)
        print("PASS: TextField instantiated")

        # Test FilePicker - checks the fix (no args in init)
        fp = ft.FilePicker()
        fp.on_result = lambda e: None
        print("PASS: FilePicker instantiated and handler assigned")

    except Exception as e:
        pytest.fail(f"Component instantiation error - {e}")


def test_app_import():
    try:
        from mkv_episode_matcher.ui import flet_app

        print("PASS: mkv_episode_matcher.ui.flet_app imported successfully")

        # Check if main exists
        assert hasattr(flet_app, "main"), "flet_app.main missing"
        print("PASS: flet_app.main exists")

    except ImportError as e:
        pytest.fail(f"Import error - {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error - {e}")


if __name__ == "__main__":
    test_flet_attributes()
    test_components()
    test_app_import()
