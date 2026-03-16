from shared.messages import (
    build_group_add_members_message,
    build_group_create_message,
    build_group_delete_message,
    build_group_kick_message,
    build_group_leave_message,
    build_group_members_request_message,
    build_group_transfer_owner_message,
)


def build_group_create_payload(name: str, members: list[str]) -> str:
    return build_group_create_message(name, members)


def build_group_kick_payload(group_id: str, username: str) -> str:
    return build_group_kick_message(group_id, username)


def build_group_owner_transfer_payload(group_id: str, new_owner: str) -> str:
    return build_group_transfer_owner_message(group_id, new_owner)


def build_add_group_members_payload(group_id: str, members: list[str]) -> str:
    return build_group_add_members_message(group_id, members)


def build_group_leave_payload(group_id: str) -> str:
    return build_group_leave_message(group_id)


def build_group_members_request_payload(group_id: str) -> str:
    return build_group_members_request_message(group_id)


def build_group_delete_payload(group_id: str) -> str:
    return build_group_delete_message(group_id)
