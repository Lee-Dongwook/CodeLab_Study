class InputValidationError(ValueError):
    """사용자가 수정할 수 있는 입력 오류."""


class PublicDataUnavailableError(RuntimeError):
    """필수 공개 데이터 제공처를 사용할 수 없을 때 발생하는 오류."""
