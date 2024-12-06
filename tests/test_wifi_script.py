import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from network.wifi_manager import test_wifi_connection

@pytest.fixture
def temp_credentials_file():
    """Fixture to create a temporary credentials file."""
    fd, temp_path = tempfile.mkstemp()
    test_credentials = {
        "ssid": "test_network",
        "password": "test_password"
    }
    with os.fdopen(fd, 'w') as f:
        json.dump(test_credentials, f)
    yield temp_path
    # Cleanup (although the script should delete it)
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_successful_wifi_test(temp_credentials_file):
    """Test successful WiFi connection test."""
    expected_result = {
        "result": "OK",
        "message": "Successfully connected to WiFi"
    }
    
    with patch('network.wifi_manager.test_wifi_connection') as mock_test: 
        mock_test.return_value = expected_result
        
        # Run the script with subprocess to test actual command-line behavior
        result = os.system(f'python3 nc/test_wifi.py {temp_credentials_file}')
        
        assert result == 0  # Check exit code
        mock_test.assert_called_once()

def test_invalid_credentials_file():
    """Test with non-existent credentials file."""
    result = os.system('python3 nc/test_wifi.py /nonexistent/path')
    assert result != 0  # Should fail with non-zero exit code

def test_malformed_credentials_file():
    """Test with malformed credentials file."""
    fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as f:
            f.write('{"ssid": "test_network"}')  # Missing password field
        
        result = os.system(f'python3 nc/test_wifi.py {temp_path}')
        assert result != 0  # Should fail with non-zero exit code
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_no_arguments():
    """Test script with no arguments."""
    result = os.system('python3 nc/test_wifi.py')
    assert result != 0  # Should fail with non-zero exit code

@pytest.mark.parametrize("test_data,expected_exit_code", [
    ({"ssid": "test_network", "password": "test_pass"}, 0),
    ({"ssid": "", "password": "test_pass"}, 1),
    ({"ssid": "test_network", "password": ""}, 1),
])
def test_various_credentials(test_data, expected_exit_code):
    """Test different credential combinations."""
    fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(test_data, f)
            
        with patch('network.wifi_manager.test_wifi_connection') as mock_test:
            mock_test.return_value = {
                "result": "OK" if expected_exit_code == 0 else "ERROR",
                "message": "Test message"
            }
            
            result = os.system(f'python3 nc/test_wifi.py {temp_path}')
            assert (result == 0) == (expected_exit_code == 0)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_file_permissions(temp_credentials_file):
    """Test file permission checks."""
    # Make file readable by others
    os.chmod(temp_credentials_file, 0o666)
    
    result = os.system(f'python3 nc/test_wifi.py {temp_credentials_file}')
    assert result != 0  # Should fail due to insecure permissions
