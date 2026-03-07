from typing import Optional

from shared.messages import build_system_message, build_username_taken_error_message
from shared.validation import validate_username
from server.repositories.chat_repository import ChatRepository


def _build_invalid_username_message(reason: str) -> str:
    if reason == "empty":
        return "ชื่อผู้ใช้ต้องไม่ว่าง"
    if reason == "too_long":
        return "ชื่อผู้ใช้ยาวเกินไป (สูงสุด 24 ตัวอักษร)"
    if reason == "reserved":
        return "ชื่อผู้ใช้นี้ไม่สามารถใช้งานได้"
    return "ชื่อผู้ใช้มีอักขระที่ไม่อนุญาต"


def join_client(client_socket, requested_username: str, repository: ChatRepository) -> Optional[str]:
    """Register a new client and broadcast presence. Returns username or None."""
    username = requested_username.strip()
    invalid_reason = validate_username(username)
    if invalid_reason:
        message = _build_invalid_username_message(invalid_reason)
        from shared.messages import build_login_error_message
        repository.send_message(client_socket, build_login_error_message(message))
        return None

    if not repository.register_client(client_socket, username):
        repository.send_message(client_socket, build_username_taken_error_message())
        return None

    repository.broadcast_message(build_system_message(f"{username} เข้าร่วมช่องแชทแล้ว!"))
    repository.broadcast_user_list()
    return username
