import threading
from shared.protocol import send_msg as protocol_send_msg

# { socket: username }
clients = {}
clients_lock = threading.Lock()

def send_msg(sock, message):
    """Send a length-prefixed message to a single socket safely."""
    try:
        protocol_send_msg(sock, message)
    except Exception:
        remove_client(sock)

def broadcast(message, exclude=None):
    """Send a message to all connected clients (optionally excluding one)."""
    with clients_lock:
        snapshot = list(clients.items())
    for sock, _ in snapshot:
        if sock is not exclude:
            send_msg(sock, message)

def broadcast_user_list():
    """Broadcast the current online user list to all clients."""
    with clients_lock:
        names = list(clients.values())
    user_list = ",".join(names)
    broadcast(f"[System|USERS:{user_list}]")

def get_socket_by_username(username):
    """Return the socket for the given username, or None."""
    with clients_lock:
        for sock, name in clients.items():
            if name.lower() == username.lower():
                return sock
    return None

def remove_client(sock):
    """Remove a disconnected client."""
    with clients_lock:
        username = clients.pop(sock, None)
    try:
        sock.close()
    except Exception:
        pass
    if username:
        broadcast(f"[System]: {username} has left the chat.")
        broadcast_user_list()
