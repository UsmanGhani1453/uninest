# 08 — Business Rules and Open Decisions

This document prevents unresolved assumptions from becoming hidden in code.

## MVP decisions and remaining open questions

### 1. Commission
Presentation: 20% commission on each booking.
**MVP rule:** Store a commission estimate equal to the configured rate multiplied by one month's per-seat rent when the request is created. This is a snapshot only; the MVP does not collect or settle commission.
Still to decide after the MVP:
- Who pays the commission: student, owner, or a defined split?
- When is commission earned: booking request, owner acceptance, payment, move-in, or completed stay?
- How do cancellation, partial refund, and disputes affect commission?
- How are amounts rounded and reconciled?

### 2. Booking confirmation and seat inventory
**MVP rule:** A student submits a booking request; the listing owner may approve or reject a pending request. Cancellation follows the role and timing policy below.
- Approval records the owner's decision; it does not collect payment or guarantee a tenancy.
- Owners configure rooms and the number of bookable seats in each room. Rent and deposit are monthly per seat across the listing.
- Pending requests do not reserve seats. At approval, UniNest assigns the first available seat in the listing's rooms.
- Approved bookings occupy their assigned seat for their requested stay dates. Overlapping dates cannot use the same seat; a seat becomes available again after the approved stay ends.
- If there are no seats for the requested dates, UniNest rejects the request or approval with a clear unavailable message; the student should choose another property.
- Seat assignment is serialized so simultaneous owner approvals cannot assign the same seat.
- Students can cancel pending requests at any time and approved bookings only before the move-in date. On or after move-in, only the property owner or an admin can cancel an approved booking.
- Cancelling an approved booking releases its assigned seat for the requested dates. Cancellation is recorded with its timestamp and cancelling user's ID.
- Cancellation does not trigger a payment, refund, or commission settlement; the MVP does not process payments.
- Booking requests, approvals, rejections, and cancellations create persistent in-app notifications for the relevant student, owner, and administrators. Users can see their latest 50 notifications, unread counts, and mark notifications read.
- In-app notifications are polled while signed in; they are not real-time push or email notifications.
- No pending-request expiry is implemented in the MVP.

### 3. Payment and settlement
- Will UniNest collect money, facilitate payment, or track direct payments to owners?
- Which provider supports the intended business and settlement model in Pakistan?
- Who handles refunds and chargebacks?
- Are deposits or recurring rent payments in scope?

### 4. Verification
- Which documents or evidence are required from owners?
- Is verification documentary, physical, or both?
- Who reviews submissions?
- When does verification expire or need rechecking?
- What can the public verification badge truthfully claim?
- **MVP behavior:** Only verified, available listings are public. Admins can reject a submission with a reason; owner changes to listing content return it to pending review.

### 5. Property and pricing
- **MVP rule:** Monthly per-seat rent, with room-level seat counts and automatic seat assignment on owner approval.
- Remaining: Should rooms have different per-seat prices? The MVP uses one per-seat price for the whole listing.
- Are utilities, mess, laundry, deposits, and other charges included?
- How is distance from a university calculated?
- Who can change price and availability after a booking request?

### 6. Reviews, reports, and support
- Are reviews in the MVP?
- Who can submit reviews?
- How are fake reviews and complaints handled?
- What support channel and response expectations will be offered?

### 7. Future revenue
- Listing fees: planned, rules and timing undecided.
- Featured listings/promotions: future possibility.
- Do not build these into the MVP without an explicit decision.

## Decision log template
- Decision ID:
- Question:
- Options:
- Decision:
- Rationale:
- Date:
- Affected documents/code:
- Status: open / decided / revisited
