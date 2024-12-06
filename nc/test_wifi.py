#!/usr/bin/env python3
import sys
import json
from network.utils import logger, format_result
from network.config import read_and_delete_credentials
from network.wifi_manager import test_wifi_connection

def main():
    if len(sys.argv) != 2:
        result = format_result(error='Invalid arguments. Usage: ./test_wifi.py <credentials_file_path>')
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    try:
        ssid, password, sudo_password = read_and_delete_credentials(sys.argv[1])
        result_data = test_wifi_connection(ssid, password, sudo_password)
        print(json.dumps(result_data, indent=2))
        sys.exit(0 if result_data['result'] == 'OK' else 1)
        
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        result = format_result(error=str(e))
        print(json.dumps(result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
