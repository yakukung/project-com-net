import re
from typing import Optional

from .models import MessageKind, ParsedMessage

JOIN_SUFFIX = " has joined the chat!"
USERNAME_TAKEN_ERROR = "[System|ERROR]: Username already taken."

_AI_MENTION_PATTERN = re.compile(r"@ai\s*", re.IGNORECASE)
def _parse_csv_names(value: str) -> list[str]:
    return [name.strip() for name in value.split(",") if name.strip()]


def contains_ai_mention(text: str) -> bool:
    return bool(re.search(r"@ai\b", text, re.IGNORECASE))


def strip_ai_mentions(text: str) -> str:
    return _AI_MENTION_PATTERN.sub("", text).strip()


def strip_bracket_prefix(text: str) -> str:
    if text.startswith("[") and "]: " in text:
        return text.split("]: ", 1)[1]
    return text


def normalize_ai_prompt(text: str) -> str:
    return strip_bracket_prefix(strip_ai_mentions(text))


# ----- Builders: client -> server -----

def build_join_message(username: str) -> str:
    return f"{username}{JOIN_SUFFIX}"


def build_public_message(username: str, text: str) -> str:
    return f"[{username}]: {text}"


def build_dm_message(target_username: str, text: str) -> str:
    return f"@{target_username} {text}"


def build_group_chat_send_message(group_id: str, text: str) -> str:
    return f"[GROUP|MSG:{group_id}]: {text}"


def build_group_create_message(group_name: str, members: list[str]) -> str:
    return f"[GROUP|CREATE:{group_name}|MEMBERS:{','.join(members)}]"


def build_group_members_request_message(group_id: str) -> str:
    return f"[GROUP|MEMBERS:{group_id}]"


def build_group_kick_message(group_id: str, username: str) -> str:
    return f"[GROUP|KICK:{group_id}:{username}]"


def build_group_delete_message(group_id: str) -> str:
    return f"[GROUP|DELETE:{group_id}]"


def build_group_transfer_owner_message(group_id: str, new_owner: str) -> str:
    return f"[GROUP|TRANSFER_OWNER:{group_id}:{new_owner}]"


def build_group_add_members_message(group_id: str, members: list[str]) -> str:
    return f"[GROUP|ADD:{group_id}|MEMBERS:{','.join(members)}]"


def build_group_leave_message(group_id: str) -> str:
    return f"[GROUP|LEAVE:{group_id}]"


# ----- Builders: server -> client -----

def build_system_message(text: str) -> str:
    return f"[System]: {text}"


def build_username_taken_error_message() -> str:
    return USERNAME_TAKEN_ERROR


def build_user_list_message(users: list[str]) -> str:
    return f"[System|USERS:{','.join(users)}]"


def build_dm_from_message(sender: str, text: str) -> str:
    return f"[DM|FROM:{sender}]: {text}"


def build_dm_to_message(target: str, text: str) -> str:
    return f"[DM|TO:{target}]: {text}"


def build_dm_ai_message(partner: str, inner_text: str) -> str:
    return f"[DM|AI|{partner}]: {inner_text}"


def build_login_error_message(reason: str) -> str:
    return f"[System|ERROR|LOGIN:{reason}]"


def build_group_created_message(group_id: str, group_name: str, owner_name: str) -> str:
    return f"[System|GROUP_CREATED:{group_id}:{group_name}|OWNER:{owner_name}]"


def build_group_members_message(group_id: str, members: list[str], owner_name: str) -> str:
    return f"[System|GROUP_MEMBERS:{group_id}:{','.join(members)}|OWNER:{owner_name}]"


def build_group_ownership_changed_message(group_id: str, new_owner_name: str) -> str:
    return f"[System|GROUP_OWNERSHIP_CHANGED:{group_id}:{new_owner_name}]"


def build_group_kicked_message(group_id: str, reason: str) -> str:
    return f"[System|GROUP_KICKED:{group_id}]: {reason}"


def build_group_deleted_message(group_id: str) -> str:
    return f"[System|GROUP_DELETED:{group_id}]"


def build_group_chat_message(
    group_id: str,
    sender: str,
    text: str,
    reply_quote: Optional[str] = None,
) -> str:
    if reply_quote:
        return f"[GROUP|MSG:{group_id}|FROM:{sender}|REPLY:{reply_quote}]: {text}"
    return f"[GROUP|MSG:{group_id}|FROM:{sender}]: {text}"


def build_chat_message(sender: str, text: str, reply_quote: Optional[str] = None) -> str:
    if reply_quote:
        return f"[{sender}|REPLY:{reply_quote}]: {text}"
    return f"[{sender}]: {text}"


# ----- Parsers: client -> server -----

_CLIENT_GROUP_CREATE_PATTERN = re.compile(r"^\[GROUP\|CREATE:([^\]|]+)\|MEMBERS:([^\]]*)\]$")
_CLIENT_GROUP_MEMBERS_PATTERN = re.compile(r"^\[GROUP\|MEMBERS:([a-zA-Z0-9\-]{2,36})\]$")
_CLIENT_GROUP_KICK_PATTERN = re.compile(r"^\[GROUP\|KICK:([a-zA-Z0-9\-]{2,36}):([^\]:\|]+)\]$")
_CLIENT_GROUP_DELETE_PATTERN = re.compile(r"^\[GROUP\|DELETE:([a-zA-Z0-9\-]{2,36})\]$")
_CLIENT_GROUP_TRANSFER_PATTERN = re.compile(r"^\[GROUP\|TRANSFER_OWNER:([a-zA-Z0-9\-]{2,36}):([^\]:\|]+)\]$")
_CLIENT_GROUP_ADD_PATTERN = re.compile(r"^\[GROUP\|ADD:([a-zA-Z0-9\-]{2,36})\|MEMBERS:([^\]]*)\]$")
_CLIENT_GROUP_LEAVE_PATTERN = re.compile(r"^\[GROUP\|LEAVE:([a-zA-Z0-9\-]{2,36})\]$")
_CLIENT_GROUP_CHAT_PATTERN = re.compile(r"^\[GROUP\|MSG:([a-zA-Z0-9\-]{2,36})\]: (.+)$", re.DOTALL)
_CLIENT_DM_PATTERN = re.compile(r"^@(?!ai\b)(\S+)\s+(.*)", re.IGNORECASE | re.DOTALL)
_CLIENT_PUBLIC_CHAT_PATTERN = re.compile(r"^\[(.+?)\]: (.+)$", re.DOTALL)
_CLIENT_JOIN_PATTERN = re.compile(rf"^([^\[\]:|,@\s]+){re.escape(JOIN_SUFFIX)}$")


def parse_client_message(message: str) -> ParsedMessage:
    match = _CLIENT_JOIN_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.JOIN, {"username": match.group(1).strip()})

    match = _CLIENT_GROUP_CREATE_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_CREATE,
            {
                "group_name": match.group(1).strip(),
                "members": _parse_csv_names(match.group(2)),
            },
        )

    match = _CLIENT_GROUP_MEMBERS_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.GROUP_MEMBERS_REQUEST, {"group_id": match.group(1)})

    match = _CLIENT_GROUP_KICK_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_KICK,
            {"group_id": match.group(1), "username": match.group(2)},
        )

    match = _CLIENT_GROUP_DELETE_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.GROUP_DELETE, {"group_id": match.group(1)})

    match = _CLIENT_GROUP_TRANSFER_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_TRANSFER_OWNER,
            {"group_id": match.group(1), "new_owner": match.group(2)},
        )

    match = _CLIENT_GROUP_ADD_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_ADD_MEMBERS,
            {"group_id": match.group(1), "members": _parse_csv_names(match.group(2))},
        )

    match = _CLIENT_GROUP_LEAVE_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.GROUP_LEAVE, {"group_id": match.group(1)})

    match = _CLIENT_GROUP_CHAT_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_CHAT_SEND,
            {"group_id": match.group(1), "text": match.group(2)},
        )

    match = _CLIENT_DM_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.DIRECT_MESSAGE,
            {"target": match.group(1), "text": match.group(2).strip()},
        )

    match = _CLIENT_PUBLIC_CHAT_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.PUBLIC_CHAT,
            {"sender": match.group(1), "text": match.group(2)},
        )

    return ParsedMessage(MessageKind.UNKNOWN, {"raw": message})


# ----- Parsers: server -> client -----

_SERVER_USER_LIST_PATTERN = re.compile(r"^\[System\|USERS:(.*?)\]$")
_SERVER_DM_FROM_PATTERN = re.compile(r"^\[DM\|FROM:(.+?)\]: (.+)$", re.DOTALL)
_SERVER_DM_TO_PATTERN = re.compile(r"^\[DM\|TO:(.+?)\]: (.+)$", re.DOTALL)
_SERVER_DM_AI_PATTERN = re.compile(r"^\[DM\|AI\|(.+?)\]: (.+)$", re.DOTALL)
_SERVER_LOGIN_ERROR_PATTERN = re.compile(r"^\[System\|ERROR\|LOGIN:(.*?)\]$")
_SERVER_GROUP_CREATED_PATTERN = re.compile(r"^\[System\|GROUP_CREATED:(.+?):(.+?)(?:\|OWNER:(.+))?\]$")
_SERVER_GROUP_MEMBERS_PATTERN = re.compile(r"^\[System\|GROUP_MEMBERS:(.+?):(.*?)\|OWNER:(.*)\]$")
_SERVER_GROUP_OWNERSHIP_PATTERN = re.compile(r"^\[System\|GROUP_OWNERSHIP_CHANGED:(.+?):(.+?)\]$")
_SERVER_GROUP_KICKED_PATTERN = re.compile(r"^\[System\|GROUP_KICKED:(.+?)\]: (.*)$")
_SERVER_GROUP_DELETED_PATTERN = re.compile(r"^\[System\|GROUP_DELETED:(.+?)\]$")
_SERVER_GROUP_CHAT_PATTERN = re.compile(
    r"^\[GROUP\|MSG:(.+?)\|FROM:(.+?)(?:\|REPLY:(.+?))?\]: (.+)$",
    re.DOTALL,
)


def parse_server_message(message: str) -> ParsedMessage:
    if message == USERNAME_TAKEN_ERROR:
        return ParsedMessage(MessageKind.USERNAME_TAKEN_ERROR, {})

    match = _SERVER_USER_LIST_PATTERN.match(message)
    if match:
        users = [name for name in match.group(1).split(",") if name]
        return ParsedMessage(MessageKind.USERS, {"users": users})

    match = _SERVER_DM_FROM_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.DM_FROM, {"sender": match.group(1), "text": match.group(2)})

    match = _SERVER_DM_TO_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.DM_TO, {"target": match.group(1), "text": match.group(2)})

    match = _SERVER_DM_AI_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.DM_AI, {"partner": match.group(1), "inner": match.group(2)})

    match = _SERVER_LOGIN_ERROR_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.LOGIN_ERROR, {"reason": match.group(1)})

    match = _SERVER_GROUP_CREATED_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_CREATED,
            {
                "group_id": match.group(1),
                "group_name": match.group(2),
                "owner": match.group(3) or "",
            },
        )

    match = _SERVER_GROUP_MEMBERS_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_MEMBERS,
            {
                "group_id": match.group(1),
                "members": _parse_csv_names(match.group(2)),
                "owner": match.group(3),
            },
        )

    match = _SERVER_GROUP_OWNERSHIP_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_OWNERSHIP_CHANGED,
            {"group_id": match.group(1), "new_owner": match.group(2)},
        )

    match = _SERVER_GROUP_KICKED_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_KICKED,
            {"group_id": match.group(1), "reason": match.group(2)},
        )

    match = _SERVER_GROUP_DELETED_PATTERN.match(message)
    if match:
        return ParsedMessage(MessageKind.GROUP_DELETED, {"group_id": match.group(1)})

    match = _SERVER_GROUP_CHAT_PATTERN.match(message)
    if match:
        return ParsedMessage(
            MessageKind.GROUP_CHAT,
            {
                "group_id": match.group(1),
                "sender": match.group(2),
                "reply_quote": match.group(3),
                "text": match.group(4),
            },
        )

    return ParsedMessage(MessageKind.UNKNOWN, {"raw": message})
