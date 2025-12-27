#!/usr/bin/env python3
"""
Entry point for Flet desktop application build.

This file is required by the Flet build system to properly create desktop executables.
It simply imports and runs the main Flet application.
"""

import flet as ft
from mkv_episode_matcher.ui.flet_app import main

if __name__ == "__main__":
    ft.app(main)