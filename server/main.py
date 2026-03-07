import socket
import threading
from dotenv import load_dotenv

from shared.config import HOST, PORT
from server.core import handle_client
from server import ai_service

# Load environment variables
load_dotenv()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server is listening on {HOST}:{PORT}...")
    print(f"Using AI Model: {ai_service.GROQ_MODEL} (via ai_service)")

    while True:
        client_socket, address = server.accept()
        print(f"Connected with {str(address)}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_server()
