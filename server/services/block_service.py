from shared.messages import build_system_message
from server.repositories.chat_repository import ChatRepository


def block_user_by_ip(client_socket, target_username: str, repository: ChatRepository) -> None:
    target_name = target_username.strip()
    if not target_name:
        repository.send_message(client_socket, build_system_message("กรุณาระบุชื่อผู้ใช้ที่ต้องการบล็อค"))
        return

    result = repository.block_user_ip(client_socket, target_name)
    if result == "ok":
        repository.send_message(
            client_socket,
            build_system_message(f"บล็อค '{target_name}' แล้ว"),
        )
        repository.broadcast_user_list()
        return

    if result == "already_blocked":
        repository.send_message(client_socket, build_system_message(f"คุณบล็อค '{target_name}' ไว้อยู่แล้ว"))
        return
    if result == "cannot_block_self":
        repository.send_message(client_socket, build_system_message("ไม่สามารถบล็อคตัวเองได้"))
        return
    if result == "target_not_found":
        repository.send_message(client_socket, build_system_message(f"ไม่พบผู้ใช้ '{target_name}' ออนไลน์"))
        return

    repository.send_message(client_socket, build_system_message("ไม่สามารถบล็อคผู้ใช้นี้ได้"))


def unblock_user_by_ip(client_socket, target_username: str, repository: ChatRepository) -> None:
    target_name = target_username.strip()
    if not target_name:
        repository.send_message(client_socket, build_system_message("กรุณาระบุชื่อผู้ใช้ที่ต้องการเลิกบล็อค"))
        return

    result = repository.unblock_user_ip(client_socket, target_name)
    if result == "ok":
        repository.send_message(
            client_socket,
            build_system_message(f"เลิกบล็อค '{target_name}' แล้ว"),
        )
        repository.broadcast_user_list()
        return

    if result == "not_blocked":
        repository.send_message(client_socket, build_system_message(f"คุณยังไม่ได้บล็อค '{target_name}'"))
        return
    if result == "cannot_unblock_self":
        repository.send_message(client_socket, build_system_message("ไม่สามารถเลิกบล็อคตัวเองได้"))
        return
    if result == "target_not_found":
        repository.send_message(client_socket, build_system_message(f"ไม่พบผู้ใช้ '{target_name}' ออนไลน์"))
        return

    repository.send_message(client_socket, build_system_message("ไม่สามารถเลิกบล็อคผู้ใช้นี้ได้"))
