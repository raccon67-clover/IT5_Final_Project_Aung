# Campus Lost and Found Management System

A FastAPI and SQLite API for a campus to record lost and found belongings, manage claims, and track item status changes. This project adapts the provided `fastapi-it5` starter: `main.py` defines routes, `app/database.py` manages SQLite, and `app/models.py` contains Pydantic models and the model helper methods used by routes.

## Features

- CRUD operations for people and item reports.
- Search and filter item reports.
- Submit claims for found-item reports.
- Approve or reject pending claims.
- Automatically update item status as claims are submitted and reviewed.
- Keep item status history.
- Validate incoming data and return useful HTTP errors.
- Test the API through Swagger UI.

## Run on Windows

Run these commands from this project folder in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/docs> to try the API. The `lost_found.db` database is created automatically.

## Project structure

- `main.py`: FastAPI application and API routes, following the starter's route pattern.
- `app/database.py`: SQLite connection context manager and table creation.
- `app/models.py`: Pydantic request/response classes and helper methods called by the routes, following the starter's model pattern.
- `app/services.py`: SQL operations and transaction rules for the lost-and-found workflow.
- `ai-context.md`: original project guidance file retained from the supplied starter.

## Database tables

- `people`: students and staff who report items or submit/review claims.
- `item_reports`: lost and found reports.
- `claims`: claims submitted for found items.
- `item_status_history`: history of item status changes.

The tables are related through primary keys and foreign keys.

## Main workflow

1. Create a person through `POST /people`.
2. Create a found-item report through `POST /items` with `report_type` set to `found`.
3. Create another person and submit a claim through `POST /claims`.
4. Review the claim through `PATCH /claims/{claim_id}/review` with `decision` set to `approved` or `rejected`.
5. Check the item's current status through `GET /items/{item_id}` and status history through `GET /items/{item_id}/history`.

## Main endpoints

### People

- `GET /people` and `GET /people/{person_id}`
- `POST /people`
- `PUT /people/{person_id}`
- `DELETE /people/{person_id}`

### Item reports

- `GET /items` and `GET /items/{item_id}`
- `POST /items`
- `PUT /items/{item_id}`
- `DELETE /items/{item_id}`
- `GET /items/{item_id}/history`
- `PATCH /items/{item_id}/close`

The list endpoint supports optional filters for report type, status, category, location, reporter, and a text search.

### Claims

- `GET /claims` and `GET /claims/{claim_id}`
- `POST /claims`
- `PATCH /claims/{claim_id}/review`
- `DELETE /claims/{claim_id}`

## Status rules

- New item reports start as `open`.
- A claim on an open found item changes the item to `under_review`.
- Approving a claim changes the claim to `approved` and the item to `claimed`; other pending claims for that item are rejected.
- Rejecting the last pending claim returns the item to `open`.
- Claimed or closed items cannot be claimed again.
- Only pending claims can be reviewed or deleted.

## Scope note

This academic API records person IDs supplied in requests but does not implement login or authentication. The reviewer and status-change IDs are workflow fields, not verified identities.
