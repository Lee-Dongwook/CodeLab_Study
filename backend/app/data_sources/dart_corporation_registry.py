from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree

from app.config import load_project_env
from app.models.domain import DomesticCompanyIdentity
from app.models.errors import DartApiError, PublicDataUnavailableError

_CORP_CODE_API_URL = "https://opendart.fss.or.kr/api/corpCode.xml"


@dataclass(frozen=True)
class DartCorporationRegistry:
    """OpenDART 고유번호 목록에서 국내 상장 종목을 식별한다."""

    api_key: str
    opener: Callable[..., Any] = urlopen
    timeout_seconds: int = 20

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise PublicDataUnavailableError("DART_API_KEY 환경변수가 설정되지 않았습니다.")
        object.__setattr__(self, "_companies", None)

    @classmethod
    def from_environment(cls) -> "DartCorporationRegistry":
        load_project_env()
        return cls(os.getenv("DART_API_KEY", ""))

    def resolve(self, normalized_input: str) -> DomesticCompanyIdentity | None:
        search_key = _company_key(normalized_input)
        for company in self._load_companies():
            if company.stock_code == normalized_input or _company_key(company.name) == search_key:
                return company
        return None

    def _load_companies(self) -> tuple[DomesticCompanyIdentity, ...]:
        cached = self._companies
        if cached is not None:
            return cached

        request_url = f"{_CORP_CODE_API_URL}?{urlencode({'crtfc_key': self.api_key})}"
        try:
            with self.opener(request_url, timeout=self.timeout_seconds) as response:
                archive_bytes = response.read()
            with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
                xml_name = next(name for name in archive.namelist() if name.lower().endswith(".xml"))
                xml_bytes = archive.read(xml_name)
            root = ElementTree.fromstring(xml_bytes)
        except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError, StopIteration) as error:
            raise DartApiError("OpenDART 기업 고유번호 목록을 조회하지 못했습니다.") from error

        companies = tuple(
            DomesticCompanyIdentity(
                name=(item.findtext("corp_name") or "").strip(),
                stock_code=(item.findtext("stock_code") or "").strip(),
                corp_code=(item.findtext("corp_code") or "").strip() or None,
            )
            for item in root.findall("list")
            if (item.findtext("stock_code") or "").strip()
        )
        object.__setattr__(self, "_companies", companies)
        return companies


def _company_key(value: str) -> str:
    return value.lower().replace(" ", "").replace("주식회사", "").replace("(주)", "").replace("㈜", "")
