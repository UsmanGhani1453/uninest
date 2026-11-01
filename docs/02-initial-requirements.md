# 02 — Initial Requirements

**Status:** Draft; validate before implementation.

## Requirement labels
- **P0 / Proposed MVP:** Core candidate for the first usable version.
- **P1 / Candidate:** Useful but can follow the core MVP.
- **Future:** Explicitly planned for later or not needed to prove the core idea.
- These priorities are proposals, not final commitments.

## Confirmed MVP scope for this project
The following items are the agreed MVP boundary for the first working release:

- **Student can browse verified listings** in Lahore by area and price range.
- **Owner can create and edit their own listings** for review.
- **Admin can verify or reject listings** before they become public.
- **Student can request a booking** for a verified listing.
- **Owner can approve or reject booking requests**.
- **Authentication and role-based access control** are required for all user-facing flows.
- **Commission is stored as a snapshot** on each booking, using the configured commission rate.

This scope intentionally excludes real payments, chat, maps, AI recommendations, and advanced analytics until after the core marketplace works in a demo environment.

## Student-facing requirements
- **REQ-ST-01 (P0):** A visitor can browse publicly available accommodation listings.
- **REQ-ST-02 (P0):** A student can view property details, including price, location, room type, and facilities when provided.
- **REQ-ST-03 (P0):** A student can filter or sort listings using agreed criteria such as budget, location, and facilities.
- **REQ-ST-04 (P0):** The interface can show the property's review/verification status accurately.
- **REQ-ST-05 (P0):** A student can initiate a booking or booking request according to the selected booking policy.
- **REQ-ST-06 (P1):** Students can compare or save accommodation options.
- **REQ-ST-07 (P1):** Students can leave reviews after an eligible stay, if a review policy is adopted.

## Owner-facing requirements
- **REQ-OW-01 (P0 candidate):** An owner can submit property information for review.
- **REQ-OW-02 (P0 candidate):** An owner can update listing information, subject to publication and review rules.
- **REQ-OW-03 (P0 candidate):** An owner can view and respond to booking requests if owner-managed confirmation is selected.
- **REQ-OW-04 (P1):** Owners can manage availability and view booking history.

## Admin/operations requirements
- **REQ-AD-01 (P0 candidate):** Authorized staff can review submitted listings and record an approval/rejection decision.
- **REQ-AD-02 (P0 candidate):** Only listings that satisfy the publication policy appear as verified/public listings.
- **REQ-AD-03 (P1):** Authorized staff can investigate user reports and suspend problematic listings.
- **REQ-AD-04 (P1):** Admin actions affecting verification or bookings are auditable.

## Business and revenue requirements
- **REQ-BIZ-01:** The intended revenue model includes a 20% booking commission.
- **REQ-BIZ-02:** Commission calculation must use an explicitly defined commission base and timing.
- **REQ-BIZ-03:** Listing fees are planned but should not be implemented until their rules are approved.
- **REQ-BIZ-04:** Featured listings/promotions are future possibilities, not MVP commitments.

## Non-functional requirements to define
- Mobile-friendly responsive design
- Authentication and role-based authorization
- Secure storage and access control for private documents
- Search performance targets
- Accessibility expectations
- Backup, recovery, logging, and deployment requirements

## Requirement completion rule
Each requirement should eventually have: unique ID, priority, rationale, acceptance criteria, status, and linked test(s).
