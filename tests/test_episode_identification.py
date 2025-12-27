import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from mkv_episode_matcher.episode_identification import EpisodeMatcher


class TestEpisodeIdentificationPatternMatching(unittest.TestCase):
    """Test the pattern matching functionality in episode identification."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

        # Mock subtitle cache
        self.mock_subtitle_cache = Mock()

        # Create identifier instance
        self.identifier = EpisodeMatcher(
            cache_dir=self.cache_dir, show_name="Test Show (2023)"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def _create_test_files(self, filenames, show_name=None):
        """Create test subtitle files in the cache directory."""
        if show_name is None:
            show_name = self.identifier.show_name

        show_dir = self.cache_dir / "data" / show_name
        show_dir.mkdir(parents=True, exist_ok=True)

        created_files = []
        for filename in filenames:
            file_path = show_dir / filename
            file_path.write_text("dummy subtitle content")
            created_files.append(file_path)

        return created_files

    def test_pattern_matching_s01e_format(self):
        """Test pattern matching for S01E format files."""
        # Create test files with S01E format
        test_files = [
            "Test Show (2023) - S01E01.srt",
            "Test Show (2023) - S01E02.srt",
            "Test Show (2023) - S01E10.srt",
            "Test Show (2023) - S02E01.srt",  # Should not match season 1
        ]

        self._create_test_files(test_files)

        # Test season 1 matching
        reference_files = self.identifier.get_reference_files(1)

        # Should find 3 files for season 1
        self.assertEqual(len(reference_files), 3)

        # Verify correct files are matched
        matched_names = [f.name for f in reference_files]
        self.assertIn("Test Show (2023) - S01E01.srt", matched_names)
        self.assertIn("Test Show (2023) - S01E02.srt", matched_names)
        self.assertIn("Test Show (2023) - S01E10.srt", matched_names)
        self.assertNotIn("Test Show (2023) - S02E01.srt", matched_names)

    def test_pattern_matching_s1e_format(self):
        """Test pattern matching for S1E format files."""
        test_files = [
            "Show - S1E01.srt",
            "Show - S1E05.srt",
            "Show - S2E01.srt",  # Should not match season 1
        ]

        self._create_test_files(test_files)

        reference_files = self.identifier.get_reference_files(1)

        # Should find 2 files for season 1
        self.assertEqual(len(reference_files), 2)

        matched_names = [f.name for f in reference_files]
        self.assertIn("Show - S1E01.srt", matched_names)
        self.assertIn("Show - S1E05.srt", matched_names)
        self.assertNotIn("Show - S2E01.srt", matched_names)

    def test_pattern_matching_01x_format(self):
        """Test pattern matching for 01x format files."""
        test_files = [
            "Show - 01x01.srt",
            "Show - 01x15.srt",
            "Show - 02x01.srt",  # Should not match season 1
        ]

        self._create_test_files(test_files)

        reference_files = self.identifier.get_reference_files(1)

        # Should find 2 files for season 1
        self.assertEqual(len(reference_files), 2)

        matched_names = [f.name for f in reference_files]
        self.assertIn("Show - 01x01.srt", matched_names)
        self.assertIn("Show - 01x15.srt", matched_names)
        self.assertNotIn("Show - 02x01.srt", matched_names)

    def test_pattern_matching_1x_format(self):
        """Test pattern matching for 1x format files."""
        test_files = [
            "Show - 1x01.srt",
            "Show - 1x08.srt",
            "Show - 2x01.srt",  # Should not match season 1
        ]

        self._create_test_files(test_files)

        reference_files = self.identifier.get_reference_files(1)

        # Should find 2 files for season 1
        self.assertEqual(len(reference_files), 2)

        matched_names = [f.name for f in reference_files]
        self.assertIn("Show - 1x01.srt", matched_names)
        self.assertIn("Show - 1x08.srt", matched_names)
        self.assertNotIn("Show - 2x01.srt", matched_names)

    def test_pattern_matching_mixed_formats(self):
        """Test pattern matching with mixed file formats."""
        test_files = [
            "Show - S01E01.srt",
            "Show - S1E02.srt",
            "Show - 01x03.srt",
            "Show - 1x04.srt",
            "Show - S02E01.srt",  # Different season
            "Show - episode1.srt",  # No matching pattern
        ]

        self._create_test_files(test_files)

        reference_files = self.identifier.get_reference_files(1)

        # Should find 4 files for season 1 (all matching patterns)
        self.assertEqual(len(reference_files), 4)

        matched_names = [f.name for f in reference_files]
        self.assertIn("Show - S01E01.srt", matched_names)
        self.assertIn("Show - S1E02.srt", matched_names)
        self.assertIn("Show - 01x03.srt", matched_names)
        self.assertIn("Show - 1x04.srt", matched_names)
        self.assertNotIn("Show - S02E01.srt", matched_names)
        self.assertNotIn("Show - episode1.srt", matched_names)

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case insensitive."""
        test_files = [
            "show - s01e01.srt",  # lowercase s and e
            "SHOW - S01E02.SRT",  # uppercase everything
            "Show - S01e03.srt",  # mixed case
        ]

        self._create_test_files(test_files)

        reference_files = self.identifier.get_reference_files(1)

        # Should find all 3 files regardless of case
        self.assertEqual(len(reference_files), 3)

    def test_dexter_new_blood_issue_reproduction(self):
        """Test the specific issue from bug report with Dexter New Blood files."""
        # Create files matching the exact pattern from the bug report
        test_files = [
            "Dexter - New Blood (2021) - S01E01.srt",
            "Dexter - New Blood (2021) - S01E02.srt",
            "Dexter - New Blood (2021) - S01E03.srt",
            "Dexter - New Blood (2021) - S01E04.srt",
            "Dexter - New Blood (2021) - S01E05.srt",
            "Dexter - New Blood (2021) - S01E06.srt",
            "Dexter - New Blood (2021) - S01E07.srt",
            "Dexter - New Blood (2021) - S01E08.srt",
            "Dexter - New Blood (2021) - S01E09.srt",
            "Dexter - New Blood (2021) - S01E10.srt",
        ]

        # Update the identifier to use the exact show name from the bug report
        show_name = "Dexter - New Blood (2021)"
        self.identifier.show_name = show_name

        self._create_test_files(test_files, show_name)

        reference_files = self.identifier.get_reference_files(1)

        # Should find all 10 files - this was the bug that was failing
        self.assertEqual(
            len(reference_files),
            10,
            f"Expected 10 files but found {len(reference_files)}. "
            f"Files found: {[f.name for f in reference_files]}",
        )

    def test_no_duplicate_files(self):
        """Test that duplicate matches are removed properly."""
        # Create a file that could match multiple patterns
        test_files = [
            "Show - S01E01.srt",  # Could match both S01E and 01x patterns if logic is wrong
        ]

        self._create_test_files(test_files)

        reference_files = self.identifier.get_reference_files(1)

        # Should find only 1 unique file, not duplicates
        self.assertEqual(len(reference_files), 1)

        # Verify it's the correct file
        self.assertEqual(reference_files[0].name, "Show - S01E01.srt")

    def test_empty_directory(self):
        """Test behavior when no matching files exist."""
        # Create the directory but no files
        show_dir = self.cache_dir / "data" / "Test Show (2023)"
        show_dir.mkdir(parents=True, exist_ok=True)

        reference_files = self.identifier.get_reference_files(1)

        # Should find no files
        self.assertEqual(len(reference_files), 0)

    def test_directory_does_not_exist(self):
        """Test behavior when the show directory doesn't exist."""
        # Don't create the directory
        reference_files = self.identifier.get_reference_files(1)

        # Should find no files (glob returns empty on non-existent directory)
        self.assertEqual(len(reference_files), 0)

    def test_caching_functionality(self):
        """Test that results are properly cached."""
        test_files = ["Show - S01E01.srt"]
        self._create_test_files(test_files)

        # First call
        reference_files_1 = self.identifier.get_reference_files(1)

        # Second call should return cached result
        reference_files_2 = self.identifier.get_reference_files(1)

        # Should be the same result
        self.assertEqual(reference_files_1, reference_files_2)

        # Verify it's actually using the cache by checking the cache directly
        cache_key = ("Test Show (2023)", 1)
        self.assertIn(cache_key, self.identifier.reference_files_cache)

    def test_different_seasons(self):
        """Test that different seasons are handled correctly."""
        test_files = [
            "Show - S01E01.srt",
            "Show - S01E02.srt",
            "Show - S02E01.srt",
            "Show - S02E02.srt",
            "Show - S03E01.srt",
        ]

        self._create_test_files(test_files)

        # Test season 1
        season1_files = self.identifier.get_reference_files(1)
        self.assertEqual(len(season1_files), 2)

        # Test season 2
        season2_files = self.identifier.get_reference_files(2)
        self.assertEqual(len(season2_files), 2)

        # Test season 3
        season3_files = self.identifier.get_reference_files(3)
        self.assertEqual(len(season3_files), 1)

        # Test non-existent season
        season4_files = self.identifier.get_reference_files(4)
        self.assertEqual(len(season4_files), 0)


if __name__ == "__main__":
    unittest.main()
