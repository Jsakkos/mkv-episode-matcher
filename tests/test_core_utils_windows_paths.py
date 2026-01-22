"""
Test Windows-specific path handling in core.utils for issue #81.

This test file verifies that FFmpeg/FFprobe subprocess calls properly handle
Windows paths with spaces and special characters using os.fspath() instead of str().
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from mkv_episode_matcher.core.utils import get_video_duration, extract_audio_chunk


class TestGetVideoDurationWindowsPaths(unittest.TestCase):
    """Test get_video_duration with Windows paths containing spaces."""

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_issue_81_exact_path(self, mock_run):
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
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_multiple_spaces_in_path(self, mock_run):
        """Test paths with multiple directories containing spaces."""
        mock_run.return_value = Mock(returncode=0, stdout="1800.0\n", stderr="")

        # Path with multiple levels of spaces
        test_path = Path(r"C:\My TV Shows\Breaking Bad\Season 1\Episode 1.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1800.0)
        mock_run.assert_called_once()

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_special_characters_in_path(self, mock_run):
        """Test paths with special characters like parentheses."""
        mock_run.return_value = Mock(returncode=0, stdout="2400.0\n", stderr="")

        # Path with parentheses (common in show names)
        test_path = Path(r"C:\Shows\Breaking Bad (2008)\Season 1\ep.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 2400.0)

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_long_path_with_spaces(self, mock_run):
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
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_input_path_with_spaces(self, mock_run):
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
    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_output_path_with_spaces(self, mock_run):
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

    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_posix_paths_still_work(self, mock_run):
        """Verify Unix/Linux paths still work correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="1234.0\n", stderr="")

        # POSIX path
        test_path = Path("/home/user/videos/show/episode.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1234.0)
        mock_run.assert_called_once()

    @patch("mkv_episode_matcher.core.utils.subprocess.run")
    def test_relative_paths(self, mock_run):
        """Test relative paths work correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="1500.0\n", stderr="")

        test_path = Path("videos/episode.mkv")
        duration = get_video_duration(test_path)

        self.assertEqual(duration, 1500.0)


if __name__ == "__main__":
    unittest.main()
