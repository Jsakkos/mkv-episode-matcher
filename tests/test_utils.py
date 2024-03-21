import unittest
from unittest.mock import patch
import os

from utils import rename_episode_file,hashes_are_similar,calculate_image_hash

class TestUtils(unittest.TestCase):
    @patch('utils.logger')
    @patch('os.path.exists')
    @patch('os.rename')
    def test_rename_episode_file_unique_name(self, mock_rename, mock_exists, mock_logger):
        # Mock the return value of os.path.exists to simulate a unique file name
        mock_exists.return_value = False

        # Call the function with sample inputs
        original_file_path = '/path/to/episode.mkv'
        season_number = 1
        episode_number = 3
        rename_episode_file(original_file_path, season_number, episode_number)

        # Assert that os.rename is called with the expected new file path
        expected_new_file_name = 'Example - S01E03.mkv'
        expected_new_file_path = os.path.join(os.path.dirname(original_file_path), expected_new_file_name)
        mock_rename.assert_called_once_with(original_file_path, expected_new_file_path)

        # Assert that the logger is called with the expected log messages
        mock_logger.info.assert_called_once_with(f'Renaming episode.mkv -> {expected_new_file_name}')
        mock_logger.warning.assert_not_called()

    @patch('utils.logger')
    @patch('os.path.exists')
    @patch('os.rename')
    def test_rename_episode_file_existing_name(self, mock_rename, mock_exists, mock_logger):
        # Mock the return value of os.path.exists to simulate an existing file name
        mock_exists.return_value = True

        # Call the function with sample inputs
        original_file_path = '/path/to/episode.mkv'
        season_number = 1
        episode_number = 3
        rename_episode_file(original_file_path, season_number, episode_number)

        # Assert that os.rename is called with the expected new file path (with suffix)
        expected_new_file_name = 'Example - S01E03_2.mkv'
        expected_new_file_path = os.path.join(os.path.dirname(original_file_path), expected_new_file_name)
        mock_rename.assert_called_once_with(original_file_path, expected_new_file_path)

        # Assert that the logger is called with the expected log messages
        mock_logger.info.assert_called_once_with(f'Renaming episode.mkv -> {expected_new_file_name}')
        mock_logger.warning.assert_called_once_with(f'Filename already exists: {expected_new_file_name}.')

    @patch('utils.logger')
    def test_hashes_are_similar_within_threshold(self, mock_logger):
        # Call the function with similar hashes within the threshold
        hash1 = 1234567890
        hash2 = 1234567885
        threshold = 10
        result = hashes_are_similar(hash1, hash2, threshold)

        # Assert that the function returns the expected result
        self.assertEqual(result, (True, 5))

        # Assert that the logger is not called
        mock_logger.info.assert_not_called()

    @patch('utils.logger')
    def test_hashes_are_similar_outside_threshold(self, mock_logger):
        # Call the function with dissimilar hashes outside the threshold
        hash1 = 1234567890
        hash2 = 1234567860
        threshold = 10
        result = hashes_are_similar(hash1, hash2, threshold)

        # Assert that the function returns the expected result
        self.assertEqual(result, (False, 30))

        # Assert that the logger is not called
        mock_logger.info.assert_not_called()

    @patch('utils.Image.open')
    @patch('imagehash.average_hash')
    def test_calculate_image_hash_with_path(self, mock_average_hash, mock_image_open):
        # Mock the return value of Image.open and imagehash.average_hash
        mock_image = mock_image_open.return_value
        mock_hash = mock_average_hash.return_value

        # Call the function with a file path
        file_path = '/path/to/image.jpg'
        result = calculate_image_hash(file_path)

        # Assert that Image.open is called with the expected file path
        mock_image_open.assert_called_once_with(file_path)

        # Assert that imagehash.average_hash is called with the opened image
        mock_average_hash.assert_called_once_with(mock_image)

        # Assert that the result is equal to the mock hash
        self.assertEqual(result, mock_hash)

    @patch('utils.Image.fromarray')
    @patch('imagehash.average_hash')
    def test_calculate_image_hash_with_data(self, mock_average_hash, mock_image_fromarray):
        # Mock the return value of Image.fromarray and imagehash.average_hash
        mock_image = mock_image_fromarray.return_value
        mock_hash = mock_average_hash.return_value

        # Call the function with binary data
        data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        result = calculate_image_hash(data, is_path=False)

        # Assert that Image.fromarray is called with the expected binary data
        mock_image_fromarray.assert_called_once_with(data)

        # Assert that imagehash.average_hash is called with the converted image
        mock_average_hash.assert_called_once_with(mock_image)

        # Assert that the result is equal to the mock hash
        self.assertEqual(result, mock_hash)

if __name__ == '__main__':
    unittest.main()