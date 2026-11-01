# 07 — Initial Data Model

This is a conceptual starting point, not a finalized schema. Final entities depend on booking, verification, and pricing decisions.

## Candidate entities

### users
- id
- name
- email
- password_hash or external identity reference
- account_status
- created_at

### properties
- id
- owner_id
- title
- description
- property_type (hostel/apartment)
- address/area
- location coordinates, if location search is implemented
- publication_status
- verification_status
- created_at / updated_at

### rooms and seats (MVP implementation)
- Each listing contains one or more named rooms.
- Each room records its number of bookable seats.
- Monthly rent and deposit are defined per seat for the listing.
- An approved booking records the allocated room and seat number.
- A seat cannot be allocated to overlapping approved stays.

### rooms_or_units
- id
- property_id
- room_type
- capacity
- rent_amount
- rent_period
- facilities
- availability details

### universities
- id
- name
- address/location

### property_verification_submissions
- id
- property_id
- submitted_by
- status
- reviewer_id
- decision_reason
- submitted_at / reviewed_at

### private_verification_files
- id
- submission_id or property_id
- document_type
- private_storage_key
- access/review metadata

### bookings
- id
- student_id
- room_or_unit_id
- requested stay details
- quoted_amount
- status
- cancelled_at / cancelled_by, when cancelled
- created_at / updated_at

### commission_records (if commission is managed in-app)
- id
- booking_id
- rate
- commission_base
- commission_amount
- status

### payment_transactions (only if payments are integrated)
- id
- booking_id
- provider_reference
- amount
- status
- transaction_type

## Important design notes
- Define rent periods explicitly; do not assume all prices are monthly.
- Decide whether bookings reserve a whole room, a bed, or an apartment.
- Store monetary amounts using an exact decimal or integer minor-unit representation.
- Use foreign keys and constraints.
- Keep financial history auditable; do not erase a transaction simply because a booking is cancelled.
- Prevent conflicting reservations using transactions and appropriate constraints/locking.
- Store sensitive verification files privately and authorize access.

## ERD
Create an entity-relationship diagram after the business rules are confirmed. Mark primary keys, foreign keys, cardinalities, and unique constraints.
