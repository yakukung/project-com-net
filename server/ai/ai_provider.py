import os

import google.generativeai as genai
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "gemini-2.5-flash-lite"

SYSTEM_PROMPT = (
    "You are a helpful AI assistant in a group chat. "
    "Be concise and friendly. "
    "Answer in the same language as the user's message."
)

_groq_api_key = os.getenv("GROQ_API_KEY")
_gemini_api_key = os.getenv("GEMINI_API_KEY")

_groq_client = Groq(api_key=_groq_api_key) if _groq_api_key else None
if _gemini_api_key:
    genai.configure(api_key=_gemini_api_key)


def _query_groq(prompt: str) -> str:
    if _groq_client is None:
        raise RuntimeError("GROQ_API_KEY is not set")

    response = _groq_client.chat.completions.create(
        model=PRIMARY_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _query_gemini(prompt: str) -> str:
    if not _gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = genai.GenerativeModel(FALLBACK_MODEL)
    response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUser: {prompt}")
    return response.text


def get_ai_response(prompt: str) -> str:
    errors = []

    try:
        print(f"--> [AI SERVICE] Fetching from Groq ({PRIMARY_MODEL})...")
        return _query_groq(prompt)
    except Exception as exc:
        print(f"--> [AI SERVICE] Groq Error: {exc}")
        errors.append(f"Groq: {str(exc)[:80]}")

    try:
        print(f"--> [AI SERVICE] Falling back to Gemini ({FALLBACK_MODEL})...")
        return _query_gemini(prompt)
    except Exception as exc:
        print(f"--> [AI SERVICE] Gemini Error: {exc}")
        errors.append(f"Gemini: {str(exc)[:80]}")

    joined_errors = " | ".join(errors)
    raise RuntimeError(f"AI unavailable. {joined_errors}")
