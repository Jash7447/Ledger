# Ledger

Ledger is a Canada-first personal finance application. Phases 1–7 establish the web/API/database foundation, secure ownership boundaries, account and transaction tracking, searchable history, the primary dashboard, and monthly budgets.

## Local development

1. Copy `.env.example` to `.env` and adjust values if needed. Ledger's Docker PostgreSQL is exposed on port `5433` by default to avoid conflicts with an existing local PostgreSQL installation.
2. Start PostgreSQL with `docker compose up postgres` (Docker is optional if you already have PostgreSQL).
3. Start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

4. Start the frontend in a second terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open http://localhost:3000. After signing in, use **Accounts** to create financial accounts and **Transactions** to record income, expenses, and transfers.

Create an account at http://localhost:3000/sign-up. The application stores an Argon2 password hash, sets an HTTP-only signed session cookie, and validates the session through FastAPI before rendering protected routes.

New users receive the product's default expense, income, and funding classifications. Account balances and budget progress are derived from transaction history. The Transactions page supports server-side search, filters, sorting, date ranges, and pagination. The dashboard summarizes monthly finances, spending, recent activity, and budget progress.

## Authentication configuration

Local development uses the values in the root `.env`. Before deploying, set:

```text
ENVIRONMENT=production
AUTH_SECRET_KEY=<a strong random secret>
AUTH_COOKIE_SECURE=true
```

Never expose `AUTH_SECRET_KEY` to the frontend or commit a real secret. When using Supabase PostgreSQL, replace only `DATABASE_URL`; authentication and authorization continue to run through FastAPI.

## Validation

Backend: `pytest`, `ruff check app tests`, and `mypy app`.

Frontend: `npm run lint`, `npm run typecheck`, and `npm run build`.
