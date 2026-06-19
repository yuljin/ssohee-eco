# ssohee-eco

개인 포트폴리오 리밸런싱 시스템입니다. 원본 스펙/데이터 묶음은 `ssohee-eco/`에 보존되어 있고, 새 구현은 `backend/`와 `frontend/`에 있습니다.

## 개발 실행

```bash
./start.sh
```

개별 실행:

```bash
cd backend
uv venv
uv pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

## 데이터

초기 DB는 `data/portfolio.db`를 사용합니다. 기존 거래 33건은 `ssohee-eco/portfolio.db`에서 복사해 검증합니다.

