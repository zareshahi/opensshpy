import os
import socket
import paramiko
from paramiko import RSAKey, ServerInterface

# Define a basic SSH server interface
class SimpleSSHServer(ServerInterface):
    def check_auth_password(self, username, password):
        if username == "user" and password == "pass":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

# Start the SSH server
def start_ssh_server():
    # Generate host key if it does not exist
    host_key_path = "server_rsa.key"
    if not os.path.exists(host_key_path):
        key = RSAKey.generate(2048)
        key.write_private_key_file(host_key_path)
    else:
        key = RSAKey(filename=host_key_path)
    
    # Set up the SSH server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 2200))  # Listening on all interfaces at port 2200
    server_socket.listen(100)
    print("Listening for connection on port 2200...")

    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")

    # Start the SSH session
    ssh_session = paramiko.Transport(client_socket)
    ssh_session.add_server_key(key)
    ssh_server = SimpleSSHServer()

    try:
        ssh_session.start_server(server=ssh_server)
    except paramiko.SSHException as e:
        print(f"SSH negotiation failed: {e}")
        return

    # Accept the client channel and handle input/output
    channel = ssh_session.accept(20)
    if channel is None:
        print("No channel request received")
        return

    print("Authenticated successfully")
    channel.send("Welcome to the SSH server!\n")
    
    while True:
        try:
            command = channel.recv(1024).decode("utf-8")
            if command.strip().lower() == "exit":
                channel.send("Goodbye!\n")
                break
            response = f"Received: {command}\n"
            channel.send(response)
        except Exception as e:
            print(f"Error: {e}")
            break

    channel.close()
    ssh_session.close()

if __name__ == "__main__":
    start_ssh_server()
