# RhFlow

RhFlow is a small two-part app made up of a FastAPI backend and a Next.js frontend.

## Project Layout

- `backend/` - FastAPI service
- `frontend/` - Next.js app

## Backend

The backend lives in `backend/main.py` and exposes:

- `GET /` - health-style message
- `GET /api/hello` - message used by the frontend

The API is configured with CORS so the frontend can call it from `http://localhost:3000`.

Run the backend from the `backend/` folder with your Python environment activated:

```bash
uvicorn main:app --reload --port 8000
```

## Frontend

The frontend is a Next.js app in `frontend/`.

Run it from the `frontend/` folder:

```bash
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Notes

- The frontend fetches data from `http://localhost:8000/api/hello`.
- Generated folders like `frontend/.next/` and `frontend/node_modules/` are ignored by Git.
