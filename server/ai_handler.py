import re
from server import ai_service
from server.client_manager import broadcast, send_msg

def query_ai_and_broadcast(prompt, original_message, target_sock=None):
    """Query AI (via ai_handler) and broadcast (or DM) the response."""
    try:
        # Strip @ai prefix and username prefix
        clean_prompt = re.sub(r'@ai\s*', '', prompt, flags=re.IGNORECASE).strip()
        if clean_prompt.startswith("[") and "]: " in clean_prompt:
            clean_prompt = clean_prompt.split("]: ", 1)[1]

        print(f"--> [AI THREAD] Querying AI for: {clean_prompt}")

        # Call the new specialized handler
        ai_text = ai_service.get_ai_response(clean_prompt)
        
        print(f"--> [AI THREAD] Response received.")

        # Build quoted reply for UI
        quoted = original_message
        if quoted.startswith("[") and "]: " in quoted:
            quoted = quoted.split("]: ", 1)[1]
        quoted = re.sub(r'@ai\s*', '', quoted, flags=re.IGNORECASE).strip()

        # Format: [AI Name|REPLY:quoted_text]: ai_response
        ai_message = f"[Groq AI|REPLY:{quoted}]: {ai_text}"

        if target_sock:
            send_msg(target_sock, ai_message)
        else:
            broadcast(ai_message)

    except Exception as e:
        print(f"--> [AI THREAD] Error: {e}")
        error_msg = f"[System]: AI Error -> ไม่สามารถตอบได้ ({str(e)[:120]})"
        if target_sock:
            send_msg(target_sock, error_msg)
        else:
            broadcast(error_msg)
