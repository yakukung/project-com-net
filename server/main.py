import socket
import threading

from dotenv import load_dotenv

from server.ai.ai_provider import PRIMARY_MODEL
from server.handlers.client_session_handler import handle_client
from shared.network_constants import SERVER_HOST, SERVER_PORT

load_dotenv()


def start_server() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen()

    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}...")
    print(f"Primary AI Model: {PRIMARY_MODEL}")

    while True:
        client_socket, address = server_socket.accept()
        print(f"Connected with {address}")
        thread = threading.Thread(target=handle_client, args=(client_socket,), daemon=True)
        thread.start()


if __name__ == "__main__":
    start_server()
