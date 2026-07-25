# Backend scaffold

국내 리서치 기능을 우선 구현하기 위한 백엔드 구조다.

- `app/api`: 리서치 요청과 응답 경계
- `app/models`: 요청·결과·출처 데이터 모델
- `app/services`: 기능 분해 명세의 F-01~F-07 처리
- `app/data_sources`: KRX, DART, 기업 공식자료 등 외부 데이터 접근 계층
- `app/config`: 환경설정과 로그 설정
- `tests`: 단위·통합 테스트

현재는 Phase 1의 입력 검증, 국내 후보 필터링, 기본 데이터 조합, 뉴스·공시, 출처, Markdown 보고서 생성 흐름까지 구현되어 있다. 실제 KRX·DART·기업 자료 어댑터는 공개 데이터 제공처 선정 후 `app/data_sources`에 추가한다.
