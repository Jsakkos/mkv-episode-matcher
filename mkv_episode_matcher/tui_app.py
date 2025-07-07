"""
TUI Application for MKV Episode Matcher using Textual.
"""

from pathlib import Path
from typing import Optional, List
import asyncio

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

from mkv_episode_matcher import __version__
from mkv_episode_matcher.config import get_config, set_config
from mkv_episode_matcher.__main__ import CONFIG_FILE, CACHE_DIR
from mkv_episode_matcher.utils import get_valid_seasons
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
        if show_dir and Path(show_dir).exists():
            self.app.push_screen(ProcessingScreen(show_dir))
        else:
            self.action_browse()
    
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
        # TODO: Get selected directory from tree
        self.notify("Processing not implemented yet")
    
    def action_get_subs(self) -> None:
        """Download subtitles for selected show."""
        # TODO: Implement subtitle download
        self.notify("Subtitle download not implemented yet")
    
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
    
    def __init__(self, show_dir: str, season: Optional[int] = None):
        super().__init__()
        self.show_dir = show_dir
        self.season = season
        self.is_paused = False
    
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
        
        # Start processing
        self.start_processing()
    
    def start_processing(self) -> None:
        """Start the processing workflow."""
        # TODO: Implement actual processing logic
        self.notify("Processing started (not fully implemented)")
    
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
        self.is_paused = not self.is_paused
        btn = self.query_one("#pause_btn", Button)
        if self.is_paused:
            btn.label = "Resume Processing"
            self.notify("Processing paused")
        else:
            btn.label = "Pause Processing"
            self.notify("Processing resumed")
    
    def action_review(self) -> None:
        """Review processing results."""
        # TODO: Implement results review
        self.notify("Results review not implemented yet")
    
    def action_cancel(self) -> None:
        """Cancel processing and return to previous screen."""
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