import asyncio
from pathlib import Path

import flet as ft

from mkv_episode_matcher import __version__ as version
from mkv_episode_matcher.core.config_manager import get_config_manager
from mkv_episode_matcher.core.engine import MatchEngine


async def main(page: ft.Page):
    # -- Theme & Page Setup --

    page.title = "MKV Episode Matcher"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 900
    page.window_height = 800
    page.window_min_width = 600
    page.window_min_height = 500

    # Custom Theme
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.DEEP_PURPLE,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    # -- State --
    cm = get_config_manager()
    config = cm.load()
    engine = None  # Will be initialized after model loads

    # Model Status UI
    model_status_icon = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.ORANGE_400, size=12)
    model_status_text = ft.Text("Loading Model...", size=12, color=ft.Colors.GREY_400)

    # We use a simple boolean to track state for the UI,
    # relying on the background task to update it.
    model_ready = False

    # Configuration Dialog placeholder (will be defined later)
    open_config_dialog = None

    # Set up AppBar after model status components are defined
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.MOVIE_FILTER),
        leading_width=40,
        title=ft.Text("MKV Episode Matcher"),
        center_title=True,
        bgcolor=ft.Colors.INVERSE_PRIMARY,
        actions=[
            ft.Row(
                [model_status_icon, model_status_text],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(width=10),
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Configuration",
                on_click=lambda _: open_config_dialog(_)
                if open_config_dialog
                else None,
            ),
            ft.Container(padding=10, content=ft.Text(f"v{version}")),
        ],
    )

    def update_model_status(loaded: bool):
        nonlocal model_ready, engine
        model_ready = loaded
        if loaded:
            model_status_icon.name = ft.Icons.CIRCLE
            model_status_icon.color = ft.Colors.GREEN_400
            model_status_text.value = "Model Ready"
            model_status_text.color = ft.Colors.GREEN_400
            # Initialize engine now that model is loaded
            if engine is None:
                engine = MatchEngine(config)
        else:
            model_status_icon.name = ft.Icons.CIRCLE
            model_status_icon.color = ft.Colors.ORANGE_400
            model_status_text.value = "Loading Model..."
            model_status_text.color = ft.Colors.GREY_400
        page.update()

    # Background loader task
    async def background_load():
        print("Starting background model load...")
        try:
            from mkv_episode_matcher.core.providers.asr import get_asr_provider

            # Update status to show loading progress
            model_status_text.value = "Downloading model..."
            page.update()

            # Load ASR model in executor to prevent blocking UI
            loop = asyncio.get_running_loop()

            # Initialize ASR provider separately
            asr_provider = get_asr_provider(config.asr_provider)

            model_status_text.value = "Loading model..."
            page.update()

            await loop.run_in_executor(None, asr_provider.load)

            print("Background model load complete.")
            update_model_status(True)
        except ImportError as e:
            print(f"Model dependencies not installed: {e}")
            model_status_text.value = "Dependencies Missing"
            model_status_icon.color = ft.Colors.RED_400
            page.update()
        except Exception as e:
            print(f"Background load failed: {e}")
            model_status_text.value = "Model Load Failed"
            model_status_icon.color = ft.Colors.RED_400
            page.update()

    # Start the background task
    page.run_task(background_load)

    # -- Components --

    path_tf = ft.TextField(
        label="Path to Library or MKV Series Folder",
        expand=True,
        border_radius=10,
        prefix_icon=ft.Icons.FOLDER,
        hint_text="Select a folder...",
    )

    season_tf = ft.TextField(
        label="Season Override",
        width=150,
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="Opt. (e.g. 1)",
        border_radius=10,
        prefix_icon=ft.Icons.NUMBERS,
    )

    # Dry run checkbox
    dry_run_cb = ft.Checkbox(
        label="Dry Run (preview only)",
        value=False,
        tooltip="Preview matches without renaming files",
    )

    # List View for Results
    results_lv = ft.ListView(expand=True, spacing=5, padding=ft.Padding.all(15))

    # Progress indicators
    progress_bar = ft.ProgressBar(visible=False, width=400, height=8)
    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
    status_text = ft.Text("Ready", italic=True, color=ft.Colors.GREY_400)
    progress_text = ft.Text("", size=12, color=ft.Colors.GREY_500, visible=False)

    # -- File Picker --
    async def pick_click(_):
        result = await ft.FilePicker().get_directory_path(
            dialog_title="Select MKV file or Series Folder"
        )
        if result:
            path_tf.value = result
            path_tf.update()
            show_snack(f"Selected: {Path(result).name}", ft.Colors.GREEN)

    def show_snack(message: str, color=ft.Colors.GREY_700):
        # Use overlay to show snackbar
        snack = ft.SnackBar(ft.Text(message), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # -- Configuration Dialog --
    def open_config_dialog_impl(_):
        # Config form fields
        cache_dir_tf = ft.TextField(
            label="Cache Directory",
            value=str(config.cache_dir),
            expand=True,
            hint_text="Directory for storing cache and downloaded subtitles",
        )

        confidence_tf = ft.TextField(
            label="Minimum Confidence Threshold",
            value=str(config.min_confidence),
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="0.0 to 1.0 (e.g., 0.7)",
        )

        asr_provider_dd = ft.Dropdown(
            label="ASR Provider",
            value=config.asr_provider,
            options=[
                ft.dropdown.Option("parakeet", "Parakeet (NVIDIA NeMo)"),
            ],
            hint_text="Speech recognition model",
        )

        subtitle_provider_dd = ft.Dropdown(
            label="Subtitle Provider",
            value=config.sub_provider,
            options=[
                ft.dropdown.Option("local", "Local Only"),
                ft.dropdown.Option("opensubtitles", "Local + OpenSubtitles"),
            ],
            hint_text="Where to get reference subtitles",
        )

        # OpenSubtitles fields
        os_api_key_tf = ft.TextField(
            label="OpenSubtitles API Key",
            value=config.open_subtitles_api_key or "",
            hint_text="Required for OpenSubtitles downloads",
            password=True,
        )

        os_username_tf = ft.TextField(
            label="OpenSubtitles Username",
            value=config.open_subtitles_username or "",
            hint_text="Optional but recommended",
        )

        os_password_tf = ft.TextField(
            label="OpenSubtitles Password",
            value=config.open_subtitles_password or "",
            password=True,
            hint_text="Optional but recommended",
        )

        # TMDb field
        tmdb_api_key_tf = ft.TextField(
            label="TMDb API Key",
            value=config.tmdb_api_key or "",
            hint_text="Optional - for episode titles and metadata",
            password=True,
        )

        def save_config(_):
            nonlocal config
            try:
                # Update config object
                config.cache_dir = Path(cache_dir_tf.value)
                config.min_confidence = float(confidence_tf.value)
                config.asr_provider = asr_provider_dd.value
                config.sub_provider = subtitle_provider_dd.value
                config.open_subtitles_api_key = os_api_key_tf.value or None
                config.open_subtitles_username = os_username_tf.value or None
                config.open_subtitles_password = os_password_tf.value or None
                config.tmdb_api_key = tmdb_api_key_tf.value or None

                # Save to file
                cm.save(config)

                # Close dialog and show success
                config_dialog.open = False
                page.update()
                show_snack("Configuration saved successfully!", ft.Colors.GREEN)

                # Reset engine to use new config (model will reload if needed)
                nonlocal engine, model_ready
                engine = None
                model_ready = False
                update_model_status(False)
                page.run_task(background_load)

            except ValueError as e:
                show_snack(f"Invalid value: {str(e)}", ft.Colors.RED_400)
            except Exception as e:
                show_snack(f"Save failed: {str(e)}", ft.Colors.RED_400)

        def cancel_config(_):
            config_dialog.open = False
            page.update()

        config_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Configuration"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("General Settings", weight=ft.FontWeight.BOLD),
                        cache_dir_tf,
                        confidence_tf,
                        asr_provider_dd,
                        subtitle_provider_dd,
                        ft.Divider(),
                        ft.Text("OpenSubtitles Settings", weight=ft.FontWeight.BOLD),
                        os_api_key_tf,
                        os_username_tf,
                        os_password_tf,
                        ft.Divider(),
                        ft.Text("Optional Services", weight=ft.FontWeight.BOLD),
                        tmdb_api_key_tf,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=500,
                height=600,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_config),
                ft.FilledButton("Save", on_click=save_config),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(config_dialog)
        config_dialog.open = True
        page.update()

    # Assign the function to the variable for the AppBar
    open_config_dialog = open_config_dialog_impl

    async def start_process(_):
        if not path_tf.value:
            show_snack("Please select a path", ft.Colors.RED_400)
            return

        if not model_ready or engine is None:
            show_snack("Please wait for model to load...", ft.Colors.ORANGE_400)
            return

        path = Path(path_tf.value)
        if not path.exists():
            show_snack("Path does not exist", ft.Colors.RED_400)
            return

        # UI Reset
        results_lv.controls.clear()
        progress_ring.visible = True
        progress_bar.visible = True
        progress_text.visible = True
        status_text.value = "Starting processing..."
        progress_text.value = "Initializing..."
        progress_bar.value = 0
        page.update()

        # Run processing in executor with progress updates
        loop = asyncio.get_running_loop()

        season_val = None
        if season_tf.value and season_tf.value.isdigit():
            season_val = int(season_tf.value)

        # Progress callback function - more responsive updates
        def update_progress(current, total):
            if total > 0:
                progress_value = current / total
                progress_bar.value = progress_value
                progress_text.value = f"Processing file {current} of {total}"
                status_text.value = f"Processing files... ({current}/{total})"

                # Multiple update attempts for better responsiveness
                try:
                    page.update()
                    # Also try updating individual controls
                    progress_bar.update()
                    progress_text.update()
                    status_text.update()
                except Exception:
                    pass  # Ignore any update errors from background thread

        try:
            # Check dry run mode
            is_dry_run = dry_run_cb.value

            # Add timeout to prevent indefinite hang
            tup = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: engine.process_path(
                        path,
                        season_override=season_val,
                        dry_run=is_dry_run,
                        progress_callback=update_progress,
                    ),
                ),
                timeout=300.0,  # 5 minutes timeout
            )

            # Unpack safely
            if isinstance(tup, tuple) and len(tup) == 2:
                results, failures = tup
            else:
                results = []
                failures = tup if isinstance(tup, list) else []

            # Hide progress indicators and show results
            progress_ring.visible = False
            progress_bar.visible = False
            progress_text.visible = False
            dry_run_text = " (Dry Run)" if is_dry_run else ""
            status_text.value = f"Complete{dry_run_text}: {len(results)} matches, {len(failures)} failures"

            if not results and not failures:
                results_lv.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.Icons.SEARCH_OFF,
                                    size=50,
                                    color=ft.Colors.GREY_700,
                                ),
                                ft.Text(
                                    "No compatible files found to process.",
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=40,
                    )
                )

            # Failures Section
            if failures:
                results_lv.controls.append(
                    ft.Text(
                        "Failures / Ignored",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_200,
                    )
                )
                for fail in failures:
                    card = ft.Card(
                        elevation=1,
                        content=ft.Container(
                            content=ft.Row([
                                ft.Icon(
                                    ft.Icons.ERROR_OUTLINE,
                                    color=ft.Colors.RED_400,
                                    size=16,
                                ),
                                ft.Container(width=8),
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Row([
                                                ft.Text(
                                                    fail.original_file.name,
                                                    weight=ft.FontWeight.W_500,
                                                    size=13,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                    expand=True,
                                                ),
                                                ft.Text(
                                                    f"{fail.series_name} S{fail.season:02d}"
                                                    if fail.series_name and fail.season
                                                    else "",
                                                    color=ft.Colors.RED_200,
                                                    size=11,
                                                    weight=ft.FontWeight.W_600,
                                                )
                                                if fail.series_name and fail.season
                                                else ft.Container(),
                                            ]),
                                            ft.Text(
                                                fail.reason,
                                                color=ft.Colors.RED_300,
                                                size=11,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ],
                                        spacing=2,
                                    ),
                                    expand=True,
                                ),
                            ]),
                            padding=ft.Padding.all(12),
                            bgcolor=ft.Colors.RED_900
                            if page.theme_mode == ft.ThemeMode.DARK
                            else ft.Colors.RED_50,
                        ),
                    )
                    results_lv.controls.append(card)

            # Successes Section
            if results:
                if failures:
                    results_lv.controls.append(ft.Divider())
                results_lv.controls.append(
                    ft.Text(
                        "Matches", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_200
                    )
                )

            for res in results:

                def rename_click(e, r=res):
                    if is_dry_run:
                        # Preview mode - just show what the new name would be
                        try:
                            title_part = (
                                f" - {r.episode_info.title}"
                                if r.episode_info.title
                                else ""
                            )
                            new_filename = f"{r.episode_info.series_name} - {r.episode_info.s_e_format}{title_part}{r.matched_file.suffix}"
                            # Clean filename
                            import re

                            new_filename = re.sub(
                                r'[<>:"/\\\\|?*]', "", new_filename
                            ).strip()
                            show_snack(
                                f"Would rename to: {new_filename}", ft.Colors.BLUE
                            )
                        except Exception as ex:
                            show_snack(f"Preview error: {ex}", ft.Colors.RED)
                    else:
                        # Actual rename mode
                        try:
                            new_path = engine._perform_rename(r)
                            if new_path:
                                e.control.text = "Renamed"
                                e.control.disabled = True
                                e.control.icon = ft.Icons.CHECK
                                show_snack(
                                    f"Renamed to {new_path.name}", ft.Colors.GREEN
                                )
                                e.control.update()
                            else:
                                show_snack("Rename failed", ft.Colors.RED)
                        except Exception as ex:
                            show_snack(f"Rename error: {ex}", ft.Colors.RED)

                # Determine button text and behavior based on dry run mode
                button_text = "Preview Rename" if is_dry_run else "Rename"
                button_icon = (
                    ft.Icons.PREVIEW
                    if is_dry_run
                    else ft.Icons.DRIVE_FILE_RENAME_OUTLINE
                )

                # Compact card design
                card = ft.Card(
                    elevation=2,
                    content=ft.Container(
                        content=ft.Row([
                            # File info section
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row([
                                            ft.Icon(
                                                ft.Icons.MOVIE,
                                                color=ft.Colors.INDIGO_400,
                                                size=16,
                                            ),
                                            ft.Container(width=5),
                                            ft.Container(
                                                content=ft.Text(
                                                    res.matched_file.name,
                                                    weight=ft.FontWeight.W_500,
                                                    size=13,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                ),
                                                expand=True,
                                            ),
                                        ]),
                                        ft.Row([
                                            ft.Text(
                                                f"→ {res.episode_info.s_e_format}",
                                                color=ft.Colors.GREEN_400,
                                                weight=ft.FontWeight.BOLD,
                                                size=12,
                                            ),
                                            ft.Container(width=15),
                                            ft.Text(
                                                f"{res.confidence:.0%}",
                                                size=11,
                                                color=ft.Colors.GREEN_400
                                                if res.confidence > 0.8
                                                else ft.Colors.ORANGE_400,
                                            ),
                                        ]),
                                    ],
                                    spacing=2,
                                ),
                                expand=True,
                            ),
                            # Button section
                            ft.Container(
                                content=ft.ElevatedButton(
                                    button_text,
                                    icon=button_icon,
                                    on_click=rename_click,
                                    style=ft.ButtonStyle(
                                        text_style=ft.TextStyle(size=12),
                                        padding=ft.Padding.symmetric(
                                            horizontal=12, vertical=8
                                        ),
                                    ),
                                ),
                                alignment=ft.Alignment.CENTER,
                            ),
                        ]),
                        padding=ft.Padding.all(12),
                    ),
                )
                results_lv.controls.append(card)

        except asyncio.TimeoutError:
            progress_ring.visible = False
            progress_bar.visible = False
            progress_text.visible = False
            status_text.value = "Processing timed out (5 minutes)"
            show_snack(
                "Processing timed out - try processing fewer files at once",
                ft.Colors.ORANGE_400,
            )
        except FileNotFoundError as e:
            progress_ring.visible = False
            progress_bar.visible = False
            progress_text.visible = False
            status_text.value = "File not found"
            show_snack(f"File not found: {str(e)}", ft.Colors.RED_400)
        except PermissionError as e:
            progress_ring.visible = False
            progress_bar.visible = False
            progress_text.visible = False
            status_text.value = "Permission denied"
            show_snack(f"Permission error: {str(e)}", ft.Colors.RED_400)
        except Exception as e:
            progress_ring.visible = False
            progress_bar.visible = False
            progress_text.visible = False
            status_text.value = f"Error: {str(e)}"
            show_snack(f"Processing error: {str(e)}", ft.Colors.RED_400)
            import traceback

            traceback.print_exc()

        page.update()

    # -- Main Layout --
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Select Media Source", size=16, weight=ft.FontWeight.W_600
                        ),
                        ft.Row(
                            controls=[
                                path_tf,
                                ft.IconButton(
                                    icon=ft.Icons.FOLDER_OPEN,
                                    tooltip="Browse Folder",
                                    icon_size=30,
                                    on_click=pick_click,
                                    icon_color=ft.Colors.INDIGO_300,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Row([
                            season_tf,
                            ft.Container(width=15),
                            dry_run_cb,
                        ]),
                        ft.Container(height=10),
                        ft.FilledButton(
                            "Start Processing",
                            icon=ft.Icons.PLAY_ARROW_ROUNDED,
                            on_click=start_process,
                            style=ft.ButtonStyle(
                                padding=20,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            height=50,
                            expand=True,
                        ),
                        ft.Divider(height=30, thickness=1, color=ft.Colors.GREY_800),
                        ft.Column(
                            [
                                ft.Row([
                                    progress_ring,
                                    ft.Container(width=10),
                                    status_text,
                                ]),
                                progress_bar,
                                progress_text,
                            ],
                            spacing=5,
                        ),
                    ]),
                    padding=20,
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=10,
                ),
                ft.Container(height=10),
                results_lv,
            ]),
            padding=20,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main=main)
