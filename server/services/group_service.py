import threading

from shared.messages import (
    build_group_chat_message,
    build_group_created_message,
    build_group_deleted_message,
    build_group_kicked_message,
    build_group_members_message,
    build_group_ownership_changed_message,
    build_system_message,
    contains_ai_mention,
    normalize_ai_prompt,
)
from shared.validation import validate_group_name
from server.repositories.chat_repository import ChatRepository


def create_group_for_owner(
    client_socket,
    group_name: str,
    member_names: list[str],
    repository: ChatRepository,
) -> None:
    cleaned_group_name = group_name.strip()
    invalid_reason = validate_group_name(cleaned_group_name)
    if invalid_reason:
        if invalid_reason == "empty":
            message = "ชื่อช่องแชทต้องไม่ว่าง"
        elif invalid_reason == "too_long":
            message = "ชื่อช่องแชทยาวเกินไป (สูงสุด 48 ตัวอักษร)"
        elif invalid_reason == "reserved":
            message = "ชื่อช่องแชทนี้เป็นชื่อที่สงวนไว้ (เช่น system, ai, admin, server, everyone)"
        elif invalid_reason == "invalid_chars":
            message = "ชื่อช่องแชทมีอักขระที่ไม่อนุญาต (ห้ามใช้ [ ] : | , และอักขระควบคุม)"
        repository.send_message(client_socket, build_system_message(message))
        return

    owner_name = repository.get_username_by_socket(client_socket) or "Unknown"
    member_sockets = [client_socket]

    for member_name in member_names:
        sock = repository.get_socket_by_username(member_name)
        if sock and sock is not client_socket and sock not in member_sockets:
            member_sockets.append(sock)

    group_id = repository.create_group(cleaned_group_name, member_sockets, owner_sock=client_socket)
    notification = build_group_created_message(group_id, cleaned_group_name, owner_name)
    for sock in member_sockets:
        repository.send_message(sock, notification)

    print(f"Group created: '{cleaned_group_name}' ({group_id}) by {owner_name}")


def send_group_members(client_socket, group_id: str, repository: ChatRepository) -> None:
    group = repository.get_group(group_id)
    if not group or client_socket not in group["members"]:
        repository.send_message(client_socket, build_system_message("ไม่สามารถดูสมาชิกช่องแชทนี้ได้"))
        return

    member_names = repository.get_group_member_names(group_id)
    owner_name = ""
    if group.get("owner"):
        owner_name = repository.get_username_by_socket(group["owner"]) or ""

    repository.send_message(client_socket, build_group_members_message(group_id, member_names, owner_name))


def kick_member_from_group(
    client_socket,
    group_id: str,
    target_username: str,
    repository: ChatRepository,
) -> None:
    requester_name = repository.get_username_by_socket(client_socket) or ""

    group = repository.get_group(group_id)
    is_owner = bool(group and group.get("owner") == client_socket)
    if not is_owner:
        repository.send_message(client_socket, build_system_message("คุณไม่ใช่ผู้สร้างช่องแชท"))
        return

    kicked_sock = repository.kick_member(group_id, target_username)
    if kicked_sock:
        repository.send_to_group(
            group_id,
            build_group_chat_message(
                group_id,
                "System",
                f"❌ {target_username} ถูกเตะออกจากช่องแชทโดย {requester_name}",
            ),
        )
        repository.send_message(kicked_sock, build_group_kicked_message(group_id, "kicked"))


def delete_group_for_owner(client_socket, group_id: str, repository: ChatRepository) -> None:
    group = repository.get_group(group_id)
    is_owner = bool(group and group.get("owner") == client_socket)
    if not is_owner:
        repository.send_message(client_socket, build_system_message("คุณไม่ใช่ผู้สร้างช่องแชท"))
        return

    members = repository.delete_group(group_id)
    for sock in members:
        repository.send_message(sock, build_group_deleted_message(group_id))


def transfer_group_owner(
    client_socket,
    group_id: str,
    new_owner_name: str,
    repository: ChatRepository,
) -> None:
    group = repository.get_group(group_id)
    is_owner = bool(group and group.get("owner") == client_socket)
    if not is_owner:
        repository.send_message(client_socket, build_system_message("คุณไม่ใช่ผู้สร้างช่องแชท"))
        return

    new_owner_sock = repository.get_socket_by_username(new_owner_name)
    if not new_owner_sock:
        repository.send_message(client_socket, build_system_message(f"ไม่พบผู้ใช้ '{new_owner_name}'"))
        return

    if new_owner_sock not in group["members"]:
        repository.send_message(client_socket, build_system_message(f"'{new_owner_name}' ไม่อยู่ในช่องแชท"))
        return

    transferred = repository.transfer_group_ownership(group_id, new_owner_sock)
    if transferred:
        previous_owner = repository.get_username_by_socket(client_socket) or "Old Owner"
        repository.send_to_group(
            group_id,
            build_group_chat_message(
                group_id,
                "System",
                f"👑 {previous_owner} ได้โอนสิทธิ์ให้ {new_owner_name}",
            ),
        )
        repository.send_to_group(group_id, build_group_ownership_changed_message(group_id, new_owner_name))


def add_members_to_existing_group(
    client_socket,
    group_id: str,
    requested_names: list[str],
    repository: ChatRepository,
) -> None:
    group = repository.get_group(group_id)
    is_owner = bool(group and group.get("owner") == client_socket)
    if not is_owner:
        repository.send_message(client_socket, build_system_message("คุณไม่ใช่ผู้สร้างช่องแชท"))
        return

    existing_members = set(group["members"])
    new_member_sockets = []
    added_names = []

    for name in requested_names:
        member_sock = repository.get_socket_by_username(name)
        if member_sock and member_sock not in existing_members and member_sock not in new_member_sockets:
            new_member_sockets.append(member_sock)
            added_names.append(name)

    if not new_member_sockets:
        return

    group_name = repository.add_members_to_group(group_id, new_member_sockets)
    if not group_name:
        return

    owner_name = repository.get_username_by_socket(client_socket) or "Owner"
    notify_new_members = build_group_created_message(group_id, group_name, owner_name)
    for sock in new_member_sockets:
        repository.send_message(sock, notify_new_members)

    added_list = ", ".join(added_names)
    repository.send_to_group(
        group_id,
        build_group_chat_message(
            group_id,
            "System",
            f"➕ {added_list} ถูกเพิ่มเข้าช่องแชทโดย {owner_name}",
        ),
    )


def leave_group_for_member(client_socket, group_id: str, repository: ChatRepository) -> None:
    left = repository.leave_group(group_id, client_socket, notify_leaver=True)
    if not left:
        repository.send_message(client_socket, build_system_message("คุณไม่ได้อยู่ในช่องแชทนี้"))


def send_group_message(
    client_socket,
    group_id: str,
    message_text: str,
    repository: ChatRepository,
) -> None:
    group = repository.get_group(group_id)
    if not group or client_socket not in group["members"]:
        repository.send_message(client_socket, build_system_message("ไม่สามารถส่งข้อความไปช่องแชทนี้ได้"))
        return

    sender_name = repository.get_username_by_socket(client_socket) or "Unknown"
    outbound = build_group_chat_message(group_id, sender_name, message_text)
    repository.send_to_group(group_id, outbound)

    if contains_ai_mention(message_text):
        repository.send_to_group(
            group_id,
            build_group_chat_message(group_id, "System", "AI กำลังพิมพ์คำตอบ..."),
        )
        thread = threading.Thread(
            target=_ai_group_reply,
            args=(message_text, group_id, repository),
            daemon=True,
        )
        thread.start()


def _ai_group_reply(prompt: str, group_id: str, repository: ChatRepository) -> None:
    """Fetch AI response and broadcast to a specific group."""
    from server.ai.ai_provider import get_ai_response
    from server.handlers.ai_message_handler import AI_SENDER_NAME

    try:
        clean_prompt = normalize_ai_prompt(prompt)
        ai_text = get_ai_response(clean_prompt)
        quoted_prompt = normalize_ai_prompt(prompt)
        response = build_group_chat_message(
            group_id,
            AI_SENDER_NAME,
            ai_text,
            reply_quote=quoted_prompt,
        )
        repository.send_to_group(group_id, response)
    except Exception as exc:
        repository.send_to_group(
            group_id,
            build_group_chat_message(group_id, "System", f"AI Error -> {str(exc)[:100]}"),
        )
