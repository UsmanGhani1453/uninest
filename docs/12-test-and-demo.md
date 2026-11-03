# 12 — MVP Test and Demo Runbook

This runbook is for a local MVP walkthrough, not production deployment.

## Start the project

Use `localhost` for the browser URL because the default backend CORS allowlist includes `http://localhost:5173`.

1. From the repository root, start MongoDB and Mailpit:

   ```powershell
   cd C:\uninest
   docker compose up -d
   ```

2. In a terminal, start the backend:

   ```powershell
   cd C:\uninest\backend
   venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

3. In another terminal, start the frontend:

   ```powershell
   cd C:\uninest\frontend
   npm run dev
   ```

4. Open http://localhost:5173. The API docs are at http://127.0.0.1:8000/docs.

## Provision a local admin account

Public registration intentionally cannot create administrators. With the backend virtual environment active and MongoDB running, run:

```powershell
cd C:\uninest\backend
python -m scripts.create_admin
```

The command prompts for the admin name, email, and password (twice). It refuses to create an account if that email already exists; it does not promote or overwrite an existing account.

## Walk through the MVP

1. **Owner:** Register through the site as a property owner. Add a Lahore listing with a title, description, address, area, monthly rent per seat, and one or more rooms with their seat counts. Add optional amenities or upload photos from your computer. It should appear in the owner dashboard as under review, but not in public search.
2. **Admin:** Sign out, sign in with the provisioned admin account, and open **Review listings**. Verify the owner submission.
3. **Student:** Sign out, register as a student, find the verified listing, open its details, and submit a request with a future move-in date.
4. **Owner:** Sign back in as the owner. The booking request should appear in the dashboard. Approve or reject it. Approval assigns the first available seat across the rooms.
5. **Student:** Sign back in as the student and confirm the request status and assigned room/seat.
6. **Rejection path (optional):** Submit a second listing, reject it from the admin dashboard with a reason, then edit it as the owner. The edit should send it back to review.

Booking approval assigns the first available seat for the requested dates. Pending requests do not reserve seats, and approval does not collect money online or guarantee a tenancy.

## Automated checks

From the repository root:

```powershell
cd C:\uninest\backend
python -m pytest -q

cd C:\uninest\frontend
npm run build
npm run lint
```

Tests use the configured MongoDB replica set and a unique temporary database per test. Each temporary test database is dropped after its test; the configured local demo database is not cleared or modified.

## Temporary invite-only browser test

For a browser-only test link, use the local staging gateway and an ngrok HTTPS tunnel. This is temporary hosting, not a production deployment. Use only fake test data; anyone with the link and invitation password can reach the staging login.

1. Keep MongoDB running, then start a separate backend in `C:\uninest\backend` with these environment settings:

   ```powershell
   $env:ENVIRONMENT = "staging"
   $env:MONGODB_URL = "mongodb://localhost:27017/uninest_staging_20261102?replicaSet=rs0"
   $env:DATABASE_NAME = "uninest_staging_20261102"
   $env:UPLOAD_DIR = "C:\Temp\uninest-staging-uploads"
   $env:JWT_SECRET = node -e "process.stdout.write(require('node:crypto').randomBytes(48).toString('base64url'))"
   New-Item -ItemType Directory -Force $env:UPLOAD_DIR | Out-Null
   .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```

   Create a staging admin in another backend terminal using the same `MONGODB_URL` and `DATABASE_NAME`, then run `.\venv\Scripts\python.exe -m scripts.create_admin`.

2. Build the frontend for the same-origin API gateway:

   ```powershell
   cd C:\uninest\frontend
   $env:VITE_API_BASE_URL = "/api/v1"
   npm run build
   ```

3. In `C:\uninest\frontend`, create the gateway credentials and start it:

   ```powershell
   $env:STAGING_GATEWAY_PASSWORD = node -e "process.stdout.write(require('node:crypto').randomBytes(32).toString('base64url'))"
   Write-Output "Share this invitation password: $env:STAGING_GATEWAY_PASSWORD"
   $env:STAGING_GATEWAY_SESSION_TOKEN = node -e "process.stdout.write(require('node:crypto').randomBytes(48).toString('base64url'))"
   $env:STAGING_FRONTEND_DIST = (Resolve-Path .\dist).Path
   node .\staging-gateway.mjs
   ```

   Keep this terminal open; the gateway requires an invitation password of at least 24 characters.
4. In another terminal, run `ngrok http 5176`. Share its HTTPS URL and the invitation password only with testers.
5. Stop the gateway, tunnel, and staging backend when the test ends. The staging database is separate from `uninest`; do not drop or modify the normal database during cleanup.

## Known demo limitations

- The project has no permanent production deployment or real email/payment provider configured.
- A temporary invite-only test link requires the local staging setup above and is available only while the host computer and services are running.
- Uploaded listing photos are stored in the backend's local uploads directory; external object storage is not configured.
- Search is intended for a modest demo dataset, not production-scale inventory.
- The MongoDB volume persists between runs. Do not remove the volume if you need to keep local demo records.
- Any test records created in the default `uninest` database by older test runs may remain there; the isolated test fixture does not identify or remove pre-existing data.
- Seat availability prevents overlapping approved bookings from using the same seat. The MVP does not support cancelling an approved booking early; contact the property owner to resolve changes.
- Old listings created before room inventory was added may need to be edited by their owner to add room names and seat counts, then reviewed again before they appear in public search.
