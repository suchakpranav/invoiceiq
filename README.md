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
