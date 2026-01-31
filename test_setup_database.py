import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import json
import logging

# Suppress logging output during tests
logging.basicConfig(level=logging.CRITICAL)

# Add the directory containing the script to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the functions to be tested
from setup_database import (
    fetch_matomo_data,
    import_matomo_models,
    check_database_exists,
    main as setup_main
)

class TestSetupDatabase(unittest.TestCase):

    @patch('setup_database.requests.get')
    def test_fetch_matomo_data(self, mock_get):
        """Test fetching data from Matomo, with and without cache."""
        mock_url = "http://fake-matomo-url.com/mobiles.yml"
        mock_content = "some yaml content"

        # Mock requests.get
        mock_response = MagicMock()
        mock_response.text = mock_content
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # --- Test 1: Fetch from network (no cache) ---
        with self.subTest("Fetch from network when no cache exists"):
            with patch('os.path.exists', return_value=False):
                with patch('builtins.open', mock_open()) as mocked_file:
                    content = fetch_matomo_data(mock_url)
                    
                    # Verify it was called
                    mock_get.assert_called_with(mock_url, timeout=30)
                    # Verify it wrote to cache
                    mocked_file.assert_called_with("matomo_mobiles.yml", 'w', encoding='utf-8')
                    handle = mocked_file()
                    handle.write.assert_called_once_with(mock_content)
                    # Verify correct content was returned
                    self.assertEqual(content, mock_content)

        # --- Test 2: Use local cache if it exists ---
        with self.subTest("Use local cache when it exists"):
            # Reset mock for new assertion
            mock_get.reset_mock()
            with patch('os.path.exists', return_value=True):
                # mock_open.side_effect allows different behavior for read
                m = mock_open(read_data=mock_content)
                with patch('builtins.open', m):
                    content = fetch_matomo_data(mock_url)
                    
                    # Verify network was NOT called
                    mock_get.assert_not_called()
                    # Verify the file was read
                    m.assert_called_with("matomo_mobiles.yml", 'r', encoding='utf-8')
                    # Verify correct content was returned
                    self.assertEqual(content, mock_content)

        # --- Test 3: Force refresh even if cache exists ---
        with self.subTest("Force refresh even when cache exists"):
            mock_get.reset_mock()
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open()) as mocked_file:
                    content = fetch_matomo_data(mock_url, force_refresh=True)

                    # Verify it was called
                    mock_get.assert_called_with(mock_url, timeout=30)
                    # Verify it wrote to cache
                    mocked_file.assert_called_with("matomo_mobiles.yml", 'w', encoding='utf-8')
                    # Verify correct content was returned
                    self.assertEqual(content, mock_content)


if __name__ == '__main__':
    unittest.main()
