from client.protocol.message_mapper import build_outbound_payload


def build_outbound_message(active_tab: str, username: str, text: str) -> str:
    return build_outbound_payload(active_tab, username, text)
