from utils.logging import logger
from utils.cmd import run_sudo_command

def poweroff(sudo_password:str)->bool:
    # Create the connection
    stdout, stderr = run_sudo_command(['poweroff'], sudo_password)
    if stderr:
        logger.error(f"Connection creation failed: {stderr}")
        raise RuntimeError(f"Connection creation failed: {stderr}")
    else:
        return True
