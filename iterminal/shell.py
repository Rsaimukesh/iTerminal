import subprocess

def is_probably_shell_command(user_input: str) -> bool:
    return bool(user_input.strip() and (user_input.split()[0].isalpha() or user_input.startswith('./')))

def run_shell_command(cmd: str):
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, '', str(e) 