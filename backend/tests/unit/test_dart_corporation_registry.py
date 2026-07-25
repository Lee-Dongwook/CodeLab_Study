import io
import unittest
import zipfile

from app.data_sources.dart_corporation_registry import DartCorporationRegistry


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


def create_archive() -> bytes:
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<result>
  <list><corp_code>00264529</corp_code><corp_name>두산로보틱스</corp_name><stock_code>454910</stock_code></list>
  <list><corp_code>00120182</corp_code><corp_name>NH투자증권</corp_name><stock_code>005940</stock_code></list>
  <list><corp_code>99999999</corp_code><corp_name>비상장회사</corp_name><stock_code> </stock_code></list>
</result>""".encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("CORPCODE.xml", xml)
    return buffer.getvalue()


class DartCorporationRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calls = 0

        def opener(*_args, **_kwargs):
            self.calls += 1
            return FakeResponse(create_archive())

        self.registry = DartCorporationRegistry("test-api-key", opener=opener)

    def test_resolves_company_name_to_stock_and_corp_code(self) -> None:
        company = self.registry.resolve("두산로보틱스")

        self.assertIsNotNone(company)
        self.assertEqual(company.stock_code, "454910")
        self.assertEqual(company.corp_code, "00264529")

    def test_resolves_stock_code_and_caches_corporation_list(self) -> None:
        first = self.registry.resolve("005940")
        second = self.registry.resolve("NH투자증권")

        self.assertEqual(first.name, "NH투자증권")
        self.assertEqual(second.corp_code, "00120182")
        self.assertEqual(self.calls, 1)

    def test_ignores_unlisted_company(self) -> None:
        self.assertIsNone(self.registry.resolve("비상장회사"))
