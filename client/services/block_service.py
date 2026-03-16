from shared.messages import build_block_user_message, build_unblock_user_message


def build_block_user_payload(target_username: str) -> str:
    return build_block_user_message(target_username)


def build_unblock_user_payload(target_username: str) -> str:
    return build_unblock_user_message(target_username)
