# 03 — Initial User Stories

These stories are a starting backlog. Add, split, reprioritize, or remove stories as the design becomes clearer.

## Student discovery
**US-01:** As a student, I want to search for hostels and apartments near my university so that I can reduce travel time.

Acceptance criteria:
- Search can use an agreed university/location input.
- Results show relevant property summaries.
- Empty results and failed searches have clear UI states.

**US-02:** As a student, I want to filter by budget, room type, and facilities so that I can find an option that suits my needs.

Acceptance criteria:
- Supported filters are documented.
- Filters can be combined.
- Displayed prices include a clear billing period when known.

**US-03:** As a student, I want to understand whether a listing has been verified so that I can make a better-informed decision.

Acceptance criteria:
- Verification state is supplied by the backend.
- The UI explains what the badge means.
- A badge does not claim a guarantee of personal safety.

## Booking
**US-04:** As a student, I want to start a booking so that I can reserve or request accommodation.

Acceptance criteria:
- The flow explains the booking state and next step.
- The server checks availability and price.
- The student can view the resulting status.
- Cancellation behavior is explained before confirmation.

## Property owner
**US-05:** As an owner, I want to submit property details so that UniNest can review the listing.

Acceptance criteria:
- Required fields and evidence are documented.
- Submission status is visible to the owner.
- Unapproved listings are not represented as verified.

## Administration
**US-06:** As an authorized reviewer, I want to approve or reject a listing so that public listings follow the agreed verification process.

Acceptance criteria:
- Only authorized reviewers can make decisions.
- The decision and timestamp are recorded.
- Rejection feedback follows an agreed policy.

## Commission
**US-07:** As a platform operator, I want a booking's commission to be calculated consistently so that revenue can be reconciled.

Acceptance criteria:
- The 20% rate is configurable or centrally defined.
- The commission base and earning trigger are approved first.
- Cancellation/refund effects are defined.
- Financial records can be traced to the relevant booking.

## Backlog fields
ID | Story | Priority | Status | Acceptance criteria | Dependencies | Test reference
