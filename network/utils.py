import sys
import subprocess
import logging

def setup_logging():
    """Configure logging settings."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stderr
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def format_result(result='Failed', ip_address=None, dhcp_server=None, 
                 gateway=None, dns_servers=None, error=None):
    """Format the result dictionary."""
    return {
        'result': result,
        'ip_address': ip_address,
        'dhcp_server': dhcp_server,
        'gateway': gateway,
        'dns_servers': dns_servers,
        'error': error
    }

def run_sudo_command(command, password):
    # -S flag makes sudo read password from stdin
    cmd = ['sudo', '-S'] + command

    
    # Create process with pipe for stdin
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send password with newline
    stdout, stderr = process.communicate(input=f'{password}\n')
    
    return stdout, stderr