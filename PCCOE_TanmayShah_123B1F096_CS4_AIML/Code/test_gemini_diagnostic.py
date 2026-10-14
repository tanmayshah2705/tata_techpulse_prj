"""
test_gemini_diagnostic.py
AutoCodeGuard — Minimal diagnostic script for Google Gemini API integration.

Tests the configured GEMINI_API_KEY against candidate models without exposing secrets.

Usage:
    python test_gemini_diagnostic.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root or parent
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("[ERROR] GEMINI_API_KEY environment variable is not set in .env.")
    sys.exit(1)

# Safe masked display (never print actual key)
masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
print(f"[INFO] GEMINI_API_KEY detected: {masked_key} (length: {len(api_key)})")

try:
    import google.genai as genai
    import google.genai.types as types
except ImportError:
    print("[ERROR] google-genai library not found. Run: pip install google-genai")
    sys.exit(1)

client = genai.Client(api_key=api_key)

test_prompt = "Identify the security risk in this Python code: eval(user_input)"
models_to_test = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

print(f"\n[TEST] Testing prompt: '{test_prompt}'\n")

for model in models_to_test:
    print(f"Testing model: {model} ... ", end="", flush=True)
    try:
        response = client.models.generate_content(
            model=model,
            contents=test_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=300,
            ),
        )
        print("SUCCESS (HTTP 200)")
        preview = response.text.strip().replace("\n", " ")[:140] if response.text else "(empty)"
        print(f"       Response preview: {preview}...\n")
        break
    except Exception as exc:
        err_msg = str(exc)
        if "503" in err_msg or "UNAVAILABLE" in err_msg:
            print("FAILED -> 503 UNAVAILABLE (Model server temporarily at capacity)")
        elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            print("FAILED -> 429 RESOURCE_EXHAUSTED (Quota limit reached for this tier)")
        elif "404" in err_msg or "NOT_FOUND" in err_msg:
            print("FAILED -> 404 NOT_FOUND (Model discontinued or unsupported)")
        elif "401" in err_msg or "API_KEY_INVALID" in err_msg:
            print("FAILED -> 401 INVALID_KEY (Check API key validity)")
        else:
            print(f"FAILED -> {type(exc).__name__}: {err_msg[:80]}")
