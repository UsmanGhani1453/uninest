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

1. **Owner:** Register through the site as a property owner. Add a Lahore listing with a title, description, address, area, monthly rent per seat, and one or more rooms with their seat counts. Add optional amenities or image URLs. It should appear in the owner dashboard as under review, but not in public search.
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

## Known demo limitations

- Use the API and UI on the local development ports; no production deployment or real email/payment provider is configured.
- Listing photos are provided as image URLs; production-grade private media upload is not part of this walkthrough.
- Search is intended for a modest demo dataset, not production-scale inventory.
- The MongoDB volume persists between runs. Do not remove the volume if you need to keep local demo records.
- Any test records created in the default `uninest` database by older test runs may remain there; the isolated test fixture does not identify or remove pre-existing data.
- Seat availability prevents overlapping approved bookings from using the same seat. The MVP does not support cancelling an approved booking early; contact the property owner to resolve changes.
- Old listings created before room inventory was added may need to be edited by their owner to add room names and seat counts, then reviewed again before they appear in public search.
