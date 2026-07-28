#!/usr/bin/env bash
# codelab 프로젝트용 Codex 실행 래퍼.
#
# 개인 ~/.codex/config.toml(로그인·모델) 위에, 프로젝트 sandbox/env 정책을
# -c 오버라이드로 얹어서 실행합니다. 팀원은 별도 설정 없이 이 스크립트만 쓰면 됩니다.
#
#   $ ./scripts/codex.sh            # 대화형 실행
#   $ ./scripts/codex.sh exec "..." # 하위 명령/인자 그대로 전달
#
# 정책의 원본(사람이 읽는 버전)은 .codex/config.shared.toml 를 참고하세요.
# 값을 바꿀 땐 아래 배열과 config.shared.toml 을 함께 수정하세요.
set -euo pipefail

exec codex \
  -c 'sandbox_mode="workspace-write"' \
  -c 'sandbox_workspace_write.network_access=false' \
  -c 'sandbox_workspace_write.exclude_tmpdir_env_var=false' \
  -c 'sandbox_workspace_write.exclude_slash_tmp=false' \
  -c 'shell_environment_policy.inherit="core"' \
  -c 'shell_environment_policy.exclude=["*KEY*","*SECRET*","*TOKEN*","*PASSWORD*"]' \
  "$@"
