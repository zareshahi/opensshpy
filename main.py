import os
import socket
import paramiko
import logging
from paramiko import RSAKey, ServerInterface

# Configure logging
logging.basicConfig(level=logging.INFO)

class SimpleSSHServer(ServerInterface):
    def __init__(self, allowed_users=None):
        self.allowed_users = allowed_users if allowed_users else {"user": "pass"}

    def check_auth_password(self, username, password):
        if username in self.allowed_users and self.allowed_users[username] == password:
            logging.info(f"Authentication successful for user: {username}")
            return paramiko.AUTH_SUCCESSFUL
        logging.warning(f"Authentication failed for user: {username}")
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            logging.info(f"Channel request {kind} accepted.")
            return paramiko.OPEN_SUCCEEDED
        logging.warning(f"Channel request {kind} denied.")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

def generate_or_load_host_key(key_path="server_rsa.key"):
    if not os.path.exists(key_path):
        logging.info("Generating new RSA host key.")
        key = RSAKey.generate(2048)
        key.write_private_key_file(key_path)
    else:
        logging.info("Loading existing RSA host key.")
        key = RSAKey(filename=key_path)
    return key

def handle_client(channel):
    try:
        channel.send("Welcome to the SSH server!\nType 'exit' to disconnect.\n")
        while True:
            command = channel.recv(1024).decode("utf-8").strip()
            if not command:
                continue
            if command.lower() == "exit":
                channel.send("Goodbye!\n")
                break
            response = f"Received: {command}\n"
            logging.info(f"Client command: {command}")
            channel.send(response)
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        channel.close()

def start_ssh_server(host="0.0.0.0", port=2200, allowed_users=None):
    host_key = generate_or_load_host_key()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(100)
    logging.info(f"Listening for connections on {host}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Connection received from {addr}")

        try:
            ssh_session = paramiko.Transport(client_socket)
            ssh_session.add_server_key(host_key)
            ssh_server = SimpleSSHServer(allowed_users=allowed_users)

            try:
                ssh_session.start_server(server=ssh_server)
            except paramiko.SSHException as e:
                logging.error(f"SSH negotiation failed: {e}")
                continue

            channel = ssh_session.accept(20)
            if channel is None:
                logging.warning("No channel request received. Closing connection.")
                continue

            logging.info("Authenticated successfully, starting session.")
            handle_client(channel)
        except Exception as e:
            logging.error(f"Exception in connection handling: {e}")
        finally:
            ssh_session.close()

if __name__ == "__main__":
    # Customizable allowed users
    allowed_users = {"user": "pass", "admin": "admin123"}  # Update with real users

    # Start the SSH server
    start_ssh_server(host="0.0.0.0", port=2200, allowed_users=allowed_users)
