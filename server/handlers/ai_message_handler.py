from shared.messages import (
    build_chat_message,
    build_dm_ai_message,
    build_dm_from_message,
    build_dm_to_message,
    build_system_message,
    normalize_ai_prompt,
)
from server.ai.ai_provider import get_ai_response
from server.repositories.chat_repository import ChatRepository

AI_SENDER_NAME = "AI Assistant"


def query_ai_and_broadcast(
    prompt: str,
    original_message: str,
    sender_sock=None,
    target_sock=None,
    repository: ChatRepository | None = None,
) -> None:
    """Query AI and send the response to global chat or DM."""
    if repository is None:
        raise RuntimeError("repository is required for AI message dispatch")

    try:
        clean_prompt = normalize_ai_prompt(prompt)
        print(f"--> [AI THREAD] Querying AI for: {clean_prompt}")

        ai_text = get_ai_response(clean_prompt)
        print("--> [AI THREAD] Response received.")

        quoted = normalize_ai_prompt(original_message)

        if sender_sock and target_sock:
            if sender_sock == target_sock:
                repository.send_message(sender_sock, build_dm_from_message("AI", f"🤖 {ai_text}"))
                return

            sender_name = repository.get_username_by_socket(sender_sock) or "Unknown"
            target_name = repository.get_username_by_socket(target_sock) or "Unknown"
            ai_content = build_chat_message(AI_SENDER_NAME, ai_text, reply_quote=quoted)
            repository.send_message(sender_sock, build_dm_ai_message(target_name, ai_content))
            repository.send_message(target_sock, build_dm_ai_message(sender_name, ai_content))
            return

        ai_message = build_chat_message(AI_SENDER_NAME, ai_text, reply_quote=quoted)
        if target_sock:
            repository.send_message(target_sock, ai_message)
        else:
            repository.broadcast_message(ai_message)
    except Exception as exc:
        print(f"--> [AI THREAD] Error: {exc}")
        error_text = f"AI Error -> ไม่สามารถตอบได้ ({str(exc)[:120]})"
        quoted = normalize_ai_prompt(original_message)

        if sender_sock and target_sock:
            if sender_sock == target_sock:
                repository.send_message(sender_sock, build_dm_from_message("AI", f"❌ {error_text}"))
                return

            sender_name = repository.get_username_by_socket(sender_sock) or "Unknown"
            target_name = repository.get_username_by_socket(target_sock) or "Unknown"
            error_content = build_chat_message(AI_SENDER_NAME, error_text, reply_quote=quoted)
            repository.send_message(sender_sock, build_dm_ai_message(target_name, error_content))
            repository.send_message(target_sock, build_dm_ai_message(sender_name, error_content))
            return

        error_message = build_system_message(error_text)
        if target_sock:
            repository.send_message(target_sock, error_message)
        else:
            repository.broadcast_message(error_message)
