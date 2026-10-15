# UniNest API (local development)

## Requirements
- Python 3.11 or newer
- Docker Desktop running
- MongoDB replica set and Mailpit from the project root's `docker-compose.yml`

## Setup in Windows CMD
```cmd
cd C:\uninest\backend
py -3.13 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```
If you already have `backend\.env`, do not overwrite it; update its values instead.

Run from `C:\uninest\backend`:
```cmd
uvicorn app.main:app --reload
```

Open:
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Mailpit: http://localhost:8025

## Important
- Registration accepts `student` and `owner`. Admin role must be provisioned manually; public registration cannot create admins.
- Listings are hidden from normal search until an admin verifies them.
- Booking commission is snapshotted at 20% of one month's rent; no real payment is processed.
- OTP, production email, real payments, map/geospatial search, and full moderation workflows are not implemented yet.
- Before deployment, use a strong random `JWT_SECRET`, restrict CORS, add rate limits and email verification, and configure real payment/email providers.
