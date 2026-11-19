import subprocess

def get_user(username):
    query = "SELECT * FROM users WHERE name='" + username + "'"
    return query

def run_command(command):
    subprocess.call(command, shell=True)


password = "admin123"