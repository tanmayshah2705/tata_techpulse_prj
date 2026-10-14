"""
gemini_integration.py
AutoCodeGuard — Gemini API integration for LLM-powered code review.

- Reads the API key from the GEMINI_API_KEY environment variable (via .env).
- Reads the model name from Model_Prompts_Config/model_config.json.
- Returns structured findings via JSON mode.
- Never executes user code or modifies local files.
- Handles quota, auth, network, and parse errors gracefully.
"""

import json
import os
import textwrap
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent.parent / "Model_Prompts_Config" / "model_config.json"

_FALLBACK_MODEL = "gemini-3.8-flash"


def _load_model_name() -> str:
    """Load model name from model_config.json; fall back to gemini-3.8-flash."""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        return cfg.get("model_name", _FALLBACK_MODEL)
    except Exception:
        return _FALLBACK_MODEL


MODEL_NAME = _load_model_name()

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""\
    You are an automotive software security expert reviewing source code
    for potential defects and security issues.

    IMPORTANT CONSTRAINTS:
    - You are a read-only reviewer. Do NOT execute code. Do NOT modify files.
    - Label all findings as POTENTIAL issues (not confirmed vulnerabilities).
    - Your line numbers are best-effort estimates; clearly note they are approximate.
    - Focus on code quality, security patterns, and automotive/safety concerns.
    - Be concise and constructive.
""")

_USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    Please review the following {language} source code for potential defects,
    security issues, and coding-guideline violations.

    SOURCE CODE:
    ```{language}
    {code}
    ```

    Respond with ONLY valid JSON matching this schema (no markdown, no extra text):
    {{
      "summary": "<one-paragraph overall assessment>",
      "findings": [
        {{
          "severity": "HIGH|MEDIUM|LOW",
          "title": "<short finding title>",
          "approximate_line": <integer or null>,
          "evidence": "<relevant code snippet>",
          "explanation": "<why this is potentially problematic>",
          "recommendation": "<specific actionable fix>"
        }}
      ],
      "overall_risk": "HIGH|MEDIUM|LOW|NONE"
    }}

    If there are no findings, return an empty findings array.
    Do not fabricate issues that do not exist in the code.
""")


# Ordered list of fallback model names tried when the primary model is unavailable.
# Primary model is read from model_config.json; these are automatic fallbacks on 503.
_FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class GeminiReviewer:
    def __init__(self):
        self._api_key = os.environ.get("GEMINI_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file and restart the application."
            )
        try:
            import google.genai as genai
            self._client = genai.Client(api_key=self._api_key)
            return self._client
        except ImportError as exc:
            raise ImportError(
                "google-genai package not found. "
                "Run: pip install google-genai"
            ) from exc

    def review(self, source_code: str, language: str = "python") -> dict:
        """
        Send source_code to Gemini for review.
        Returns a dict with keys: summary, findings, overall_risk, error (if any).
        Never returns None; always returns a valid dict.
        """
        if not source_code or not source_code.strip():
            return {
                "summary": "No code submitted.",
                "findings": [],
                "overall_risk": "NONE",
                "error": None,
            }

        try:
            client = self._get_client()
        except (ValueError, ImportError) as exc:
            return self._error_response(str(exc))

        prompt = _USER_PROMPT_TEMPLATE.format(
            language=language,
            code=source_code,
        )

        # Build the ordered list of models to try: configured model first, then fallbacks
        models_to_try = [MODEL_NAME]
        for fb in _FALLBACK_MODELS:
            if fb != MODEL_NAME:
                models_to_try.append(fb)

        last_error: str = "Gemini API error: unknown error."
        import google.genai.types as types

        for attempt_model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=attempt_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                        max_output_tokens=4096,
                    ),
                )
                raw_text = response.text or ""
                result = self._parse_response(raw_text)
                # Annotate which model actually responded if it differed from configured
                if attempt_model != MODEL_NAME:
                    result["model_used"] = attempt_model
                    result["model_note"] = (
                        f"Primary model '{MODEL_NAME}' was unavailable; "
                        f"responded via fallback '{attempt_model}'."
                    )
                else:
                    result["model_used"] = attempt_model
                return result

            except Exception as exc:
                err_str = str(exc)
                # Only retry on 503/UNAVAILABLE; all other errors are final
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    last_error = err_str
                    continue  # try next fallback model
                # Non-retriable errors — classify and return immediately
                if "API_KEY_INVALID" in err_str or "401" in err_str:
                    friendly = (
                        "Invalid API key. Check your GEMINI_API_KEY in .env and "
                        "ensure it is active at https://aistudio.google.com/app/apikey"
                    )
                elif "QUOTA" in err_str.upper() or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    friendly = (
                        "API quota exceeded or rate-limited (HTTP 429). "
                        "Wait a minute and retry, or check your billing at "
                        "https://console.cloud.google.com/billing"
                    )
                elif "404" in err_str or "NOT_FOUND" in err_str:
                    friendly = (
                        f"Model '{attempt_model}' was not found (HTTP 404). "
                        "The model may have been deprecated. Update 'model_name' in "
                        "Model_Prompts_Config/model_config.json. "
                        f"Currently available models include: gemini-3.8-flash, gemini-3.6-flash. "
                        f"API message: {err_str[:300]}"
                    )
                elif "ConnectionError" in err_str or "timeout" in err_str.lower() or "ConnectError" in err_str:
                    friendly = (
                        "Network error connecting to the Gemini API. "
                        "Check your internet connection and try again."
                    )
                else:
                    friendly = f"Gemini API error: {err_str}"
                return self._error_response(friendly)

        # All models returned 503 — report the transient error
        models_tried = ", ".join(models_to_try)
        return self._error_response(
            f"All Gemini models are temporarily unavailable (HTTP 503 — high demand). "
            f"Models tried: {models_tried}. "
            "This is a transient server-side issue. Wait 30–60 seconds and try again."
        )

    @staticmethod
    def _parse_response(raw_text: str) -> dict:
        """Validate and return the parsed JSON response."""
        raw_text = raw_text.strip()
        # Strip markdown fences if present
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_text

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return {
                "summary": "Gemini returned a non-JSON response.",
                "findings": [],
                "overall_risk": "UNKNOWN",
                "error": f"JSON parse error. Raw response: {raw_text[:500]}",
            }

        # Normalise to expected schema
        return {
            "summary": str(data.get("summary", "")),
            "findings": _normalise_findings(data.get("findings", [])),
            "overall_risk": str(data.get("overall_risk", "UNKNOWN")),
            "error": None,
        }

    @staticmethod
    def _error_response(message: str) -> dict:
        return {
            "summary": "",
            "findings": [],
            "overall_risk": "UNKNOWN",
            "error": message,
        }

    def is_api_key_set(self) -> bool:
        return bool(self._api_key)


def _normalise_findings(raw: list) -> list:
    """Ensure each finding has required keys; drop malformed entries."""
    normalised = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        normalised.append({
            "severity": str(item.get("severity", "UNKNOWN")).upper(),
            "title": str(item.get("title", "Untitled")),
            "approximate_line": item.get("approximate_line"),
            "evidence": str(item.get("evidence", "")),
            "explanation": str(item.get("explanation", "")),
            "recommendation": str(item.get("recommendation", "")),
        })
    return normalised


# Module-level singleton
_reviewer: Optional[GeminiReviewer] = None


def get_reviewer() -> GeminiReviewer:
    global _reviewer
    if _reviewer is None:
        _reviewer = GeminiReviewer()
    return _reviewer
