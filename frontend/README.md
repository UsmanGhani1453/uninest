# UniNest frontend

React + TypeScript + Vite frontend for the UniNest student accommodation MVP.

## Run locally

1. Start the backend and MongoDB as described in [../backend/README.md](../backend/README.md).
2. From this directory, install dependencies and start Vite:

   ```powershell
   npm install
   npm run dev
   ```

3. Open the local URL printed by Vite (normally http://localhost:5173).

The frontend uses `http://127.0.0.1:8000/api/v1` by default. To point it at a different API, set `VITE_API_BASE_URL` in a local `.env` file, for example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## MVP flows

- Visitors can search and view available verified listings.
- Students can create an account, request a booking, review their requests, and cancel pending requests.
- Owners can define rooms and bookable seats, set monthly rent per seat, manage listings, and approve or reject booking requests.
- Admins can review pending listings and verify or reject them.
- On approval, UniNest assigns the first available seat for the requested dates. Pending requests do not hold seats.
- Successful sign-in shows a role-specific welcome popup for students, owners, and admins.

Admin accounts must be provisioned by the backend operator; public registration only supports student and owner accounts. Booking approval is not an online payment or a tenancy guarantee.
