import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
from io import BytesIO
from unittest.mock import MagicMock, patch
from PIL import Image
from io import BytesIO
import requests
from unittest.mock import MagicMock, patch
from PIL import Image
from io import BytesIO
import requests

from tmdb_client import calculate_image_hash_from_url, fetch_season_details



class TestTmdbClient(unittest.TestCase):
    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_success(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        # Mock the Image.open function
        mock_image_open = MagicMock()
        mock_image_open.return_value = Image.open(BytesIO(b'fake_image_data'))

        with patch('tmdb_client.Image.open', mock_image_open):
            # Call the function with a valid image URL
            image_url = 'https://example.com/image.jpg'
            result = calculate_image_hash_from_url(image_url)

            # Assert that the result is not None
            self.assertIsNotNone(result)

            # Assert that the result is a string
            self.assertIsInstance(result, str)

    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_failure(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with an invalid image URL
        image_url = 'https://example.com/nonexistent.jpg'
        result = calculate_image_hash_from_url(image_url)

        # Assert that the result is None
        self.assertIsNone(result)

    @patch('tmdb_client.requests.get')
    def test_fetch_season_details_success(self, mock_get):
        # Mock the response from the requests.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'episodes': [
                {'name': 'Episode 1'},
                {'name': 'Episode 2'},
                {'name': 'Episode 3'}
            ]
        }
        mock_get.return_value = mock_response

        # Call the function with a valid show ID and season number
        show_id = '12345'
        season_number = 1
        result = fetch_season_details(show_id, season_number)

        # Assert that the result is the expected number of episodes
        self.assertEqual(result, 3)

    @patch('tmdb_client.requests.get')
    def test_fetch_season_details_failure(self, mock_get):
        # Mock the response from the requests.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with an invalid show ID and season number
        show_id = '54321'
        season_number = 2
        result = fetch_season_details(show_id, season_number)

        # Assert that the result is 0
        self.assertEqual(result, 0)
class TestTmdbClient(unittest.TestCase):
    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_success(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        # Mock the Image.open function
        mock_image_open = MagicMock()
        mock_image_open.return_value = Image.open(BytesIO(b'fake_image_data'))

        with patch('tmdb_client.Image.open', mock_image_open):
            # Call the function with a valid image URL
            image_url = 'https://example.com/image.jpg'
            result = calculate_image_hash_from_url(image_url)

            # Assert that the result is not None
            self.assertIsNotNone(result)

            # Assert that the result is a string
            self.assertIsInstance(result, str)

    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_failure(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with an invalid image URL
        image_url = 'https://example.com/nonexistent.jpg'
        result = calculate_image_hash_from_url(image_url)

        # Assert that the result is None
        self.assertIsNone(result)

class TestTmdbClient(unittest.TestCase):
    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_success(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        # Mock the Image.open function
        mock_image_open = MagicMock()
        mock_image_open.return_value = Image.open(BytesIO(b'fake_image_data'))

        with patch('tmdb_client.Image.open', mock_image_open):
            # Call the function with a valid image URL
            image_url = 'https://example.com/image.jpg'
            result = calculate_image_hash_from_url(image_url)

            # Assert that the result is not None
            self.assertIsNotNone(result)

            # Assert that the result is a string
            self.assertIsInstance(result, str)

    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_failure(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with an invalid image URL
        image_url = 'https://example.com/nonexistent.jpg'
        result = calculate_image_hash_from_url(image_url)

        # Assert that the result is None
        self.assertIsNone(result)

    def test_fetch_show_id_success(self):
        # Mock the response from the requests.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "12345"}
            ]
        }
        mock_get = MagicMock(return_value=mock_response)

        with patch('tmdb_client.requests.get', mock_get):
            # Call the function with a valid show name
            show_name = "Friends"
            result = fetch_show_id(show_name)

            # Assert that the result is not None
            self.assertIsNotNone(result)

            # Assert that the result is a string
            self.assertIsInstance(result, str)

            # Assert that the result is the expected show ID
            self.assertEqual(result, "12345")

    def test_fetch_show_id_failure(self):
        # Mock the response from the requests.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": []
        }
        mock_get = MagicMock(return_value=mock_response)

        with patch('tmdb_client.requests.get', mock_get):
            # Call the function with an invalid show name
            show_name = "Nonexistent Show"
            result = fetch_show_id(show_name)

            # Assert that the result is None
            self.assertIsNone(result)

class TestTmdbClient(unittest.TestCase):
    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_success(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        # Mock the Image.open function
        mock_image_open = MagicMock()
        mock_image_open.return_value = Image.open(BytesIO(b'fake_image_data'))

        with patch('tmdb_client.Image.open', mock_image_open):
            # Call the function with a valid image URL
            image_url = 'https://example.com/image.jpg'
            result = calculate_image_hash_from_url(image_url)

            # Assert that the result is not None
            self.assertIsNotNone(result)

            # Assert that the result is a string
            self.assertIsInstance(result, str)

    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_failure(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with an invalid image URL
        image_url = 'https://example.com/nonexistent.jpg'
        result = calculate_image_hash_from_url(image_url)

        # Assert that the result is None
        self.assertIsNone(result)

    @patch('tmdb_client.rate_limited_request.get')
    def test_fetch_and_hash_episode_images_success(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'stills': [
                {'file_path': '/image1.jpg'},
                {'file_path': '/image2.jpg'}
            ]
        }
        mock_get.return_value = mock_response

        # Mock the calculate_image_hash_from_url function
        mock_calculate_hash = MagicMock()
        mock_calculate_hash.side_effect = ['hash1', 'hash2']
        with patch('tmdb_client.calculate_image_hash_from_url', mock_calculate_hash):
            # Call the function with sample arguments
            show_id = 123
            season_number = 1
            episode_number = 1
            result = fetch_and_hash_episode_images(show_id, season_number, episode_number)

            # Assert that the result is a list
            self.assertIsInstance(result, list)

            # Assert that the result contains the expected hash values
            self.assertEqual(result, ['hash1', 'hash2'])

    @patch('tmdb_client.rate_limited_request.get')
    def test_fetch_and_hash_episode_images_failure(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with sample arguments
        show_id = 123
        season_number = 1
        episode_number = 1
        result = fetch_and_hash_episode_images(show_id, season_number, episode_number)

        # Assert that the result is None
        self.assertIsNone(result)

class TestTmdbClient(unittest.TestCase):
    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_success(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response

        # Mock the Image.open function
        mock_image_open = MagicMock()
        mock_image_open.return_value = Image.open(BytesIO(b'fake_image_data'))

        with patch('tmdb_client.Image.open', mock_image_open):
            # Call the function with a valid image URL
            image_url = 'https://example.com/image.jpg'
            result = calculate_image_hash_from_url(image_url)

            # Assert that the result is not None
            self.assertIsNotNone(result)

            # Assert that the result is a string
            self.assertIsInstance(result, str)

    @patch('tmdb_client.rate_limited_request.get')
    def test_calculate_image_hash_from_url_failure(self, mock_get):
        # Mock the response from the rate_limited_request.get function
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the function with an invalid image URL
        image_url = 'https://example.com/nonexistent.jpg'
        result = calculate_image_hash_from_url(image_url)

        # Assert that the result is None
        self.assertIsNone(result)

    @patch('tmdb_client.fetch_season_details')
    @patch('tmdb_client.fetch_and_hash_episode_images')
    @patch('tmdb_client.get_config')
    @patch('tmdb_client.ThreadPoolExecutor')
    def test_fetch_and_hash_season_images(self, mock_executor, mock_get_config, mock_fetch_and_hash_episode_images, mock_fetch_season_details):
        # Mock the return values and behavior of the dependencies
        show_id = 123
        season_number = 1
        total_episodes = 5
        config = {'max_threads': 10}
        episode_hashes = {1: 'hash1', 2: 'hash2', 3: 'hash3', 4: 'hash4', 5: 'hash5'}

        mock_fetch_season_details.return_value = total_episodes
        mock_get_config.return_value = config
        mock_executor.return_value.__enter__.return_value.submit.side_effect = [
            MagicMock(return_value=episode_hashes[1]),
            MagicMock(return_value=episode_hashes[2]),
            MagicMock(return_value=episode_hashes[3]),
            MagicMock(return_value=episode_hashes[4]),
            MagicMock(return_value=episode_hashes[5])
        ]

        # Call the function under test
        result = fetch_and_hash_season_images(show_id, season_number)

        # Assert the expected behavior
        self.assertEqual(result, episode_hashes)

        mock_fetch_season_details.assert_called_once_with(show_id, season_number)
        mock_get_config.assert_called_once_with(CONFIG_FILE)
        mock_executor.assert_called_once_with(max_workers=config['max_threads'])
        mock_executor.return_value.__enter__.return_value.submit.assert_has_calls([
            unittest.mock.call(mock_fetch_and_hash_episode_images, show_id, season_number, 1),
            unittest.mock.call(mock_fetch_and_hash_episode_images, show_id, season_number, 2),
            unittest.mock.call(mock_fetch_and_hash_episode_images, show_id, season_number, 3),
            unittest.mock.call(mock_fetch_and_hash_episode_images, show_id, season_number, 4),
            unittest.mock.call(mock_fetch_and_hash_episode_images, show_id, season_number, 5)
        ])

if __name__ == '__main__':
    unittest.main()
