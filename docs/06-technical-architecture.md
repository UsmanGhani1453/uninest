# 06 — Technical Architecture

**Chosen stack for MVP:** React frontend + FastAPI backend + MongoDB via Beanie ODM.

## Chosen high-level structure
Browser → React UI → FastAPI REST API → business logic/services → MongoDB database.

The MongoDB + Beanie choice is the current implementation baseline for this repository and is suitable for the MVP because it supports rapid iteration on document-based entities such as users, listings, bookings, and reviews without introducing a migration-heavy relational schema before the product flow is proven.

Additional services may include private file storage, email notifications, maps/geocoding, and a payment provider. These are dependencies to assess, not automatic MVP requirements.

## Frontend responsibilities
- Page layouts and navigation
- Search/filter controls
- Forms and client-side validation
- API calls and loading/error states
- Student/owner/admin experiences as approved

## Backend responsibilities
- Authentication and authorization
- Listing and verification rules
- Search/filter query handling
- Booking state transitions and availability validation
- Commission calculation after business rules are defined
- Input validation, audit events, and consistent errors

## Database
PostgreSQL is a reasonable candidate because listings, users, bookings, and financial records are relational and require transactional consistency.

## Architectural safeguards
- Enforce permissions on the backend, not only in React.
- Do not trust prices, roles, commission amounts, or availability supplied by the browser.
- Keep secrets outside source control.
- Store private verification documents in restricted storage.
- Use database migrations for schema changes.
- Protect booking creation from conflicting concurrent requests.
- If payments are added, verify provider webhooks and handle retries idempotently.

## Development environments
- Local development
- Optional staging environment
- Production environment

## Architecture Decision Record (ADR) template
- Decision ID and date
- Context/problem
- Options considered
- Chosen option
- Reasoning and trade-offs
- Consequences
- Status: proposed / accepted / superseded
