import os
import re
from groq import Groq
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.5-flash-lite"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

SYSTEM_PROMPT = "You are a helpful AI assistant in a group chat. Be concise and friendly. Answer in the same language as the user's message."

def _query_groq(prompt):
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024,
        temperature=0.7
    )
    return response.choices[0].message.content

def _query_gemini(prompt):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(full_prompt)
    return response.text

def get_ai_response(clean_prompt):
    try:
        print(f"--> [AI SERVICE] Fetching from Groq ({GROQ_MODEL})...")
        return _query_groq(clean_prompt)
    except Exception as groq_err:
        print(f"--> [AI SERVICE] Groq Error: {groq_err}")
        
    try:
        print(f"--> [AI SERVICE] Falling back to Gemini ({GEMINI_MODEL})...")
        return _query_gemini(clean_prompt)
    except Exception as gemini_err:
        print(f"--> [AI SERVICE] Gemini Error: {gemini_err}")
        
    raise Exception(f"AI Unavailable. (Groq: {str(groq_err)[:50]}, Gemini: {str(gemini_err)[:50]})")
