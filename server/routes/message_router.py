from shared.models import MessageKind, ParsedMessage
from shared.messages import build_system_message
from server.repositories.chat_repository import ChatRepository
from server.services import block_service, direct_message_service, group_service, session_service


class MessageRouter:
    def __init__(self, repository: ChatRepository) -> None:
        self.repository = repository

    def route(
        self,
        parsed: ParsedMessage,
        raw_message: str,
        client_socket,
        username: str | None,
    ) -> str | None:
        if username is None and parsed.kind != MessageKind.JOIN:
            self.repository.send_message(client_socket, build_system_message("กรุณาเข้าสู่แชตก่อนส่งคำสั่ง"))
            return username

        if parsed.kind == MessageKind.JOIN:
            if username is None:
                return session_service.join_client(
                    client_socket,
                    parsed.data["username"],
                    self.repository,
                )

            direct_message_service.send_public_message(client_socket, raw_message, self.repository)
            return username

        if parsed.kind == MessageKind.BLOCK_USER:
            block_service.block_user_by_ip(client_socket, parsed.data["target_username"], self.repository)
            return username

        if parsed.kind == MessageKind.UNBLOCK_USER:
            block_service.unblock_user_by_ip(client_socket, parsed.data["target_username"], self.repository)
            return username

        if parsed.kind == MessageKind.GROUP_CREATE:
            group_service.create_group_for_owner(
                client_socket,
                parsed.data["group_name"],
                parsed.data["members"],
                self.repository,
            )
            return username

        if parsed.kind == MessageKind.GROUP_MEMBERS_REQUEST:
            group_service.send_group_members(client_socket, parsed.data["group_id"], self.repository)
            return username

        if parsed.kind == MessageKind.GROUP_KICK:
            group_service.kick_member_from_group(
                client_socket,
                parsed.data["group_id"],
                parsed.data["username"],
                self.repository,
            )
            return username

        if parsed.kind == MessageKind.GROUP_DELETE:
            group_service.delete_group_for_owner(client_socket, parsed.data["group_id"], self.repository)
            return username

        if parsed.kind == MessageKind.GROUP_TRANSFER_OWNER:
            group_service.transfer_group_owner(
                client_socket,
                parsed.data["group_id"],
                parsed.data["new_owner"],
                self.repository,
            )
            return username

        if parsed.kind == MessageKind.GROUP_ADD_MEMBERS:
            group_service.add_members_to_existing_group(
                client_socket,
                parsed.data["group_id"],
                parsed.data["members"],
                self.repository,
            )
            return username

        if parsed.kind == MessageKind.GROUP_LEAVE:
            group_service.leave_group_for_member(client_socket, parsed.data["group_id"], self.repository)
            return username

        if parsed.kind == MessageKind.GROUP_CHAT_SEND:
            group_service.send_group_message(
                client_socket,
                parsed.data["group_id"],
                parsed.data["text"],
                self.repository,
            )
            return username

        if parsed.kind == MessageKind.DIRECT_MESSAGE:
            direct_message_service.send_direct_message(
                client_socket,
                parsed.data["target"],
                parsed.data["text"],
                self.repository,
            )
            return username

        if parsed.kind == MessageKind.PUBLIC_CHAT:
            direct_message_service.send_public_message(
                client_socket,
                parsed.data["text"],
                self.repository,
            )
            return username

        direct_message_service.send_public_message(client_socket, raw_message, self.repository)
        return username
