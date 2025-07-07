"""
TUI Application for MKV Episode Matcher using Textual.
"""

from pathlib import Path
from typing import Optional, List
import asyncio
import threading
import time
import re
import shutil

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, Header, Footer, Static, Input, Checkbox, 
    ProgressBar, DataTable, DirectoryTree, TabbedContent, 
    TabPane, Label, Switch, Select
)
from textual.screen import Screen
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from textual.validation import Function, Number
# Using threading instead of textual workers for compatibility

from mkv_episode_matcher import __version__
from mkv_episode_matcher.config import get_config, set_config
from mkv_episode_matcher.__main__ import CONFIG_FILE, CACHE_DIR
from mkv_episode_matcher.utils import (
    get_valid_seasons, check_filename, clean_text, 
    normalize_path, rename_episode_file, get_subtitles
)
from mkv_episode_matcher.episode_identification import EpisodeMatcher
from mkv_episode_matcher.tmdb_client import fetch_show_id
import os


class WelcomeScreen(Screen):
    """Welcome screen with main navigation options."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "configure", "Configure"),
        Binding("b", "browse", "Browse"),
        Binding("r", "recent", "Recent"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"MKV Episode Matcher v{__version__}", id="title"),
            Static("Automatically match and rename your MKV TV episodes", id="subtitle"),
            Horizontal(
                Button("⚙️ Configure Settings", id="configure_btn", variant="primary"),
                Button("📁 Browse Shows", id="browse_btn", variant="success"),
                Button("🚀 Quick Match", id="quick_btn", variant="warning"),
                id="main_buttons"
            ),
            Container(
                Static("📊 Recent Activity", id="recent_title"),
                DataTable(id="recent_table"),
                id="recent_container"
            ),
            id="welcome_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Load recent activity data."""
        table = self.query_one("#recent_table", DataTable)
        table.add_columns("Show", "Season", "Status", "Episodes")
        # TODO: Load actual recent activity from logs/config
        table.add_row("Breaking Bad", "Season 1", "✓ Complete", "12/12")
        table.add_row("Better Call Saul", "Season 2", "⚠️ Partial", "8/10")
        table.add_row("The Wire", "Season 3", "🔄 Processing", "5/13")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "configure_btn":
            self.action_configure()
        elif event.button.id == "browse_btn":
            self.action_browse()
        elif event.button.id == "quick_btn":
            self.action_quick_match()
    
    def action_configure(self) -> None:
        """Switch to configuration screen."""
        self.app.push_screen(ConfigScreen())
    
    def action_browse(self) -> None:
        """Switch to browse screen."""
        self.app.push_screen(BrowseScreen())
    
    def action_quick_match(self) -> None:
        """Start quick match process."""
        config = get_config(CONFIG_FILE)
        show_dir = config.get("show_dir")
        self.notify(f"Config show_dir: {show_dir}")
        
        if show_dir and Path(show_dir).exists():
            self.notify(f"Using configured show directory: {show_dir}")
            self.app.push_screen(ProcessingScreen(show_dir))
        else:
            self.notify("No configured show directory, opening browser")
            # For testing, let's create a dummy processing screen
            test_dir = "/tmp/test_show"
            self.notify(f"Testing with dummy directory: {test_dir}")
            # Enable get_subs for testing so it bypasses the reference file check
            self.app.push_screen(ProcessingScreen(test_dir, dry_run=True, get_subs=True))
    
    def action_recent(self) -> None:
        """Focus on recent activity."""
        self.query_one("#recent_table").focus()


class ConfigScreen(Screen):
    """Configuration screen for API keys and settings."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+s", "save", "Save"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("⚙️ Configuration", id="config_title"),
            Vertical(
                Label("TMDb API Key:"),
                Input(placeholder="Enter your TMDb API key", id="tmdb_key"),
                Label("OpenSubtitles API Key:"),
                Input(placeholder="Enter your OpenSubtitles API key", id="os_key"),
                Label("User Agent:"),
                Input(value=f"MKV Episode Matcher v{__version__}", id="user_agent"),
                Label("Username:"),
                Input(placeholder="OpenSubtitles username", id="username"),
                Label("Password:"),
                Input(placeholder="OpenSubtitles password", password=True, id="password"),
                Label("Default Show Directory:"),
                Horizontal(
                    Input(placeholder="/path/to/shows", id="show_dir"),
                    Button("Browse...", id="browse_dir"),
                ),
                Label("Confidence Threshold:"),
                Input(value="0.7", id="confidence", validators=[Number(minimum=0.0, maximum=1.0)]),
                Horizontal(
                    Checkbox("Enable GPU", id="gpu_enabled"),
                    Checkbox("Verbose Mode", id="verbose"),
                    Checkbox("Dry Run", id="dry_run"),
                ),
                id="config_form"
            ),
            Horizontal(
                Button("Save Configuration", id="save_btn", variant="success"),
                Button("Test Connection", id="test_btn", variant="primary"),
                Button("Reset to Defaults", id="reset_btn", variant="error"),
                id="config_buttons"
            ),
            id="config_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Load current configuration."""
        config = get_config(CONFIG_FILE)
        
        # Populate form fields
        self.query_one("#tmdb_key", Input).value = config.get("tmdb_api_key", "")
        self.query_one("#os_key", Input).value = config.get("open_subtitles_api_key", "")
        self.query_one("#user_agent", Input).value = config.get("open_subtitles_user_agent", f"MKV Episode Matcher v{__version__}")
        self.query_one("#username", Input).value = config.get("open_subtitles_username", "")
        self.query_one("#password", Input).value = config.get("open_subtitles_password", "")
        self.query_one("#show_dir", Input).value = config.get("show_dir", "")
        self.query_one("#confidence", Input).value = config.get("confidence", "0.7")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save_btn":
            self.action_save()
        elif event.button.id == "test_btn":
            self.action_test()
        elif event.button.id == "reset_btn":
            self.action_reset()
        elif event.button.id == "browse_dir":
            self.action_browse_dir()
    
    def action_save(self) -> None:
        """Save configuration."""
        # Get form values
        tmdb_key = self.query_one("#tmdb_key", Input).value
        os_key = self.query_one("#os_key", Input).value
        user_agent = self.query_one("#user_agent", Input).value
        username = self.query_one("#username", Input).value
        password = self.query_one("#password", Input).value
        show_dir = self.query_one("#show_dir", Input).value
        
        # Save configuration
        set_config(
            tmdb_key, os_key, user_agent, username, password, show_dir, CONFIG_FILE
        )
        
        self.notify("Configuration saved successfully!")
    
    def action_test(self) -> None:
        """Test API connections."""
        # TODO: Implement API connection testing
        self.notify("Testing connections... (not implemented yet)")
    
    def action_reset(self) -> None:
        """Reset to default values."""
        self.query_one("#tmdb_key", Input).value = ""
        self.query_one("#os_key", Input).value = ""
        self.query_one("#user_agent", Input).value = f"MKV Episode Matcher v{__version__}"
        self.query_one("#username", Input).value = ""
        self.query_one("#password", Input).value = ""
        self.query_one("#show_dir", Input).value = ""
        self.query_one("#confidence", Input).value = "0.7"
        self.notify("Configuration reset to defaults")
    
    def action_browse_dir(self) -> None:
        """Browse for show directory."""
        # TODO: Implement directory browser
        self.notify("Directory browser not implemented yet")
    
    def action_back(self) -> None:
        """Go back to welcome screen."""
        self.app.pop_screen()


class BrowseScreen(Screen):
    """Browse and select show directories."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("enter", "select", "Select"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📁 Show Browser", id="browse_title"),
            Horizontal(
                DirectoryTree("/", id="dir_tree"),
                Vertical(
                    Static("Selected Show:", id="selected_label"),
                    DataTable(id="seasons_table"),
                    Horizontal(
                        Button("Process Selected", id="process_btn", variant="success"),
                        Button("Get Subtitles", id="subs_btn", variant="primary"),
                        Button("Settings", id="settings_btn"),
                    ),
                    id="details_panel"
                ),
                id="browse_content"
            ),
            id="browse_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the browse screen."""
        # Setup seasons table
        table = self.query_one("#seasons_table", DataTable)
        table.add_columns("Season", "Episodes", "Status")
        
        # Load default directory if available
        config = get_config(CONFIG_FILE)
        show_dir = config.get("show_dir")
        if show_dir and Path(show_dir).exists():
            self.query_one("#dir_tree", DirectoryTree).path = show_dir
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection in directory tree."""
        path = event.path
        if path.is_dir():
            self.update_show_details(path)
    
    def update_show_details(self, show_path: Path) -> None:
        """Update the details panel with show information."""
        self.query_one("#selected_label", Static).update(f"Selected Show: {show_path.name}")
        
        # Update seasons table
        table = self.query_one("#seasons_table", DataTable)
        table.clear()
        
        seasons = get_valid_seasons(str(show_path))
        for season_path in seasons:
            season_name = Path(season_path).name
            mkv_files = list(Path(season_path).glob("*.mkv"))
            episode_count = len(mkv_files)
            
            # TODO: Check actual processing status
            status = "✓ Ready" if episode_count > 0 else "⚠️ No episodes"
            
            table.add_row(season_name, str(episode_count), status)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "process_btn":
            self.action_process()
        elif event.button.id == "subs_btn":
            self.action_get_subs()
        elif event.button.id == "settings_btn":
            self.app.push_screen(ConfigScreen())
    
    def action_process(self) -> None:
        """Process the selected show."""
        # Get selected directory from tree
        tree = self.query_one("#dir_tree", DirectoryTree)
        self.notify(f"Directory tree found: {tree}")
        
        if hasattr(tree, 'cursor_node') and tree.cursor_node:
            selected_path = str(tree.cursor_node.data.path)
            self.notify(f"Selected path: {selected_path}")
            
            if Path(selected_path).is_dir():
                # Check if it's a valid show directory
                seasons = get_valid_seasons(selected_path)
                self.notify(f"Found {len(seasons)} seasons in {selected_path}")
                
                if seasons:
                    self.notify(f"Starting processing for: {selected_path}")
                    self.app.push_screen(ProcessingScreen(selected_path))
                else:
                    self.notify("No seasons with .mkv files found in selected directory")
            else:
                self.notify("Please select a show directory")
        else:
            self.notify("Please select a show directory first")
            # Try to get current path from tree
            if hasattr(tree, 'path'):
                current_path = str(tree.path)
                self.notify(f"Tree current path: {current_path}")
                if Path(current_path).is_dir():
                    seasons = get_valid_seasons(current_path)
                    if seasons:
                        self.notify(f"Using tree path: {current_path}")
                        self.app.push_screen(ProcessingScreen(current_path))
                    else:
                        self.notify("Current path has no valid seasons")
    
    def action_get_subs(self) -> None:
        """Download subtitles for selected show."""
        # Get selected directory from tree
        tree = self.query_one("#dir_tree", DirectoryTree)
        if hasattr(tree, 'cursor_node') and tree.cursor_node:
            selected_path = str(tree.cursor_node.data.path)
            if Path(selected_path).is_dir():
                # Check if it's a valid show directory
                seasons = get_valid_seasons(selected_path)
                if seasons:
                    self.app.push_screen(ProcessingScreen(selected_path, get_subs=True))
                else:
                    self.notify("No seasons with .mkv files found in selected directory")
            else:
                self.notify("Please select a show directory")
        else:
            self.notify("Please select a show directory first")
    
    def action_back(self) -> None:
        """Go back to welcome screen."""
        self.app.pop_screen()


class ProcessingScreen(Screen):
    """Processing screen with progress tracking."""
    
    BINDINGS = [
        Binding("p", "pause", "Pause"),
        Binding("r", "resume", "Resume"),
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, show_dir: str, season: Optional[int] = None, dry_run: bool = False, get_subs: bool = False, confidence: float = 0.7):
        super().__init__()
        self.show_dir = show_dir
        self.season = season
        self.dry_run = dry_run
        self.get_subs = get_subs
        self.confidence = confidence
        self.is_paused = False
        self.is_cancelled = False
        self.current_file = ""
        self.current_step = ""
        self.total_files = 0
        self.processed_files = 0
        self.matched_files = 0
        self.processing_thread = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"🔄 Processing: {Path(self.show_dir).name}", id="processing_title"),
            Static("Overall Progress:", id="overall_label"),
            ProgressBar(total=100, id="overall_progress"),
            Static("Current Episode: Initializing...", id="current_episode"),
            Static("Status: Starting...", id="status"),
            Static("Step Progress:", id="step_label"),
            ProgressBar(total=100, id="step_progress"),
            Container(
                Static("📊 Results:", id="results_title"),
                DataTable(id="results_table"),
                id="results_container"
            ),
            Horizontal(
                Button("Pause Processing", id="pause_btn", variant="warning"),
                Button("Review Results", id="review_btn"),
                Button("Cancel", id="cancel_btn", variant="error"),
                id="processing_buttons"
            ),
            id="processing_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize processing screen."""
        # Setup results table
        table = self.query_one("#results_table", DataTable)
        table.add_columns("Episode", "Status", "Confidence")
        
        # Add some immediate feedback
        self.notify("ProcessingScreen mounted - initializing...")
        self._update_status("🎬 ProcessingScreen starting up...")
        
        # Add a test row to show the table is working
        table.add_row("Test", "Initializing...", "0.00")
        
        # Start processing
        self.start_processing()
    
    def start_processing(self) -> None:
        """Start the processing workflow in a background thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            self.notify("Processing already running")
            return
        
        self.notify("Starting processing...")
        self._update_status("🚀 Initializing...")
        
        try:
            self.processing_thread = threading.Thread(target=self._process_episodes, daemon=True)
            self.processing_thread.start()
            self.notify("Processing thread started")
        except Exception as e:
            self.notify(f"Failed to start processing: {str(e)}")
            self._update_status(f"❌ Failed to start: {str(e)}")
    
    def _process_episodes(self) -> None:
        """Main processing logic running in background thread."""
        try:
            self.call_from_thread(self.notify, "Processing thread started successfully")
            self.call_from_thread(self._update_status, "📋 Loading configuration...")
            
            config = get_config(CONFIG_FILE)
            self.call_from_thread(self.notify, f"Config loaded. Show dir: {self.show_dir}")
            
            show_name = clean_text(normalize_path(self.show_dir).name)
            self.call_from_thread(self.notify, f"Cleaned show name: {show_name}")
            self.call_from_thread(self._update_status, "🧠 Initializing episode matcher...")
            
            matcher = EpisodeMatcher(CACHE_DIR, show_name, min_confidence=self.confidence)
            self.call_from_thread(self.notify, "Episode matcher initialized")
            
            # Update UI with show info
            self.call_from_thread(self._update_processing_title, f"🔄 Processing: {show_name}")
            
            # Check for reference files
            reference_dir = Path(CACHE_DIR) / "data" / show_name
            self.call_from_thread(self.notify, f"Checking reference dir: {reference_dir}")
            reference_files = list(reference_dir.glob("*.srt"))
            self.call_from_thread(self.notify, f"Found {len(reference_files)} reference files")
            
            if (not self.get_subs) and (not reference_files):
                self.call_from_thread(self._update_status, "⚠️ No reference subtitle files found")
                self.call_from_thread(self.notify, "Warning: No reference subtitle files found. Consider using --get-subs")
                return
            
            # Get season paths
            self.call_from_thread(self.notify, f"Getting valid seasons from: {self.show_dir}")
            season_paths = get_valid_seasons(self.show_dir)
            self.call_from_thread(self.notify, f"Found season paths: {season_paths}")
            
            if not season_paths:
                self.call_from_thread(self._update_status, "❌ No seasons with .mkv files found")
                self.call_from_thread(self.notify, "Error: No seasons with .mkv files found")
                return
            
            # Filter by specific season if requested
            self.call_from_thread(self.notify, f"Season filter: {self.season}")
            if self.season is not None:
                season_path = str(Path(self.show_dir) / f"Season {self.season}")
                self.call_from_thread(self.notify, f"Looking for specific season: {season_path}")
                if season_path not in season_paths:
                    self.call_from_thread(self._update_status, f"❌ Season {self.season} has no .mkv files")
                    self.call_from_thread(self.notify, f"Error: Season {self.season} has no .mkv files to process")
                    return
                season_paths = [season_path]
                self.call_from_thread(self.notify, f"Using filtered season paths: {season_paths}")
            else:
                self.call_from_thread(self.notify, f"Using all season paths: {season_paths}")
            
            # Count total files
            self.call_from_thread(self.notify, "Counting MKV files...")
            all_mkv_files = []
            for season_path in season_paths:
                self.call_from_thread(self.notify, f"Checking season: {season_path}")
                mkv_files = [
                    f for f in Path(season_path).glob("*.mkv")
                    if not check_filename(f)
                ]
                self.call_from_thread(self.notify, f"Found {len(mkv_files)} unprocessed MKV files in {season_path}")
                all_mkv_files.extend([(season_path, f) for f in mkv_files])
            
            self.total_files = len(all_mkv_files)
            self.call_from_thread(self.notify, f"Total files to process: {self.total_files}")
            
            if self.total_files == 0:
                self.call_from_thread(self._update_status, "✅ No new files to process")
                self.call_from_thread(self.notify, "All files already processed")
                return
            
            self.call_from_thread(self.notify, "Initializing progress tracking...")
            self.call_from_thread(self._update_overall_progress, 0)
            
            # Process each season
            self.call_from_thread(self.notify, "Starting season processing loop...")
            for i, season_path in enumerate(season_paths):
                self.call_from_thread(self.notify, f"Processing season {i+1}/{len(season_paths)}: {season_path}")
                
                if self.is_cancelled:
                    self.call_from_thread(self.notify, "Processing cancelled during season loop")
                    break
                
                season_num = int(re.search(r'Season (\d+)', season_path).group(1))
                self.call_from_thread(self.notify, f"Extracted season number: {season_num}")
                
                mkv_files = [
                    f for f in Path(season_path).glob("*.mkv")
                    if not check_filename(f)
                ]
                self.call_from_thread(self.notify, f"Files to process in season {season_num}: {len(mkv_files)}")
                
                if not mkv_files:
                    self.call_from_thread(self.notify, f"No files in season {season_num}, skipping")
                    continue
                
                temp_dir = Path(season_path) / "temp"
                self.call_from_thread(self.notify, f"Creating temp directory: {temp_dir}")
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    # Download subtitles if requested
                    if self.get_subs:
                        self.call_from_thread(self.notify, f"get_subs enabled - downloading subtitles for season {season_num}")
                        self.call_from_thread(self._update_status, f"⬇️ Downloading subtitles for Season {season_num}...")
                        
                        self.call_from_thread(self.notify, f"Fetching show ID for: {matcher.show_name}")
                        show_id = fetch_show_id(matcher.show_name)
                        self.call_from_thread(self.notify, f"Show ID result: {show_id}")
                        
                        if show_id:
                            self.call_from_thread(self.notify, f"Downloading subtitles for show ID {show_id}, season {season_num}")
                            get_subtitles(show_id, seasons={season_num}, config=config)
                            self.call_from_thread(self.notify, f"Subtitles downloaded for Season {season_num}")
                        else:
                            self.call_from_thread(self.notify, "Could not find show ID for subtitle download")
                    else:
                        self.call_from_thread(self.notify, "get_subs disabled, skipping subtitle download")
                    
                    # Process each file
                    self.call_from_thread(self.notify, f"Starting file processing loop for {len(mkv_files)} files")
                    for i, mkv_file in enumerate(mkv_files):
                        self.call_from_thread(self.notify, f"Processing file {i+1}/{len(mkv_files)}: {mkv_file}")
                        
                        if self.is_cancelled:
                            self.call_from_thread(self.notify, "Processing cancelled during file loop")
                            break
                        
                        # Handle pause
                        if self.is_paused:
                            self.call_from_thread(self.notify, "Processing paused, waiting...")
                        while self.is_paused and not self.is_cancelled:
                            time.sleep(0.1)
                        
                        if self.is_cancelled:
                            self.call_from_thread(self.notify, "Processing cancelled after pause check")
                            break
                        
                        file_basename = Path(mkv_file).name
                        self.current_file = file_basename
                        self.call_from_thread(self.notify, f"Current file: {file_basename}")
                        
                        # Update UI
                        self.call_from_thread(self._update_current_episode, f"S{season_num:02d}E?? - {file_basename}")
                        self.call_from_thread(self._update_status, "🔊 Analyzing audio...")
                        self.call_from_thread(self._update_step_progress, 0)
                        
                        # Process the file
                        self.processed_files += 1
                        self.call_from_thread(self.notify, f"About to process single file: {mkv_file}")
                        
                        try:
                            match = self._process_single_file(matcher, mkv_file, temp_dir, season_num)
                            self.call_from_thread(self.notify, f"File processing completed. Match result: {match}")
                        except Exception as e:
                            self.call_from_thread(self.notify, f"Error processing file {mkv_file}: {str(e)}")
                            match = None
                        
                        if match:
                            self.matched_files += 1
                            episode_name = f"S{match['season']:02d}E{match['episode']:02d}"
                            new_name = f"{matcher.show_name} - {episode_name}.mkv"
                            confidence = match['confidence']
                            
                            # Update results table
                            status = "✓ Matched" if confidence > 0.8 else "⚠️ Low confidence"
                            self.call_from_thread(self._add_result, episode_name, status, f"{confidence:.2f}")
                            
                            # Rename file if not dry run
                            if not self.dry_run:
                                self.call_from_thread(self._update_status, "📝 Renaming file...")
                                rename_episode_file(mkv_file, new_name)
                        else:
                            # No match found
                            self.call_from_thread(self._add_result, file_basename, "❌ No match", "0.00")
                        
                        # Update overall progress
                        overall_progress = int((self.processed_files / self.total_files) * 100)
                        self.call_from_thread(self._update_overall_progress, overall_progress)
                        
                finally:
                    # Cleanup temp directory
                    if not self.dry_run and temp_dir.exists():
                        shutil.rmtree(temp_dir)
            
            # Final status update
            if self.is_cancelled:
                self.call_from_thread(self._update_status, "❌ Processing cancelled")
            else:
                success_rate = (self.matched_files / self.processed_files) * 100 if self.processed_files > 0 else 0
                self.call_from_thread(self._update_status, f"✅ Complete! {self.matched_files}/{self.processed_files} matched ({success_rate:.1f}%)")
                self.call_from_thread(self.notify, f"Processing complete! {self.matched_files} files matched")
                
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.call_from_thread(self._update_status, f"❌ Error: {str(e)}")
            self.call_from_thread(self.notify, error_msg)
            
            # Log the full traceback
            import traceback
            traceback_str = traceback.format_exc()
            self.call_from_thread(self.notify, f"Full traceback: {traceback_str[:200]}...")
            print(f"TUI Processing Error: {error_msg}")
            print(f"Full traceback:\n{traceback_str}")
    
    def _process_single_file(self, matcher: EpisodeMatcher, mkv_file: Path, temp_dir: Path, season_num: int) -> Optional[dict]:
        """Process a single MKV file and return match result."""
        try:
            self.call_from_thread(self.notify, f"_process_single_file started for: {mkv_file.name}")
            
            # Update step progress for different stages
            self.call_from_thread(self._update_step_progress, 20)
            self.call_from_thread(self._update_status, "🎵 Extracting audio...")
            self.call_from_thread(self.notify, "Step 1: Audio extraction simulation")
            
            # Simulate processing steps with progress updates
            time.sleep(0.1)  # Brief pause for UI updates
            
            self.call_from_thread(self._update_step_progress, 40)
            self.call_from_thread(self._update_status, "🎙️ Running speech recognition...")
            self.call_from_thread(self.notify, "Step 2: About to call matcher.identify_episode")
            
            # Actual episode identification - THIS IS LIKELY WHERE IT HANGS
            self.call_from_thread(self.notify, f"Calling matcher.identify_episode with: file={mkv_file}, temp_dir={temp_dir}, season={season_num}")
            match = matcher.identify_episode(mkv_file, temp_dir, season_num)
            self.call_from_thread(self.notify, f"matcher.identify_episode returned: {match}")
            
            self.call_from_thread(self._update_step_progress, 80)
            self.call_from_thread(self._update_status, "🔍 Comparing with reference subtitles...")
            self.call_from_thread(self.notify, "Step 3: Post-processing")
            
            time.sleep(0.1)  # Brief pause for UI updates
            
            self.call_from_thread(self._update_step_progress, 100)
            self.call_from_thread(self.notify, f"_process_single_file completed successfully")
            
            return match
            
        except Exception as e:
            error_msg = f"Error processing {mkv_file.name}: {str(e)}"
            self.call_from_thread(self.notify, error_msg)
            
            # Get traceback
            import traceback
            tb = traceback.format_exc()
            self.call_from_thread(self.notify, f"Traceback: {tb[:200]}...")
            
            return None
    
    def _update_processing_title(self, title: str) -> None:
        """Update the processing title."""
        self.query_one("#processing_title", Static).update(title)
    
    def _update_status(self, status: str) -> None:
        """Update the current status."""
        self.query_one("#status", Static).update(f"Status: {status}")
    
    def _update_current_episode(self, episode: str) -> None:
        """Update the current episode being processed."""
        self.query_one("#current_episode", Static).update(f"Current Episode: {episode}")
    
    def _update_overall_progress(self, progress: int) -> None:
        """Update the overall progress bar."""
        progress_bar = self.query_one("#overall_progress", ProgressBar)
        progress_bar.progress = progress
    
    def _update_step_progress(self, progress: int) -> None:
        """Update the step progress bar."""
        progress_bar = self.query_one("#step_progress", ProgressBar)
        progress_bar.progress = progress
    
    def _add_result(self, episode: str, status: str, confidence: str) -> None:
        """Add a result to the results table."""
        table = self.query_one("#results_table", DataTable)
        table.add_row(episode, status, confidence)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "pause_btn":
            self.action_pause()
        elif event.button.id == "review_btn":
            self.action_review()
        elif event.button.id == "cancel_btn":
            self.action_cancel()
    
    def action_pause(self) -> None:
        """Pause/resume processing."""
        if not self.processing_thread or not self.processing_thread.is_alive():
            self.notify("No processing is currently running")
            return
            
        self.is_paused = not self.is_paused
        btn = self.query_one("#pause_btn", Button)
        if self.is_paused:
            btn.label = "Resume Processing"
            self._update_status("⏸️ Processing paused")
            self.notify("Processing paused")
        else:
            btn.label = "Pause Processing"
            self._update_status("▶️ Processing resumed")
            self.notify("Processing resumed")
    
    def action_resume(self) -> None:
        """Resume processing (same as unpause)."""
        if self.is_paused:
            self.action_pause()
    
    def action_review(self) -> None:
        """Review processing results."""
        # Focus on the results table for easier navigation
        self.query_one("#results_table").focus()
        self.notify("Use arrow keys to navigate results")
    
    def action_cancel(self) -> None:
        """Cancel processing and return to previous screen."""
        if self.processing_thread and self.processing_thread.is_alive():
            self.is_cancelled = True
            self._update_status("🛑 Cancelling...")
            self.notify("Cancelling processing...")
            
            # Wait briefly for cleanup, then return
            def delayed_exit():
                time.sleep(1)
                self.app.call_from_thread(self.app.pop_screen)
            
            threading.Thread(target=delayed_exit, daemon=True).start()
        else:
            self.app.pop_screen()


class MKVEpisodeMatcherApp(App):
    """Main TUI application."""
    
    CSS_PATH = "tui_styles.tcss"
    TITLE = "MKV Episode Matcher"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def on_mount(self) -> None:
        """Initialize the application."""
        self.push_screen(WelcomeScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui():
    """Run the TUI application."""
    app = MKVEpisodeMatcherApp()
    app.run()


if __name__ == "__main__":
    run_tui()