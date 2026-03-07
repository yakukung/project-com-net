import threading
import uuid
from typing import Optional

from shared.messages import (
    build_group_chat_message,
    build_group_kicked_message,
    build_group_ownership_changed_message,
    build_system_message,
    build_user_list_message,
)
from shared.protocol import send_msg as protocol_send_msg


class ChatRepository:
    """Thread-safe in-memory repository for connected clients and groups."""

    def __init__(self) -> None:
        self.clients: dict[object, str] = {}
        self.clients_lock = threading.Lock()
        self.groups: dict[str, dict] = {}
        self.groups_lock = threading.Lock()

    def get_username_by_socket(self, sock) -> Optional[str]:
        with self.clients_lock:
            return self.clients.get(sock)

    def register_client(self, sock, requested_username: str) -> bool:
        with self.clients_lock:
            if any(name.lower() == requested_username.lower() for name in self.clients.values()):
                return False
            self.clients[sock] = requested_username
        return True

    def send_message(self, sock, message: str) -> None:
        try:
            protocol_send_msg(sock, message)
        except Exception:
            self.remove_client(sock)

    def broadcast_message(self, message: str, exclude=None) -> None:
        with self.clients_lock:
            sockets = list(self.clients.keys())

        for sock in sockets:
            if sock is exclude:
                continue
            self.send_message(sock, message)

    def broadcast_user_list(self) -> None:
        with self.clients_lock:
            names = list(self.clients.values())
        self.broadcast_message(build_user_list_message(names))

    def get_socket_by_username(self, username: str):
        with self.clients_lock:
            for sock, name in self.clients.items():
                if name.lower() == username.lower():
                    return sock
        return None

    def _send_internal(self, sock, message: str) -> None:
        try:
            protocol_send_msg(sock, message)
        except Exception:
            pass

    def _remove_member_from_group(self, group_id: str, member_sock, username: str) -> bool:
        notifications: list[tuple[object, str]] = []

        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group or member_sock not in group["members"]:
                return False

            group["members"].discard(member_sock)
            remaining_members = list(group["members"])

            if group.get("owner") == member_sock:
                if remaining_members:
                    new_owner_sock = remaining_members[0]
                    group["owner"] = new_owner_sock
                    new_owner_name = self.get_username_by_socket(new_owner_sock) or "Someone"

                    leave_notice = build_group_chat_message(
                        group_id,
                        "System",
                        f"🚪 {username} ได้ออกจากช่องแชท | 👑 {new_owner_name} ได้เป็นเจ้าของช่องแชทคนใหม่",
                    )
                    owner_signal = build_group_ownership_changed_message(group_id, new_owner_name)

                    for sock in remaining_members:
                        notifications.append((sock, leave_notice))
                        notifications.append((sock, owner_signal))
                else:
                    self.groups.pop(group_id, None)
            else:
                if not remaining_members:
                    self.groups.pop(group_id, None)
                else:
                    leave_notice = build_group_chat_message(
                        group_id,
                        "System",
                        f"🚪 {username} ได้ออกจากช่องแชท",
                    )
                    for sock in remaining_members:
                        notifications.append((sock, leave_notice))

        for sock, message in notifications:
            self._send_internal(sock, message)

        return True

    def leave_group(self, group_id: str, member_sock, notify_leaver: bool = True) -> bool:
        username = self.get_username_by_socket(member_sock)
        if not username:
            return False

        removed = self._remove_member_from_group(group_id, member_sock, username)
        if removed and notify_leaver:
            self.send_message(member_sock, build_group_kicked_message(group_id, "left"))

        return removed

    def remove_client(self, sock) -> None:
        with self.clients_lock:
            username = self.clients.pop(sock, None)

        try:
            sock.close()
        except Exception:
            pass

        if not username:
            return

        with self.groups_lock:
            group_ids = [group_id for group_id, group in self.groups.items() if sock in group["members"]]

        for group_id in group_ids:
            self._remove_member_from_group(group_id, sock, username)

        self.broadcast_message(build_system_message(f"{username} ออกจากช่องแชทแล้ว"))
        self.broadcast_user_list()

    def create_group(self, name: str, member_sockets: list, owner_sock=None) -> str:
        with self.groups_lock:
            for _ in range(10):
                group_id = str(uuid.uuid4())[:8]
                if group_id not in self.groups:
                    self.groups[group_id] = {
                        "name": name,
                        "members": set(member_sockets),
                        "owner": owner_sock,
                    }
                    return group_id

            group_id = str(uuid.uuid4())
            while group_id in self.groups:
                group_id = str(uuid.uuid4())
            self.groups[group_id] = {
                "name": name,
                "members": set(member_sockets),
                "owner": owner_sock,
            }
        return group_id

    def add_members_to_group(self, group_id: str, new_member_sockets: list) -> Optional[str]:
        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group:
                return None

            group["members"].update(new_member_sockets)
            return group["name"]

    def send_to_group(self, group_id: str, message: str, exclude=None) -> None:
        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group:
                return
            sockets = list(group["members"])

        for sock in sockets:
            if sock is exclude:
                continue
            self.send_message(sock, message)

    def get_group(self, group_id: str) -> Optional[dict]:
        with self.groups_lock:
            return self.groups.get(group_id)

    def get_group_member_names(self, group_id: str) -> list[str]:
        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group:
                return []
            sockets = list(group["members"])

        with self.clients_lock:
            return [self.clients[sock] for sock in sockets if sock in self.clients]

    def kick_member(self, group_id: str, username: str):
        target_sock = self.get_socket_by_username(username)
        if not target_sock:
            return None

        removed = self.leave_group(group_id, target_sock, notify_leaver=False)
        if not removed:
            return None

        return target_sock

    def delete_group(self, group_id: str) -> list:
        with self.groups_lock:
            group = self.groups.pop(group_id, None)
        return list(group["members"]) if group else []

    def transfer_group_ownership(self, group_id: str, new_owner_sock) -> bool:
        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group:
                return False
            group["owner"] = new_owner_sock
        return True

    def get_user_groups(self, sock) -> list[tuple[str, str]]:
        result = []
        with self.groups_lock:
            for group_id, group in self.groups.items():
                if sock in group["members"]:
                    result.append((group_id, group["name"]))
        return result


_chat_repository = ChatRepository()


def get_chat_repository() -> ChatRepository:
    return _chat_repository
