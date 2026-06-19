# Vercel 배포 절차

## 1. Neon Postgres 생성

1. Neon에서 새 프로젝트를 만든다.
2. 연결 문자열을 복사한다.
3. Vercel 환경변수 `DATABASE_URL`에 연결 문자열을 넣는다.

Neon 연결 문자열은 보통 다음 형태다.

```text
postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

앱은 이 값을 자동으로 `postgresql+psycopg://...` 형태로 변환해서 SQLAlchemy에 연결한다.

## 2. 인증 환경변수 설정

Vercel 환경변수에 다음 값을 설정한다.

```text
APP_BASIC_AUTH_USER=원하는아이디
APP_BASIC_AUTH_PASSWORD=강한비밀번호
```

이 두 값이 있으면 모바일/브라우저 접속 시 Basic Auth 로그인 창이 뜬다. 설정하지 않으면 공개 상태가 되므로 배포 환경에서는 반드시 설정한다.

## 3. 기존 거래 데이터 이관

로컬에서 Neon `DATABASE_URL`을 지정한 뒤 CSV를 import한다.

```bash
DATABASE_URL="postgresql://USER:PASSWORD@HOST/DB?sslmode=require" \
  backend/.venv/bin/python -m backend.scripts.import_transactions \
  --csv ssohee-eco/transactions_export.csv \
  --replace
```

`ssohee-eco/transactions_export.csv`는 개인 금융 데이터라 GitHub에 올리지 않는다.

## 4. Vercel 프로젝트 연결

Vercel에서 GitHub 저장소 `yuljin/ssohee-eco`를 import한다.

권장 설정:

```text
Framework Preset: Other
Build Command: npm run build
Output Directory: public
Install Command: 기본값
```

이 저장소에는 `vercel.json`이 포함되어 있어 `/api/index.py` FastAPI 함수로 모든 요청을 전달한다.

## 5. 배포 후 확인

```text
https://YOUR-PROJECT.vercel.app/health
https://YOUR-PROJECT.vercel.app/
```

모바일에서는 Vercel URL을 열고 Basic Auth 계정으로 로그인하면 된다.
