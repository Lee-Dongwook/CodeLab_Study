import unittest

from app.models.errors import InputValidationError
from app.services.input_validator import validate_request


class ValidateRequestTests(unittest.TestCase):
    def test_accepts_theme_and_positive_top_n(self) -> None:
        request = validate_request("  AI   반도체 ", 3)

        self.assertEqual(request.theme, "AI 반도체")
        self.assertEqual(request.top_n, 3)

    def test_accepts_domestic_company_name(self) -> None:
        request = validate_request("두산로보틱스", 1)

        self.assertEqual(request.theme, "두산로보틱스")

    def test_rejects_blank_theme(self) -> None:
        with self.assertRaises(InputValidationError):
            validate_request("   ", 3)

    def test_rejects_numeric_only_theme(self) -> None:
        with self.assertRaises(InputValidationError):
            validate_request("454910", 3)

    def test_rejects_invalid_top_n(self) -> None:
        for value in (0, -1, "3", True):
            with self.subTest(value=value):
                with self.assertRaises(InputValidationError):
                    validate_request("로봇", value)
