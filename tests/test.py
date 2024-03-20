import unittest
from mkv_episode_matcher.utils import check_filename, rename_episode_file, calculate_image_hash, hashes_are_similar
import os
class TestUtils(unittest.TestCase):

    def test_check_filename(self):
        self.assertTrue(check_filename('Example - S01E03.mkv', 'Example', 1, 3))
        self.assertFalse(check_filename('Example - S01E03.avi', 'Example', 1, 3))
        self.assertFalse(check_filename('Example - S01E04.mkv', 'Example', 1, 3))
        self.assertFalse(check_filename('Example - S02E03.mkv', 'Example', 1, 3))
        self.assertFalse(check_filename('Other - S01E03.mkv', 'Example', 1, 3))

    def test_rename_episode_file(self):
        # create a temporary directory for testing
        import tempfile
        temp_dir = tempfile.TemporaryDirectory()
        original_file_path = os.path.join(temp_dir.name, 'episode.mkv')
        with open(original_file_path, 'w') as f:
            f.write('test')
        season_number = 1
        episode_number = 3
        series_title = 'Example'
        rename_episode_file(original_file_path, season_number, episode_number)
        new_file_path = os.path.join(temp_dir.name, f'{series_title} - S01E03.mkv')
        self.assertTrue(os.path.exists(new_file_path))
        temp_dir.cleanup()

    def test_calculate_image_hash(self):
        import imagehash
        from PIL import Image
        image = Image.new('RGB', (100, 100), color='red')
        
        hash = calculate_image_hash(image.to_array(), is_path=False)
        self.assertIsInstance(hash, imagehash.ImageHash)

    def test_hashes_are_similar(self):
        self.assertTrue(hashes_are_similar(10, 15, threshold=10))
        self.assertFalse(hashes_are_similar(10, 25, threshold=10))

if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()
