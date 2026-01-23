"""
Test Windows-specific path handling in core.utils for issue #81.

This test file verifies that FFmpeg/FFprobe subprocess calls properly handle
Windows paths with spaces and special characters using os.fspath() instead of str().

Also tests FFmpeg path resolution for uv-managed environments.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from mkv_episode_matcher.core.utils import (
    _find_executable,
    extract_audio_chunk,
    get_ffmpeg_path,
    get_ffprobe_path,
    get_video_duration,
)


class TestGetVideoDurationWindowsPaths(unittest.TestCase):
    """Test get_video_duration with Windows paths containing spaces."""

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_issue_81_exact_path(self, mock_run, mock_which):
        """
        Reproduce exact error from issue #81: C:\\Friends\\Season 1\\05.mkv

        The user reported: [WinError 2] The system cannot find the file specified
        This test verifies the fix using os.fspath().
        """
        # Arrange: Mock ffprobe success
        mock_run.return_value = Mock(
            returncode=0,
            stdout="1234.56\n",
            stderr=""
        )

        # Act: Call with path containing spaces (exact path from issue)
        test_path = Path(r"C:\Friends\Season 1\05.mkv")
        duration = get_video_duration(test_path)

        # Assert: Should succeed with os.fspath()
        self.assertEqual(duration, 1234.56)
        mock_run.assert_called_once()

        # Verify the path was properly converted for subprocess
        call_args = mock_run.call_args[0][0]  # Get command list
        # The path should be in the command arguments
        self.assertTrue(
            any(r"C:\Friends\Season 1\05.mkv" in str(arg) for arg in call_args),
            f"Path not found in command: {call_args}"
        )

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_multiple_spaces_in_path(self, mock_run, mock_which):
        """Test paths with multiple directories containing spaces."""
        mock_run.return_value = Mock(returncode=0, stdout="1800.0\n", stderr="")

        # Path with multiple levels of spaces
        test_path = Path(r"C:\My TV Shows\Breaking Bad\Season 1\Episode 1.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1800.0)
        mock_run.assert_called_once()

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_special_characters_in_path(self, mock_run, mock_which):
        """Test paths with special characters like parentheses."""
        mock_run.return_value = Mock(returncode=0, stdout="2400.0\n", stderr="")

        # Path with parentheses (common in show names)
        test_path = Path(r"C:\Shows\Breaking Bad (2008)\Season 1\ep.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 2400.0)

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_long_path_with_spaces(self, mock_run, mock_which):
        """Test very long Windows paths with spaces."""
        mock_run.return_value = Mock(returncode=0, stdout="3000.0\n", stderr="")

        # Long path similar to Windows user directories
        test_path = Path(
            r"C:\Users\John Doe\Documents\My Videos\TV Shows"
            r"\Breaking Bad\Season 1\Episode 1.mkv"
        )
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 3000.0)


class TestExtractAudioChunkWindowsPaths(unittest.TestCase):
    """Test extract_audio_chunk with Windows paths containing spaces."""

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffmpeg")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_input_path_with_spaces(self, mock_run, mock_which):
        """Test extract_audio_chunk with input path containing spaces."""
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            # Mock successful FFmpeg execution and create output file
            def create_output(*args, **kwargs):
                output_path.write_bytes(b'\x00' * 2048)  # Create file >1KB
                return Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = create_output

            # Input path with spaces
            input_path = Path(r"C:\Friends\Season 1\episode.mkv")

            # Call function
            result = extract_audio_chunk(input_path, 0.0, 30.0, output_path)

            # Should succeed
            self.assertEqual(result, output_path)
            mock_run.assert_called_once()

            # Verify both input and output paths in command
            call_args = mock_run.call_args[0][0]
            self.assertTrue(
                any(r"Friends\Season 1" in str(arg) for arg in call_args),
                f"Input path not found in command: {call_args}"
            )
        finally:
            if output_path.exists():
                output_path.unlink()

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffmpeg")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_output_path_with_spaces(self, mock_run, mock_which):
        """Test extract_audio_chunk with output path containing spaces."""
        # Output path with spaces (use temp directory)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory with spaces
            temp_dir = Path(tmpdir) / "Test User"
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_path = temp_dir / "audio chunk.wav"

            # Mock and create output
            def create_output(*args, **kwargs):
                output_path.write_bytes(b'\x00' * 2048)
                return Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = create_output

            input_path = Path(r"C:\video.mkv")
            result = extract_audio_chunk(input_path, 0.0, 30.0, output_path)

            self.assertEqual(result, output_path)


class TestCrossplatformPathHandling(unittest.TestCase):
    """Test that the fix maintains cross-platform compatibility."""

    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_posix_paths_still_work(self, mock_run, mock_which):
        """Verify Unix/Linux paths still work correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="1234.0\n", stderr="")

        # POSIX path
        test_path = Path("/home/user/videos/show/episode.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1234.0)
        mock_run.assert_called_once()

    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_relative_paths(self, mock_run, mock_which):
        """Test relative paths work correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="1500.0\n", stderr="")

        test_path = Path("videos/episode.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1500.0)


class TestFFmpegPathResolution(unittest.TestCase):
    """Test FFmpeg executable path resolution for uv-managed environments."""

    @patch("mkv_episode_matcher.core.utils.shutil.which")
    def test_ffmpeg_found_in_path(self, mock_which):
        """Test that FFmpeg can be found when in PATH."""
        # Clear the LRU cache to ensure fresh lookup
        _find_executable.cache_clear()

        # Mock shutil.which to return a path
        mock_which.return_value = "/usr/bin/ffmpeg"

        result = get_ffmpeg_path()

        self.assertEqual(result, "/usr/bin/ffmpeg")
        mock_which.assert_called_once_with("ffmpeg")

    @patch("mkv_episode_matcher.core.utils.shutil.which")
    def test_ffprobe_found_in_path(self, mock_which):
        """Test that ffprobe can be found when in PATH."""
        # Clear the LRU cache
        _find_executable.cache_clear()

        mock_which.return_value = "/usr/bin/ffprobe"

        result = get_ffprobe_path()

        self.assertEqual(result, "/usr/bin/ffprobe")
        mock_which.assert_called_once_with("ffprobe")

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.shutil.which")
    def test_ffmpeg_windows_path(self, mock_which):
        """Test FFmpeg resolution on Windows with typical install path."""
        _find_executable.cache_clear()

        # Typical Windows FFmpeg path
        mock_which.return_value = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"

        result = get_ffmpeg_path()

        self.assertEqual(result, r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")

    @patch("mkv_episode_matcher.core.utils.shutil.which")
    def test_ffmpeg_not_found_raises_error(self, mock_which):
        """Test that FileNotFoundError is raised when FFmpeg not in PATH."""
        _find_executable.cache_clear()

        # Mock shutil.which to return None (not found)
        mock_which.return_value = None

        with self.assertRaises(FileNotFoundError) as context:
            get_ffmpeg_path()

        # Verify error message contains helpful information
        error_message = str(context.exception)
        self.assertIn("ffmpeg not found in PATH", error_message)
        self.assertIn("Please ensure FFmpeg is installed", error_message)

    @patch("mkv_episode_matcher.core.utils.shutil.which")
    def test_ffprobe_not_found_raises_error(self, mock_which):
        """Test that FileNotFoundError is raised when ffprobe not in PATH."""
        _find_executable.cache_clear()

        mock_which.return_value = None

        with self.assertRaises(FileNotFoundError) as context:
            get_ffprobe_path()

        error_message = str(context.exception)
        self.assertIn("ffprobe not found in PATH", error_message)

    @patch("mkv_episode_matcher.core.utils.shutil.which")
    def test_lru_cache_reduces_lookups(self, mock_which):
        """Test that LRU cache prevents repeated shutil.which calls."""
        _find_executable.cache_clear()

        mock_which.return_value = "/usr/bin/ffmpeg"

        # Call multiple times
        get_ffmpeg_path()
        get_ffmpeg_path()
        get_ffmpeg_path()

        # Should only call shutil.which once due to caching
        mock_which.assert_called_once_with("ffmpeg")


class TestFFmpegIntegrationWithFunctions(unittest.TestCase):
    """Test that get_video_duration and extract_audio_chunk work with path resolution."""

    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffprobe")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_get_video_duration_uses_resolved_path(self, mock_run, mock_which):
        """Test that get_video_duration uses the resolved ffprobe path."""
        _find_executable.cache_clear()

        mock_run.return_value = Mock(returncode=0, stdout="1234.5\n", stderr="")

        test_path = Path("test.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1234.5)

        # Verify the resolved path was used in the command
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "ffprobe")

    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value=None)
    def test_get_video_duration_handles_missing_ffprobe(self, mock_which):
        """Test that get_video_duration handles missing ffprobe gracefully."""
        _find_executable.cache_clear()

        test_path = Path("test.mkv")

        # Should return 0.0 when ffprobe not found (as per existing error handling)
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 0.0)

    @patch("mkv_episode_matcher.core.utils.shutil.which", return_value="ffmpeg")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_extract_audio_uses_resolved_path(self, mock_run, mock_which):
        """Test that extract_audio_chunk uses the resolved ffmpeg path."""
        _find_executable.cache_clear()

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            def create_output(*args, **kwargs):
                output_path.write_bytes(b'\x00' * 2048)
                return Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = create_output

            input_path = Path("test.mkv")
            result = extract_audio_chunk(input_path, 0.0, 30.0, output_path)

            self.assertEqual(result, output_path)

            # Verify the resolved path was used
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args[0], "ffmpeg")
        finally:
            if output_path.exists():
                output_path.unlink()


if __name__ == "__main__":
    unittest.main()
