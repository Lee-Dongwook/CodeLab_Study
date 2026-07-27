import json
import os
import unittest
from unittest.mock import patch

from app.data_sources.openai_theme import OpenAIThemeCandidateFinder


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class OpenAIThemeCandidateFinderTests(unittest.TestCase):
    def test_uses_common_model_environment_variable_as_fallback(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-5.4-nano"}, clear=True):
            client = OpenAIThemeCandidateFinder.from_environment()

        self.assertEqual(client._model, "gpt-5.4-nano")

    def test_prefers_theme_specific_model_environment_variable(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-5.4-nano", "OPENAI_THEME_MODEL": "gpt-5.4"}, clear=True):
            client = OpenAIThemeCandidateFinder.from_environment()

        self.assertEqual(client._model, "gpt-5.4")

    def test_parses_structured_candidate_response(self) -> None:
        content = json.dumps(
            {"candidates": [{"company_name": "두산로보틱스", "related_business": "협동로봇", "relevance": "direct", "selection_reason": "협동로봇 제품을 제공"}]}
        )
        client = OpenAIThemeCandidateFinder(
            "test-key",
            opener=lambda *_args, **_kwargs: FakeResponse({"output": [{"content": [{"type": "output_text", "text": content}]}]}),
        )

        candidates = client.find_candidates("로봇")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].company_name, "두산로보틱스")
        self.assertEqual(candidates[0].relevance, "direct")

    def test_requests_up_to_ten_candidates_by_default(self) -> None:
        captured_request = None

        def opener(request, **_kwargs):
            nonlocal captured_request
            captured_request = request
            return FakeResponse({"output": [{"content": [{"type": "output_text", "text": json.dumps({"candidates": [{"company_name": "두산로보틱스", "related_business": "협동로봇", "relevance": "direct", "selection_reason": "협동로봇 제품"}]})}]}]})

        OpenAIThemeCandidateFinder("test-key", opener=opener).find_candidates("로봇")

        self.assertIsNotNone(captured_request)
        payload = json.loads(captured_request.data.decode("utf-8"))
        schema = payload["text"]["format"]["schema"]
        system_prompt = payload["input"][0]["content"][0]["text"]
        self.assertEqual(schema["properties"]["candidates"]["maxItems"], 10)
        self.assertIn("가능한 한 10개", system_prompt)
