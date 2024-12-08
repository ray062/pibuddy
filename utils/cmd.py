import subprocess
def run_sudo_command(command, sudo_password):
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
    stdout, stderr = process.communicate(input=f'{sudo_password}\n')
    
    return stdout, stderr