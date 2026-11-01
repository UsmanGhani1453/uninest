# 09 — Initial Testing Plan

## Test layers
- Unit tests for business rules and validation
- API integration tests
- Frontend production build and lint checks
- Manual browser walkthroughs for critical user flows
- Authorization and file-access tests
- Responsive and accessibility checks
- Concurrency tests for booking inventory
- Payment/webhook tests only if payment integration is implemented

## Current MVP validation
The backend integration suite in `backend/app/tests/test_main.py` currently exercises:
- Health response, student registration/login, and rejection of public admin registration
- Owner listing creation with multiple rooms and seats, default public visibility, verification authorization, content-edit resubmission, and combined area/university/type/rent filters
- Admin listing rejection and the resulting owner resubmission behavior
- Booking eligibility, per-seat rent/deposit/commission snapshots, auto-assignment across rooms, overlapping stay conflicts, no-seat messaging, student/owner access, status transitions, and invalid past move-in dates
- Each test receives a uniquely named temporary MongoDB database, which is dropped after the test; the configured local demo database is not cleared.

Frontend checks:
- `npm run build` type-checks the React/TypeScript app and creates the Vite production bundle.
- `npm run lint` runs Oxlint.
- Follow the manual demo walkthrough in [12-test-and-demo.md](./12-test-and-demo.md) for browser flows. The frontend has no dedicated component-test runner yet.

## Candidate critical tests

### Search
- Search by a supported university or location.
- Combine filters.
- Handle no results and invalid filter values.
- Confirm only eligible public listings are returned.

### Verification
- Pending listings are not falsely shown as verified.
- Unauthorized users cannot approve a listing.
- Rejected/suspended listings follow the publication policy.
- Private evidence files cannot be accessed by unrelated users.

### Booking
- A valid request follows the agreed workflow.
- A booking is rejected if no seat is available for its requested dates.
- Concurrent approvals cannot allocate the same seat to overlapping stays.
- Students can cancel pending requests and approved bookings before move-in; cancellation releases the seat.
- Students cannot cancel approved bookings on or after move-in, but owners and admins can.
- Cancellation records its timestamp and actor, and does not process a payment or refund.
- Students cannot access other users' private booking details.
- Cancellation follows the agreed policy.

### Commission and payments
- Commission tests must match the approved commission base and earning trigger.
- Test rounding and refunds.
- If online payments exist, duplicate webhook events must not duplicate transactions or commissions.

## Test case template
- Test ID:
- Requirement/story ID:
- Preconditions:
- Steps:
- Expected result:
- Actual result:
- Pass/fail:
- Evidence / issue link:

## Release gate
Do not launch with unresolved critical security defects, broken booking workflows, or unverified assumptions about payment/commission handling.
