HEADER_SIZE = 10
ENCODING = "utf-8"


def send_msg(sock, message: str) -> None:
    msg_bytes = message.encode(ENCODING)
    header = f"{len(msg_bytes):<{HEADER_SIZE}}".encode(ENCODING)
    sock.sendall(header + msg_bytes)


def _recv_exact(sock, size: int, allow_clean_eof: bool = False) -> bytes | None:
    if size == 0:
        return b""

    chunks: list[bytes] = []
    bytes_recd = 0

    while bytes_recd < size:
        chunk = sock.recv(size - bytes_recd)
        if not chunk:
            if bytes_recd == 0 and allow_clean_eof:
                return None
            raise RuntimeError("Socket connection broken")
        chunks.append(chunk)
        bytes_recd += len(chunk)

    return b"".join(chunks)


def recv_msg(sock) -> str | None:
    header = _recv_exact(sock, HEADER_SIZE, allow_clean_eof=True)
    if header is None:
        return None

    length_str = header.decode(ENCODING).strip()
    if not length_str:
        return None

    if not length_str.isdigit():
        raise RuntimeError(f"Invalid message header: {length_str!r}")

    msg_length = int(length_str)
    payload = _recv_exact(sock, msg_length)
    if payload is None:
        raise RuntimeError("Socket connection broken")

    return payload.decode(ENCODING)
