from shared.messages import (
    build_dm_message,
    build_group_chat_send_message,
    build_public_message,
)


def build_outbound_payload(active_tab: str, username: str, message: str) -> str:
    """Map current UI context to protocol payload sent to server."""
    if active_tab.startswith("group:"):
        group_id = active_tab[6:]
        return build_group_chat_send_message(group_id, message)

    if active_tab != "group":
        if not message.startswith("@") or message.lower().startswith("@ai ") or message.lower() == "@ai":
            return build_dm_message(active_tab, message)
        return message

    if not message.startswith("@") or message.lower().startswith("@ai"):
        return build_public_message(username, message)

    return message
