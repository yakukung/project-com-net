RESERVED_USERNAMES = {
    "system",
    "ai",
    "ai assistant",
    "admin",
    "server",
    "everyone",
    "all",
    "group",
    "dm",
    "public",
    "broadcast",
    "localhost",
    "bot",
}

MAX_USERNAME_LENGTH = 24
MAX_GROUP_NAME_LENGTH = 48

_USERNAME_FORBIDDEN_CHARS = set("[]:|,@\n\r\t")
_GROUP_FORBIDDEN_CHARS = set("[]:|,\n\r\t")


def validate_username(value: str) -> str | None:
    username = value.strip()
    if not username:
        return "empty"

    if len(username) > MAX_USERNAME_LENGTH:
        return "too_long"

    if any(ch.isspace() for ch in username):
        return "invalid_chars"

    if any(ch in _USERNAME_FORBIDDEN_CHARS for ch in username):
        return "invalid_chars"

    if username.lower() in RESERVED_USERNAMES:
        return "reserved"

    return None


def validate_group_name(value: str) -> str | None:
    group_name = value.strip()
    if not group_name:
        return "empty"

    if len(group_name) > MAX_GROUP_NAME_LENGTH:
        return "too_long"

    if any(ch in _GROUP_FORBIDDEN_CHARS for ch in group_name):
        return "invalid_chars"

    if group_name.lower() in RESERVED_USERNAMES:
        return "reserved"

    return None
