# CRUD API with JWT Auth

A REST API built with FastAPI. Users register, log in, and manage their own orders.

## Features
- CRUD for orders (GET, POST, PUT, DELETE)
- Password hashing with bcrypt
- JWT authentication (30 min expiry)
- Ownership checks: users can only access their own orders (403 otherwise)
- Pagination on listing, rate limiting on login

## Run locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn CRUDAPI:app --reload
```
Open http://127.0.0.1:8000/docs

## Environment
Set `SECRET_KEY` as an environment variable in production.

## Endpoints
| Method | Path | Auth |
|---|---|---|
| POST | /register | no |
| POST | /login | no |
| GET | /orders | yes |
| POST | /orders | yes |
| GET/PUT/DELETE | /orders/{id} | yes (owner only) |

## Note
Data is stored in memory, so it resets when the server restarts.