import json
import mimetypes
import os
from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv

load_dotenv()


class AIService:
    """
    Single Gemini integration point for all AI calls.
    """

    _client = None
    _types = None

    def __init__(self):
        self.provider = (getattr(settings, "AI_PROVIDER", "") or os.getenv("AI_PROVIDER", "gemini")).strip().lower() or "gemini"
        self.api_key = (getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model = (getattr(settings, "GEMINI_MODEL", "") or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")).strip() or "gemini-3.6-flash"

        if self.provider != "gemini":
            raise RuntimeError("AI_PROVIDER currently supports only 'gemini'.")

        if self.api_key and AIService._client is None:
            try:
                from google import genai
                from google.genai import types
            except ImportError as exc:
                raise RuntimeError(
                    "The google-genai package is not installed. Install requirements.txt before using AI features."
                ) from exc

            AIService._client = genai.Client(api_key=self.api_key)
            AIService._types = types

    @property
    def client(self):
        if AIService._client is None:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        return AIService._client

    @staticmethod
    def _normalize_json_response(response):
        if isinstance(response, dict):
            return response

        if response is None:
            return {}

        if hasattr(response, "output_text") and response.output_text:
            content = response.output_text
        else:
            content = str(response)

        content = content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end >= start:
            content = content[start : end + 1]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def generate_text(self, prompt, system_prompt=None, response_format=None):
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        config_kwargs = {"temperature": 0}
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt
        if response_format:
            config_kwargs["response_mime_type"] = "application/json"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=AIService._types.GenerateContentConfig(**config_kwargs),
        )
        return getattr(response, "text", "") or ""

    def generate_json(self, prompt, system_prompt=None):
        response = self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
        )
        return self._normalize_json_response(response)

    def analyze_image(self, prompt, file_path, system_prompt=None):
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/pdf" if path.suffix.lower() == ".pdf" else "image/png"

        with path.open("rb") as file_handle:
            file_bytes = file_handle.read()

        parts = [
            AIService._types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            prompt,
        ]

        config_kwargs = {
            "temperature": 0,
            "response_mime_type": "application/json",
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        response = self.client.models.generate_content(
            model=self.model,
            contents=parts,
            config=AIService._types.GenerateContentConfig(**config_kwargs),
        )
        content = getattr(response, "text", "") or "{}"
        return self._normalize_json_response(content)
