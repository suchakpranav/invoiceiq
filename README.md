# InvoiceIQ — v0.3.0 (PostgreSQL)

Local-first invoice management with FastAPI, PostgreSQL, SQLAlchemy and Alembic.
Authentication, document upload, OCR and full GST validation are not implemented.
Use synthetic data only and bind the API to localhost.

## Windows setup

Install PostgreSQL 17 (or 18) and pgAdmin from https://www.postgresql.org/download/windows/.
Keep port 5432 and remember the administrator password. In pgAdmin, connect as
`postgres`, open Query Tool on the `postgres` database and run each statement separately.
Replace both password placeholders with distinct strong URL-safe passwords.

```sql
CREATE ROLE invoiceiq_app LOGIN PASSWORD 'REPLACE_APP_PASSWORD';
CREATE ROLE invoiceiq_test LOGIN PASSWORD 'REPLACE_TEST_PASSWORD';
CREATE DATABASE invoiceiq OWNER invoiceiq_app;
CREATE DATABASE invoiceiq_test OWNER invoiceiq_test;
```

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
copy .env.example .env
```

For an existing installation, preserve `.env` instead of copying over it. Set
`INVOICEIQ_APP_VERSION=0.3.0` and replace `INVOICEIQ_DATABASE_URL` with
`postgresql+psycopg://invoiceiq_app:YOUR_APP_PASSWORD@127.0.0.1:5432/invoiceiq`.
Percent-encode reserved URL characters in passwords. Never commit credentials.

```cmd
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. The homepage remains a service-status preview.
The health endpoint indicates API liveness, not database readiness.

## Tests

In a second CMD with the virtual environment active:

```cmd
set "INVOICEIQ_TEST_DATABASE_URL=postgresql+psycopg://invoiceiq_test:YOUR_TEST_PASSWORD@127.0.0.1:5432/invoiceiq_test"
python -m pytest -v
python -m ruff check .
```

Tests require a dedicated database named `invoiceiq_test`; each fixture creates
and migrates a random schema and drops only that schema afterward. The CI workflow
starts an ephemeral PostgreSQL 17 service. Its password is for CI only.

## Design

Money is stored as integer paise (`subtotal_cents`) and tax rates as basis points.
The API uses Decimal for calculations. SQLAlchemy sessions are scoped to repository
operations, and the engine checks pooled connections before use. Search uses
case-insensitive literal substring matching. Count and page queries are separate,
so concurrent changes may affect pagination. The initial migration creates the
invoice table and indexes. Back up before migrations; downgrading deletes data.

This edition does not import old SQLite records. Preserve any existing SQLite file
if it contains data you need. PostgreSQL integration requires a running server.
