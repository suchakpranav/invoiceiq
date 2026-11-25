# InvoiceIQ

A local-first invoice processing workspace for Indian small businesses. Version 0.1.0 is the application foundation, not an invoice extraction engine.

## Windows setup (Command Prompt)

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the workspace and http://127.0.0.1:8000/docs for API documentation.

## Checks

```sh
python -m pytest -q
python -m ruff check .
```

## Design

FastAPI serves a small static frontend and a versioned JSON health endpoint. Configuration comes from environment variables via Pydantic Settings. The application factory allows isolated test configuration. No database, OCR, authentication or invoice upload is implemented yet. Run on localhost only.

## Next milestone

Expand the API with invoice schemas, validation and persistent storage. Do not upload real customer documents or secrets to GitHub.

## Phase 2 — Invoice API (0.2.0)

Update `INVOICEIQ_APP_VERSION` in your local `.env` to `0.2.0`. Run the server
with `python -m uvicorn app.main:app --reload` and open `/docs` to try the API.

- POST `/api/v1/invoices`: create an invoice.
- GET `/api/v1/invoices`: list, search (`q`), filter (`supplier`, `date_from`,
  `date_to`) and paginate (`offset`, `limit`).
- GET, PUT, DELETE `/api/v1/invoices/{invoice_id}`: retrieve, replace or delete.

Example request:

```json
{"invoice_number":"INV-001","supplier":"Sample Traders","customer":"Demo Retail","invoice_date":"2026-11-25","subtotal":"1250.50","tax_rate":"18"}
```

Amounts use decimal arithmetic and tax is rounded half-up to two decimal places.
This is a simplified tax calculation, not a GST compliance engine. Records live
in memory, are lost on restart and are not shared between server processes.
No authentication, duplicate detection or invoice upload is implemented yet.
Use synthetic data only. The homepage remains the Phase 1 interface; use Swagger
for invoice management. Run `python -m pytest -v` and `python -m ruff check .`.
