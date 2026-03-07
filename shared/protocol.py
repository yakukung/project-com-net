def send_msg(sock, message):
    """Send a length-prefixed message to a single socket."""
    msg_bytes = message.encode('utf-8')
    header = f"{len(msg_bytes):<10}".encode('utf-8')
    sock.sendall(header + msg_bytes)

def recv_msg(sock):
    """Receive a length-prefixed message from a single socket."""
    length_str = sock.recv(10).decode('utf-8').strip()
    if not length_str:
        return None

    msg_length = int(length_str)
    chunks = []
    bytes_recd = 0
    while bytes_recd < msg_length:
        chunk = sock.recv(min(msg_length - bytes_recd, 4096))
        if not chunk:
            raise RuntimeError("Socket connection broken")
        chunks.append(chunk)
        bytes_recd += len(chunk)

    return b''.join(chunks).decode('utf-8')
