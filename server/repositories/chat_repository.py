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
        self.client_ips: dict[object, str] = {}
        self.blocked_ips_by_client: dict[object, set[str]] = {}
        self.blocked_targets_by_client: dict[object, dict[str, str]] = {}
        self.clients_lock = threading.Lock()
        self.groups: dict[str, dict] = {}
        self.groups_lock = threading.Lock()

    def get_username_by_socket(self, sock) -> Optional[str]:
        with self.clients_lock:
            return self.clients.get(sock)

    def _resolve_socket_ip(self, sock) -> Optional[str]:
        try:
            peer = sock.getpeername()
            if isinstance(peer, tuple) and peer:
                return str(peer[0])
        except Exception:
            return None
        return None

    def get_client_ip(self, sock) -> Optional[str]:
        with self.clients_lock:
            ip = self.client_ips.get(sock)
        return ip or self._resolve_socket_ip(sock)

    def register_client(self, sock, requested_username: str, client_ip: Optional[str] = None) -> bool:
        resolved_ip = client_ip or self._resolve_socket_ip(sock)
        with self.clients_lock:
            if any(name.lower() == requested_username.lower() for name in self.clients.values()):
                return False
            self.clients[sock] = requested_username
            if resolved_ip:
                self.client_ips[sock] = resolved_ip
            self.blocked_ips_by_client.setdefault(sock, set())
            self.blocked_targets_by_client.setdefault(sock, {})
        return True

    def is_sender_blocked_for_recipient(self, sender_sock, recipient_sock) -> bool:
        if not sender_sock or sender_sock is recipient_sock:
            return False

        sender_ip = self.get_client_ip(sender_sock)
        if not sender_ip:
            return False

        with self.clients_lock:
            blocked_ips = self.blocked_ips_by_client.get(recipient_sock, set())
            return sender_ip in blocked_ips

    def block_user_ip(self, blocker_sock, target_username: str) -> str:
        target_sock = self.get_socket_by_username(target_username)
        if not target_sock:
            return "target_not_found"
        if target_sock is blocker_sock:
            return "cannot_block_self"

        target_ip = self.get_client_ip(target_sock)
        if not target_ip:
            return "target_ip_unknown"

        with self.clients_lock:
            blocked_ips = self.blocked_ips_by_client.setdefault(blocker_sock, set())
            blocked_targets = self.blocked_targets_by_client.setdefault(blocker_sock, {})
            blocked_targets[target_username.lower()] = target_ip
            if target_ip in blocked_ips:
                return "already_blocked"
            blocked_ips.add(target_ip)
        return "ok"

    def unblock_user_ip(self, blocker_sock, target_username: str) -> str:
        target_key = target_username.lower()
        target_sock = self.get_socket_by_username(target_username)
        if target_sock is blocker_sock:
            return "cannot_unblock_self"

        target_ip = self.get_client_ip(target_sock) if target_sock else None

        with self.clients_lock:
            blocked_ips = self.blocked_ips_by_client.setdefault(blocker_sock, set())
            blocked_targets = self.blocked_targets_by_client.setdefault(blocker_sock, {})
            if not target_ip:
                target_ip = blocked_targets.get(target_key)
            if target_ip not in blocked_ips:
                return "not_blocked"
            blocked_ips.remove(target_ip)
            for blocked_name, blocked_ip in list(blocked_targets.items()):
                if blocked_name == target_key or blocked_ip == target_ip:
                    blocked_targets.pop(blocked_name, None)
        return "ok"

    def send_message_from(self, sender_sock, recipient_sock, message: str) -> bool:
        if self.is_sender_blocked_for_recipient(sender_sock, recipient_sock):
            return False
        self.send_message(recipient_sock, message)
        return True

    def send_message(self, sock, message: str) -> None:
        try:
            protocol_send_msg(sock, message)
        except Exception:
            self.remove_client(sock)

    def broadcast_message(self, message: str, exclude=None, sender_sock=None) -> None:
        with self.clients_lock:
            sockets = list(self.clients.keys())

        for sock in sockets:
            if sock is exclude:
                continue
            if self.is_sender_blocked_for_recipient(sender_sock, sock):
                continue
            self.send_message(sock, message)

    def broadcast_user_list(self) -> None:
        with self.clients_lock:
            client_items = list(self.clients.items())
            ip_map = dict(self.client_ips)
            blocked_map = {sock: set(ips) for sock, ips in self.blocked_ips_by_client.items()}

        for recipient_sock, _ in client_items:
            blocked_ips = blocked_map.get(recipient_sock, set())
            visible_names: list[str] = []
            for sender_sock, sender_name in client_items:
                sender_ip = ip_map.get(sender_sock)
                if sender_sock is not recipient_sock and sender_ip and sender_ip in blocked_ips:
                    continue
                visible_names.append(sender_name)
            self.send_message(recipient_sock, build_user_list_message(visible_names))

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
                        if not self.is_sender_blocked_for_recipient(member_sock, sock):
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
                        if not self.is_sender_blocked_for_recipient(member_sock, sock):
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
            self.client_ips.pop(sock, None)
            self.blocked_ips_by_client.pop(sock, None)
            self.blocked_targets_by_client.pop(sock, None)

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

        self.broadcast_message(build_system_message(f"{username} ออกจากช่องแชทแล้ว"), sender_sock=sock)
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

    def send_to_group(self, group_id: str, message: str, exclude=None, sender_sock=None) -> None:
        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group:
                return
            sockets = list(group["members"])

        for sock in sockets:
            if sock is exclude:
                continue
            if self.is_sender_blocked_for_recipient(sender_sock, sock):
                continue
            self.send_message(sock, message)

    def get_group(self, group_id: str) -> Optional[dict]:
        with self.groups_lock:
            return self.groups.get(group_id)

    def get_group_member_names(self, group_id: str, viewer_sock=None) -> list[str]:
        with self.groups_lock:
            group = self.groups.get(group_id)
            if not group:
                return []
            sockets = list(group["members"])

        with self.clients_lock:
            blocked_ips = set(self.blocked_ips_by_client.get(viewer_sock, set())) if viewer_sock else set()
            result: list[str] = []
            for sock in sockets:
                username = self.clients.get(sock)
                if not username:
                    continue
                if viewer_sock and sock is not viewer_sock:
                    sender_ip = self.client_ips.get(sock)
                    if sender_ip and sender_ip in blocked_ips:
                        continue
                result.append(username)
            return result

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

    def is_group_name_exists(self, name: str) -> bool:
        """Check if a group name already exists (case-insensitive)."""
        target_name = name.lower().strip()
        with self.groups_lock:
            for group in self.groups.values():
                if group["name"].lower().strip() == target_name:
                    return True
        return False


_chat_repository = ChatRepository()


def get_chat_repository() -> ChatRepository:
    return _chat_repository
