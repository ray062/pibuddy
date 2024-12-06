import os
import json
import stat
from .utils import logger

def read_and_delete_credentials(cred_file_path):
    """Read credentials from temporary file and delete it immediately."""
    try:
        if not os.path.exists(cred_file_path):
            raise FileNotFoundError("Credentials file not found")
        
        file_stat = os.stat(cred_file_path)
        if file_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise PermissionError("Credentials file has too open permissions")
        
        with open(cred_file_path, 'r') as f:
            creds = json.load(f)
            
        if 'ssid' not in creds or 'password' not in creds or 'sudo_password' not in creds:
            raise ValueError("Missing required credentials fields")
            
        return creds['ssid'], creds['password'], creds['sudo_password']
        
    finally:
        try:
            os.remove(cred_file_path)
            logger.info(f"Credentials file {cred_file_path} has been deleted")
        except Exception as e:
            logger.warning(f"Could not delete credentials file: {e}")
