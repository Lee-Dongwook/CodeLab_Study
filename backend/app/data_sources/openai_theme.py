from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Sequence
from urllib.request import Request, urlopen

from app.config import load_project_env
from app.models.errors import PublicDataUnavailableError

_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class ThemeCandidateSuggestion:
    company_name: str
    related_business: str
    relevance: str
    selection_reason: str


class OpenAIThemeCandidateFinder:
    """테마 키워드에 대한 국내 상장사 후보를 제안받는 어댑터.

    모델 응답은 후보 탐색에만 사용한다. 실제 분석 대상은 호출부에서 DART
    상장 종목 목록으로 재식별해야 한다.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        opener: Callable[..., Any] = urlopen,
        timeout_seconds: int = 20,
    ) -> None:
        if not api_key.strip():
            raise PublicDataUnavailableError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        self._api_key = api_key
        self._model = model
        self._opener = opener
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(cls) -> "OpenAIThemeCandidateFinder":
        load_project_env()
        return cls(os.getenv("OPENAI_API_KEY", ""), model=os.getenv("OPENAI_THEME_MODEL", "gpt-4o-mini"))

    def find_candidates(self, theme: str, *, limit: int = 5) -> Sequence[ThemeCandidateSuggestion]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "candidates": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": limit,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "company_name": {"type": "string"},
                            "related_business": {"type": "string"},
                            "relevance": {"type": "string", "enum": ["direct", "indirect"]},
                            "selection_reason": {"type": "string"},
                        },
                        "required": ["company_name", "related_business", "relevance", "selection_reason"],
                    },
                }
            },
            "required": ["candidates"],
        }
        payload = {
            "model": self._model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "한국 KRX 상장 보통주 테마 리서치 후보 탐색기다. 투자 추천이나 순위를 만들지 말고, 입력 테마와 사업 연관성이 높은 국내 상장 기업명만 3~5개 제안하라. ETF, ETN, 우선주, SPAC, 비상장사는 제외한다. 모든 설명은 짧고 사실 중심으로 작성한다."}],
                },
                {"role": "user", "content": [{"type": "input_text", "text": f"테마: {theme}"}]},
            ],
            "text": {"format": {"type": "json_schema", "name": "krx_theme_candidates", "strict": True, "schema": schema}},
        }
        request = Request(
            _RESPONSES_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as error:
            raise PublicDataUnavailableError("OpenAI 테마 후보 탐색을 완료하지 못했습니다.") from error

        try:
            parsed = json.loads(_output_text(response_payload))
            candidates = parsed["candidates"]
        except (KeyError, TypeError, ValueError) as error:
            raise PublicDataUnavailableError("OpenAI 테마 후보 응답 형식이 올바르지 않습니다.") from error

        suggestions = []
        for candidate in candidates[:limit]:
            if not isinstance(candidate, dict):
                continue
            name = str(candidate.get("company_name", "")).strip()
            if not name:
                continue
            suggestions.append(
                ThemeCandidateSuggestion(
                    company_name=name,
                    related_business=str(candidate.get("related_business", "")).strip(),
                    relevance=str(candidate.get("relevance", "indirect")),
                    selection_reason=str(candidate.get("selection_reason", "")).strip(),
                )
            )
        if not suggestions:
            raise PublicDataUnavailableError("OpenAI가 확인 가능한 국내 후보를 반환하지 않았습니다.")
        return tuple(suggestions)


def _output_text(payload: dict[str, Any]) -> str:
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("output_text가 없습니다.")
