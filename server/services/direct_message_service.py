import threading

from shared.messages import (
    build_chat_message,
    build_dm_ai_message,
    build_dm_from_message,
    build_dm_to_message,
    build_system_message,
    contains_ai_mention,
)
from server.repositories.chat_repository import ChatRepository


def send_direct_message(
    client_socket,
    target_name: str,
    dm_text: str,
    repository: ChatRepository,
) -> None:
    sender_name = repository.get_username_by_socket(client_socket) or "Unknown"
    target_sock = repository.get_socket_by_username(target_name)

    if not target_sock:
        repository.send_message(client_socket, build_system_message(f"ไม่พบผู้ใช้ '{target_name}' ออนไลน์"))
        return

    repository.send_message(target_sock, build_dm_from_message(sender_name, dm_text))
    repository.send_message(client_socket, build_dm_to_message(target_name, dm_text))

    if contains_ai_mention(dm_text):
        from server.handlers.ai_message_handler import query_ai_and_broadcast

        typing_notice = build_system_message("AI กำลังพิมพ์คำตอบ...")
        repository.send_message(client_socket, build_dm_ai_message(target_name, typing_notice))
        repository.send_message(target_sock, build_dm_ai_message(sender_name, typing_notice))
        thread = threading.Thread(
            target=query_ai_and_broadcast,
            args=(dm_text, dm_text, client_socket, target_sock, repository),
            daemon=True,
        )
        thread.start()


def send_public_message(client_socket, message_text: str, repository: ChatRepository) -> None:
    sender_name = repository.get_username_by_socket(client_socket) or "Unknown"
    public_message = build_chat_message(sender_name, message_text)
    repository.broadcast_message(public_message)

    if contains_ai_mention(message_text):
        from server.handlers.ai_message_handler import query_ai_and_broadcast

        repository.broadcast_message(build_system_message("AI กำลังพิมพ์คำตอบ..."))
        thread = threading.Thread(
            target=query_ai_and_broadcast,
            args=(message_text, message_text, None, None, repository),
            daemon=True,
        )
        thread.start()
