import json
import unittest

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
