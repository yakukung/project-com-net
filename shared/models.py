from dataclasses import dataclass
from enum import Enum
from typing import Any

class MessageKind(str, Enum):
    # Client -> Server
    JOIN = "join"
    GROUP_CREATE = "group_create"
    GROUP_MEMBERS_REQUEST = "group_members_request"
    GROUP_KICK = "group_kick"
    GROUP_DELETE = "group_delete"
    GROUP_TRANSFER_OWNER = "group_transfer_owner"
    GROUP_ADD_MEMBERS = "group_add_members"
    GROUP_LEAVE = "group_leave"
    GROUP_CHAT_SEND = "group_chat_send"
    DIRECT_MESSAGE = "direct_message"
    PUBLIC_CHAT = "public_chat"

    # Server -> Client
    USERNAME_TAKEN_ERROR = "username_taken_error"
    LOGIN_ERROR = "login_error"
    USERS = "users"
    DM_FROM = "dm_from"
    DM_TO = "dm_to"
    DM_AI = "dm_ai"
    GROUP_CREATED = "group_created"
    GROUP_MEMBERS = "group_members"
    GROUP_OWNERSHIP_CHANGED = "group_ownership_changed"
    GROUP_KICKED = "group_kicked"
    GROUP_DELETED = "group_deleted"
    GROUP_CHAT = "group_chat"

    # Fallback
    UNKNOWN = "unknown"
    ERROR = "error"

@dataclass(frozen=True)
class ParsedMessage:
    kind: MessageKind
    data: dict[str, Any]
