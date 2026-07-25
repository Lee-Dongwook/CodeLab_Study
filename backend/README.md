# Backend scaffold

국내 리서치 기능을 우선 구현하기 위한 백엔드 구조다.

- `app/api`: 리서치 요청과 응답 경계
- `app/models`: 요청·결과·출처 데이터 모델
- `app/services`: 기능 분해 명세의 F-01~F-07 처리
- `app/data_sources`: KRX, DART, 기업 공식자료 등 외부 데이터 접근 계층
- `app/config`: 환경설정과 로그 설정
- `tests`: 단위·통합 테스트

현재는 폴더와 모듈 위치만 만든 상태이며, 기능 로직은 포함하지 않는다.
