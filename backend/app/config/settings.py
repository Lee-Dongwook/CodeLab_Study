from __future__ import annotations

import os
from pathlib import Path


def load_project_env() -> None:
    """프로젝트 루트 또는 backend 폴더의 .env를 환경변수로 읽는다.

    이미 운영 환경에서 설정한 환경변수는 덮어쓰지 않는다.
    """
    backend_directory = Path(__file__).resolve().parents[2]
    project_root = backend_directory.parent
    for env_path in (project_root / ".env", backend_directory / ".env"):
        if not env_path.is_file():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            normalized_key = key.strip()
            normalized_value = value.strip().strip('"').strip("'")
            if normalized_key:
                os.environ.setdefault(normalized_key, normalized_value)
