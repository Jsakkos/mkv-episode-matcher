import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from mkv_episode_matcher.episode_identification import (
    EpisodeMatcher,
    get_video_duration,
)


class TestErrorHandling(unittest.TestCase):
    """Test error handling functionality in episode identification."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

        # Create identifier instance
        self.identifier = EpisodeMatcher(
            cache_dir=self.cache_dir, show_name="Test Show (2023)"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_extract_audio_chunk_ffmpeg_failure(self):
        """Test that extract_audio_chunk handles FFmpeg failures gracefully."""
        # Ensure the chunk file doesn't already exist
        chunk_path = self.identifier.temp_dir / "chunk_300.wav"
        if chunk_path.exists():
            chunk_path.unlink()

        # Mock subprocess.run to simulate FFmpeg failure
        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stderr="Error: Invalid file format"
            )

            # Should raise RuntimeError with descriptive message
            with self.assertRaises(RuntimeError) as context:
                self.identifier.extract_audio_chunk("test.mkv", 300)

            self.assertIn("FFmpeg failed with return code 1", str(context.exception))
            self.assertIn("Invalid file format", str(context.exception))

    def test_extract_audio_chunk_timeout(self):
        """Test that extract_audio_chunk handles timeouts properly."""
        # Ensure the chunk file doesn't already exist
        chunk_path = self.identifier.temp_dir / "chunk_300.wav"
        if chunk_path.exists():
            chunk_path.unlink()

        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 30)

            # Should raise RuntimeError with timeout message
            with self.assertRaises(RuntimeError) as context:
                self.identifier.extract_audio_chunk("test.mkv", 300)

            self.assertIn("FFmpeg timed out after 30 seconds", str(context.exception))

    def test_extract_audio_chunk_no_output_file(self):
        """Test handling when FFmpeg succeeds but doesn't create output file."""
        # Ensure the chunk file doesn't already exist
        chunk_path = self.identifier.temp_dir / "chunk_300.wav"
        if chunk_path.exists():
            chunk_path.unlink()

        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")

            # Should raise RuntimeError when output file doesn't exist
            with self.assertRaises(RuntimeError) as context:
                self.identifier.extract_audio_chunk("test.mkv", 300)

            self.assertIn("output file was not created", str(context.exception))

    def test_extract_audio_chunk_small_file(self):
        """Test warning for small audio files."""
        # Ensure the chunk file doesn't already exist
        test_chunk_path = self.identifier.temp_dir / "chunk_300.wav"
        test_chunk_path.parent.mkdir(parents=True, exist_ok=True)
        if test_chunk_path.exists():
            test_chunk_path.unlink()

        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")

            # Mock the file creation during subprocess call
            def create_small_file(*args, **kwargs):
                test_chunk_path.write_bytes(b"small")  # Create a very small file
                return Mock(returncode=0, stderr="")

            mock_run.side_effect = create_small_file

            # Should not raise error for small files, but should log warning
            with patch(
                "mkv_episode_matcher.episode_identification.logger"
            ) as mock_logger:
                result = self.identifier.extract_audio_chunk("test.mkv", 300)
                self.assertEqual(result, str(test_chunk_path))
                mock_logger.warning.assert_called_once()
                self.assertIn("too small", mock_logger.warning.call_args[0][0])

    def test_get_video_duration_ffprobe_failure(self):
        """Test that get_video_duration handles ffprobe failures."""
        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stderr="No such file or directory"
            )

            with self.assertRaises(RuntimeError) as context:
                get_video_duration("nonexistent.mkv")

            self.assertIn("ffprobe failed with return code 1", str(context.exception))
            self.assertIn("No such file or directory", str(context.exception))

    def test_get_video_duration_timeout(self):
        """Test that get_video_duration handles timeouts."""
        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 10)

            with self.assertRaises(RuntimeError) as context:
                get_video_duration("test.mkv")

            self.assertIn("ffprobe timed out", str(context.exception))

    def test_get_video_duration_empty_output(self):
        """Test handling of empty ffprobe output."""
        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with self.assertRaises(RuntimeError) as context:
                get_video_duration("test.mkv")

            self.assertIn("returned empty duration", str(context.exception))

    def test_get_video_duration_invalid_duration(self):
        """Test handling of invalid duration values."""
        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="-5.0",  # Invalid negative duration
                stderr="",
            )

            with self.assertRaises(RuntimeError) as context:
                get_video_duration("test.mkv")

            self.assertIn("Invalid duration: -5.0", str(context.exception))

    def test_identify_episode_no_reference_files(self):
        """Test identify_episode when no reference files are found."""
        result = self.identifier.identify_episode("test.mkv", Path("/tmp"), 1)
        self.assertIsNone(result)

    def test_identify_episode_video_duration_failure(self):
        """Test identify_episode when video duration cannot be obtained."""
        # Create some reference files
        show_dir = self.cache_dir / "data" / "Test Show (2023)"
        show_dir.mkdir(parents=True, exist_ok=True)
        (show_dir / "Test Show (2023) - S01E01.srt").write_text("dummy content")

        with patch(
            "mkv_episode_matcher.episode_identification.get_video_duration"
        ) as mock_duration:
            mock_duration.side_effect = RuntimeError("Duration extraction failed")

            result = self.identifier.identify_episode("test.mkv", Path("/tmp"), 1)
            self.assertIsNone(result)

    @patch("mkv_episode_matcher.asr_models.get_cached_model")
    def test_identify_episode_model_failure_resilience(self, mock_get_cached_model):
        """Test that identify_episode continues when models fail."""
        # Create reference files
        show_dir = self.cache_dir / "data" / "Test Show (2023)"
        show_dir.mkdir(parents=True, exist_ok=True)
        (show_dir / "Test Show (2023) - S01E01.srt").write_text("dummy content")

        # Mock successful duration extraction
        with patch(
            "mkv_episode_matcher.episode_identification.get_video_duration",
            return_value=1800,
        ):
            # Mock the first model to fail, second to succeed
            mock_model_tiny = Mock()
            mock_model_tiny.transcribe.side_effect = Exception("Tiny model failed")
            mock_model_base = Mock()
            mock_model_base.transcribe.return_value = {"text": "test"}

            mock_get_cached_model.side_effect = [mock_model_tiny, mock_model_base]

            # Mock audio extraction to succeed
            with patch.object(
                self.identifier, "extract_audio_chunk", return_value="/tmp/chunk.wav"
            ):
                with patch.object(
                    self.identifier, "load_reference_chunk", return_value="test"
                ):
                    # Should not crash even when tiny model fails
                    self.identifier.identify_episode("test.mkv", Path("/tmp"), 1)
                    # Result may be None due to no actual matching, but shouldn't raise exception

    def test_audio_extraction_cleanup(self):
        """Test that failed audio extractions are cleaned up properly."""
        # Create a partial file that will be cleaned up
        test_chunk_path = self.identifier.temp_dir / "chunk_300.wav"
        test_chunk_path.parent.mkdir(parents=True, exist_ok=True)
        if test_chunk_path.exists():
            test_chunk_path.unlink()

        with patch(
            "mkv_episode_matcher.episode_identification.subprocess.run"
        ) as mock_run:

            def create_then_fail(*args, **kwargs):
                test_chunk_path.write_text("partial content")
                raise RuntimeError("FFmpeg failed")

            mock_run.side_effect = create_then_fail

            with self.assertRaises(RuntimeError):
                self.identifier.extract_audio_chunk("test.mkv", 300)

            # File should be cleaned up after failure
            self.assertFalse(test_chunk_path.exists())


if __name__ == "__main__":
    unittest.main()
