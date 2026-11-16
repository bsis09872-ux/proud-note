# 🌱 Proud Note API

오늘 **알게 된 것 · 해낸 것 · 오늘의 나**를 기록하고, 친구들이 이모지로 칭찬해 주는 TIL 게시판 API.

- **배포 주소**: `http://<EC2 주소>/docs`
- **스택**: Python 3.13 · FastAPI · SQLAlchemy 2 (async) · PostgreSQL 17 · Alembic · JWT(HS512) · Docker

## 공간 정책

| 정책 | 🏡 friends | 🌏 plaza |
|---|---|---|
| 열람 / 작성 | 회원 / 회원 | 누구나 / 회원+비회원 |
| 작성자 표시 | 닉네임 | 익명 |
| 하루 작성 | 무제한 | 1인 1개 |
| 보관 | 무제한 | 최신 50개 |
| 댓글 / 반응 | O / 회원 | X / 회원 |

- 비회원은 비밀번호를 걸고 쓰고, 수정·삭제할 때 `X-Guest-Password` 헤더로 검증해요.
- 커스텀 이모지는 슬랙처럼 직접 등록해서 `:name:` 형식으로 반응할 수 있어요.

## 실행

```bash
cp .env.example .env          # JWT_SECRET_KEY 는 64자 이상으로 채우기
docker compose up -d          # 로컬 PostgreSQL
uv sync
uv run alembic upgrade head   # 테이블 + 기본 공간 생성
uv run uvicorn main:app --reload --app-dir src
```

- API 문서: http://localhost:8000/docs
- 테스트: `uv run pytest`. 테스트 전용 DB(`proud_note_test`)는 자동으로 만들어져요.
- 관리자 지정: `PYTHONPATH=src uv run python scripts/promote_admin.py <email>`

## 배포 (EC2)

```bash
cp .env.prod.example .env.prod   # 값 채우기
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

## API

| 구분 | 엔드포인트 |
|---|---|
| 회원 | `POST /v1/users` · `GET/PATCH/DELETE /v1/users/me` · `PATCH /v1/users/me/password` |
| 인증 | `POST /v1/auth/login` · `POST /v1/auth/logout` |
| 공간 | `GET /v1/spaces` · `GET/PATCH /v1/spaces/{id}` (수정은 관리자) |
| 노트 | `GET/POST /v1/spaces/{id}/notes` (`?tag=`, `?keyword=`) · `GET/PATCH/DELETE /v1/notes/{id}` · `GET /v1/notes/writing-guide` |
| 댓글 | `GET/POST /v1/notes/{id}/comments` · `PATCH/DELETE /v1/comments/{id}` |
| 이모지 | `GET/POST /v1/emojis` · `DELETE /v1/emojis/{name}` · `GET/POST/DELETE /v1/notes/{id}/reactions` |

모든 응답은 `{ success, code, message, data, errors, timestamp }` 형식이에요.

## 구조

```
src/
├── shared/core/   # 설정·로깅·DB·공통 응답·예외 핸들러·미들웨어
├── wiring/        # 의존성 주입 연결 (dependency_overrides)
└── user | auth | space | note | emoji/
    ├── domain/          # 엔티티·규칙·리포지토리 인터페이스
    ├── application/     # 서비스 + Command/Query DTO
    ├── infrastructure/  # SQLAlchemy 모델·저장소·보안
    └── presentation/    # 라우터·응답 스키마
```

## 구현 포인트

- **광장 동시성**: `pg_advisory_xact_lock`으로 같은 공간의 작성을 순서대로 처리해서, 하루 1개·최대 50개 제한이 동시 요청에도 깨지지 않게 했어요.
- **비회원 식별**: IP 원문은 저장하지 않고 HMAC 해시만 저장해요.
- **캐싱**: 이모지 목록(5분)과 반응 집계(30초)를 메모리 TTL 캐시에 담고, 바뀌면 바로 비워요.
- **미들웨어**: 요청 ID와 처리 시간을 로그·헤더로 남기고, CORS와 GZip을 적용했어요.
- **튜터 코드에서 고친 버그**:
  - 인증 없이 남의 비밀번호를 바꿀 수 있던 문제
  - 탈퇴 회원도 로그인되던 문제
  - `created_at`이 서버 시작 시각으로 고정되던 문제
  - 검증 오류가 409로 나가던 문제
