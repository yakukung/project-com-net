import re
import threading
from shared.protocol import recv_msg
from server.client_manager import (
    clients, clients_lock, broadcast, send_msg, 
    broadcast_user_list, get_socket_by_username, remove_client
)
from server.ai_handler import query_ai_and_broadcast

def handle_client(client_socket):
    """Handle one connected client."""
    username = None

    while True:
        try:
            message = recv_msg(client_socket)
            if message is None:
                break

            print(f"Received: {message}")

            # ── Extract sender username from join message ──
            if username is None and "has joined the chat!" in message:
                requested_username = message.split(" has joined")[0].strip()
                with clients_lock:
                    if any(name.lower() == requested_username.lower() for name in clients.values()):
                        send_msg(client_socket, "[System|ERROR]: Username already taken.")
                        continue
                    username = requested_username
                    clients[client_socket] = username
                broadcast(f"[System]: {username} has joined the chat!")
                broadcast_user_list()
                continue

            # ── DM: message starts with @username (not @ai) ──
            dm_match = re.match(r'^@(?!ai\b)(\S+)\s+(.*)', message, re.IGNORECASE | re.DOTALL)
            if dm_match:
                target_name = dm_match.group(1)
                dm_text = dm_match.group(2).strip()

                sender_name = clients.get(client_socket, "Unknown")
                target_sock = get_socket_by_username(target_name)

                if target_sock:
                    send_msg(target_sock, f"[DM|FROM:{sender_name}]: {dm_text}")
                    send_msg(client_socket, f"[DM|TO:{target_name}]: {dm_text}")
                else:
                    send_msg(client_socket, f"[System]: ไม่พบผู้ใช้ '{target_name}' ออนไลน์")
                continue

            # ── Group message ──
            broadcast(message)

            # Check for @ai
            if "@ai" in message.lower():
                broadcast("[System]: AI กำลังพิมพ์คำตอบ...")
                ai_thread = threading.Thread(
                    target=query_ai_and_broadcast,
                    args=(message, message)
                )
                ai_thread.start()

        except Exception as e:
            print(f"Client error: {e}")
            break

    remove_client(client_socket)
