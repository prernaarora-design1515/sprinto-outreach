"""
Gemini backend - same three methods and the same prompts as ClaudeLLM,
using Google's `google-genai` SDK.

How the structured answer is enforced:
  We send Gemini the JSON Schema of our Pydantic model (response_json_schema),
  so it must reply with JSON of that shape. We then validate the reply with
  Pydantic. If it doesn't match, we raise LLMError instead of guessing.
"""

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

import config
from llm import (EMAIL_SYSTEM, NEXT_PAGE_SYSTEM, RESEARCH_SYSTEM, LLMError, email_user_text,
                 next_page_user_text, research_user_text)
from schemas import CompanyResearch, EmailDraftOutput, NextPageChoice

_BLOCKED = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "RECITATION", "SPII", "MODEL_ARMOR"}


def inline_schema(schema):
    """
    Pydantic puts nested models in "$defs" and points to them with "$ref".
    We copy each definition into place, so Gemini gets one plain schema
    (our models are not recursive, so this always finishes).
    """
    defs = schema.get("$defs", {})

    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].split("/")[-1]])
            return {k: resolve(v) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [resolve(v) for v in node]
        return node

    return resolve(schema)


class GeminiLLM:
    mode = "gemini"

    def __init__(self, client=None):
        # `client` can be swapped for a fake in tests.
        self.client = client or genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.GEMINI_MODEL

    def _ask(self, system, user_text, schema, max_tokens=16000):
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=inline_schema(schema.model_json_schema()),
            max_output_tokens=max_tokens,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=user_text, config=cfg)
        except errors.ClientError as e:            # 4xx - our request or key is the problem
            msg = str(e.message or e)
            if "API key" in msg or e.code in (401, 403):
                raise LLMError("Gemini API key was rejected. Check GEMINI_API_KEY in .env.")
            if e.code == 429:
                raise LLMError("Gemini rate limit or free-tier quota reached. Wait and try again.")
            if e.code == 404:
                raise LLMError(f"Gemini model '{self.model}' not found. Set GEMINI_MODEL in .env.")
            raise LLMError(f"Gemini rejected the request ({e.code}): {msg}")
        except errors.ServerError as e:            # 5xx - Google's side
            raise LLMError(f"Gemini server error {e.code}. Try again later.")
        except errors.APIError as e:
            raise LLMError(f"Gemini API error {e.code}: {e.message}")
        except Exception as e:                     # network problems etc.
            raise LLMError(f"Could not reach the Gemini API ({e.__class__.__name__}).")

        feedback = getattr(response, "prompt_feedback", None)
        if feedback is not None and getattr(feedback, "block_reason", None):
            raise LLMError(f"Gemini blocked the request ({feedback.block_reason}).")
        candidates = getattr(response, "candidates", None) or []
        reason = getattr(candidates[0], "finish_reason", None) if candidates else None
        reason_name = getattr(reason, "name", str(reason or ""))
        if reason_name == "MAX_TOKENS":
            raise LLMError("Gemini's answer was cut off (max tokens). Try fewer/shorter pages.")
        if reason_name in _BLOCKED:
            raise LLMError(f"Gemini declined to answer ({reason_name}).")

        text = getattr(response, "text", None)
        if not text:
            raise LLMError("Gemini returned an empty answer.")
        try:
            return schema.model_validate_json(text)
        except ValidationError:
            raise LLMError("Gemini's answer did not match the expected structure.")

    def extract_research(self, company_url, pages):
        return self._ask(RESEARCH_SYSTEM, research_user_text(company_url, pages), CompanyResearch)

    def choose_next_page(self, context):
        return self._ask(NEXT_PAGE_SYSTEM, next_page_user_text(context), NextPageChoice, max_tokens=4000)

    def write_email(self, context):
        return self._ask(EMAIL_SYSTEM, email_user_text(context), EmailDraftOutput, max_tokens=8000)
