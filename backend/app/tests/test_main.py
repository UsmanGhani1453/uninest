from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.main import app
from app.models.user import User


def test_health():
    # The application lifespan requires a running MongoDB replica set.
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_register_and_login_student():
    with TestClient(app) as client:
        unique_email = f"student.{uuid4()}@example.com"
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Student Auth Test",
                "email": unique_email,
                "password": "SecurePass123!",
                "role": "student",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["user"]["email"] == unique_email.lower()
        assert data["user"]["role"] == "student"
        assert "access_token" in data

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200, login_response.text
        assert login_response.json()["user"]["email"] == unique_email.lower()


def test_register_rejects_admin_role():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Invalid Admin",
                "email": f"admin.{uuid4()}@example.com",
                "password": "SecurePass123!",
                "role": "admin",
            },
        )
        assert response.status_code == 422


def test_owner_can_create_unverified_listing_and_public_search_hides_it_until_verified():
    with TestClient(app) as client:
        owner_email = f"owner.{uuid4()}@example.com"
        register = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Owner Listing Test",
                "email": owner_email,
                "password": "SecurePass123!",
                "role": "owner",
            },
        )
        assert register.status_code == 201, register.text
        token = register.json()["access_token"]

        create_response = client.post(
            "/api/v1/listings",
            json={
                "title": "Room near GCU Lahore",
                "description": "A clean room for students near the university with wifi and study support.",
                "accommodation_type": "room",
                "rent_per_month": 16000,
                "security_deposit": 20000,
                "address": "123 Gulberg Road, Lahore",
                "area": "Gulberg",
                "city": "Lahore",
                "university_names": ["GCU", "University of Central Punjab"],
                "amenities": ["wifi", "laundry"],
                "image_urls": ["https://example.com/room.jpg"],
                "rooms": [{"name": "Room 1", "seat_count": 2}],
                "bathrooms": 1,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201, create_response.text
        listing_id = create_response.json()["id"]

        public_results = client.get("/api/v1/listings")
        assert public_results.status_code == 200
        assert all(item["id"] != listing_id for item in public_results.json())
        assert client.get(f"/api/v1/listings/{listing_id}").status_code == 404
        assert client.get(
            "/api/v1/admin/listings/pending",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code == 403

        forged_verification = client.patch(
            f"/api/v1/listings/{listing_id}",
            json={"is_verified": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert forged_verification.status_code == 422

        admin = User(
            id=PydanticObjectId(),
            full_name="Test Admin",
            email=f"admin.{uuid4()}@example.com",
            password_hash="unused",
            role="admin",
        )
        app.dependency_overrides[get_current_user] = lambda: admin
        try:
            pending = client.get("/api/v1/admin/listings/pending")
            assert pending.status_code == 200, pending.text
            pending_listing = next(item for item in pending.json() if item["id"] == listing_id)
            assert pending_listing["description"].startswith("A clean room for students")
            assert pending_listing["university_names"] == ["GCU", "University of Central Punjab"]
            assert pending_listing["amenities"] == ["wifi", "laundry"]

            verify_response = client.patch(f"/api/v1/admin/listings/{listing_id}/verify")
            assert verify_response.status_code == 200, verify_response.text
            assert verify_response.json()["is_verified"] is True
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        verified_results = client.get("/api/v1/listings")
        assert verified_results.status_code == 200
        ids = [item["id"] for item in verified_results.json()]
        assert listing_id in ids

        filtered_results = client.get(
            "/api/v1/listings",
            params={
                "area": "Gulberg",
                "university": "GCU",
                "accommodation_type": "room",
                "min_rent": 15000,
                "max_rent": 17000,
            },
        )
        assert filtered_results.status_code == 200
        assert any(item["id"] == listing_id for item in filtered_results.json())

        owner_results = client.get(
            "/api/v1/listings/mine",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert owner_results.status_code == 200
        assert any(item["id"] == listing_id for item in owner_results.json())

        edit = client.patch(
            f"/api/v1/listings/{listing_id}",
            json={"description": "Updated description pending a fresh admin review for this listing."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert edit.status_code == 200, edit.text
        assert edit.json()["is_verified"] is False
        assert all(
            item["id"] != listing_id
            for item in client.get("/api/v1/listings").json()
        )


def test_admin_rejection_hides_listing_and_owner_edit_resubmits_for_review():
    with TestClient(app) as client:
        owner_email = f"reject.owner.{uuid4()}@example.com"
        register = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Owner Rejection Test",
                "email": owner_email,
                "password": "SecurePass123!",
                "role": "owner",
            },
        )
        assert register.status_code == 201, register.text
        owner_token = register.json()["access_token"]
        create = client.post(
            "/api/v1/listings",
            json={
                "title": "Student Apartment near UOL",
                "description": "Apartment listing submitted for the admin rejection workflow test.",
                "accommodation_type": "apartment",
                "rent_per_month": 25000,
                "address": "45 Raiwind Road, Lahore",
                "area": "Johar Town",
                "rooms": [{"name": "Apartment", "seat_count": 1}],
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert create.status_code == 201, create.text
        listing_id = create.json()["id"]

        admin = User(
            id=PydanticObjectId(),
            full_name="Test Admin",
            email=f"reject.admin.{uuid4()}@example.com",
            password_hash="unused",
            role="admin",
        )
        app.dependency_overrides[get_current_user] = lambda: admin
        try:
            response = client.patch(
                f"/api/v1/admin/listings/{listing_id}/reject",
                json={"reason": "Please provide clearer property photos."},
            )
            assert response.status_code == 200, response.text
            assert response.json()["is_rejected"] is True
            assert response.json()["verification_note"] == "Please provide clearer property photos."
            pending = client.get("/api/v1/admin/listings/pending")
            assert all(item["id"] != listing_id for item in pending.json())
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert client.get(f"/api/v1/listings/{listing_id}").status_code == 404
        update = client.patch(
            f"/api/v1/listings/{listing_id}",
            json={"image_urls": ["https://example.com/updated.jpg"]},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert update.status_code == 200, update.text
        assert update.json()["is_rejected"] is False
        assert update.json()["is_verified"] is False
        assert update.json()["verification_note"] is None


def test_booking_request_snapshot_permissions_and_status_transitions():
    with TestClient(app) as client:
        owner_register = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Booking Flow Owner",
                "email": f"booking.owner.{uuid4()}@example.com",
                "password": "SecurePass123!",
                "role": "owner",
            },
        )
        student_register = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Booking Flow Student",
                "email": f"booking.student.{uuid4()}@example.com",
                "password": "SecurePass123!",
                "role": "student",
            },
        )
        assert owner_register.status_code == 201, owner_register.text
        assert student_register.status_code == 201, student_register.text
        owner_token = owner_register.json()["access_token"]
        student_token = student_register.json()["access_token"]

        listing_response = client.post(
            "/api/v1/listings",
            json={
                "title": "Booking Test Hostel Room",
                "description": "A clean room for students included for booking workflow testing.",
                "accommodation_type": "room",
                "rent_per_month": 25000,
                "security_deposit": 10000,
                "address": "16 Main Boulevard, Lahore",
                "area": "Gulberg",
                "rooms": [
                    {"name": "Room 1", "seat_count": 1},
                    {"name": "Room 2", "seat_count": 1},
                ],
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert listing_response.status_code == 201, listing_response.text
        listing_id = listing_response.json()["id"]
        assert listing_response.json()["capacity"] == 2
        assert [room["seat_count"] for room in listing_response.json()["rooms"]] == [1, 1]
        booking_payload = {
            "listing_id": listing_id,
            "move_in_date": (date.today() + timedelta(days=30)).isoformat(),
            "duration_months": 6,
            "student_message": "I would like to request this room.",
        }

        not_yet_verified = client.post(
            "/api/v1/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert not_yet_verified.status_code == 404

        admin = User(
            id=PydanticObjectId(),
            full_name="Booking Flow Admin",
            email=f"booking.admin.{uuid4()}@example.com",
            password_hash="unused",
            role="admin",
        )
        app.dependency_overrides[get_current_user] = lambda: admin
        try:
            verify = client.patch(f"/api/v1/admin/listings/{listing_id}/verify")
            assert verify.status_code == 200, verify.text
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        first_booking = client.post(
            "/api/v1/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert first_booking.status_code == 201, first_booking.text
        first_data = first_booking.json()
        assert first_data["status"] == "pending"
        assert first_data["monthly_rent_snapshot"] == 25000
        assert first_data["security_deposit_snapshot"] == 10000
        assert first_data["commission_rate_snapshot"] == settings.BOOKING_COMMISSION_RATE
        assert first_data["commission_amount_snapshot"] == round(
            25000 * settings.BOOKING_COMMISSION_RATE, 2
        )

        owner_notifications = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_notifications.status_code == 200, owner_notifications.text
        assert owner_notifications.json()["unread_count"] == 1
        request_notification = owner_notifications.json()["items"][0]
        assert request_notification["event_type"] == "booking_requested"
        assert request_notification["booking_id"] == first_data["id"]

        student_notifications = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_notifications.status_code == 200
        assert student_notifications.json() == {"items": [], "unread_count": 0}

        another_user_cannot_read_notification = client.patch(
            f"/api/v1/notifications/{request_notification['id']}/read",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert another_user_cannot_read_notification.status_code == 404

        mark_read = client.patch(
            f"/api/v1/notifications/{request_notification['id']}/read",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert mark_read.status_code == 200, mark_read.text
        assert mark_read.json()["is_read"] is True
        assert mark_read.json()["read_at"]

        owner_notification_state = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_notification_state.json()["unread_count"] == 0

        second_booking = client.post(
            "/api/v1/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert second_booking.status_code == 201, second_booking.text
        second_id = second_booking.json()["id"]
        third_booking = client.post(
            "/api/v1/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        fourth_booking = client.post(
            "/api/v1/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert third_booking.status_code == 201, third_booking.text
        assert fourth_booking.status_code == 201, fourth_booking.text

        student_bookings = client.get(
            "/api/v1/bookings/mine",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_bookings.status_code == 200
        assert len([x for x in student_bookings.json() if x["listing_id"] == listing_id]) >= 2

        owner_bookings = client.get(
            "/api/v1/bookings/owner",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_bookings.status_code == 200
        assert any(x["id"] == first_data["id"] for x in owner_bookings.json())

        student_cannot_approve = client.patch(
            f"/api/v1/bookings/{first_data['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_cannot_approve.status_code == 403

        approve = client.patch(
            f"/api/v1/bookings/{first_data['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert approve.status_code == 200, approve.text
        assert approve.json()["status"] == "approved"
        assert approve.json()["room_name"] == "Room 1"
        assert approve.json()["seat_number"] == 1

        approval_notifications = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert approval_notifications.status_code == 200
        assert approval_notifications.json()["unread_count"] == 1
        assert approval_notifications.json()["items"][0]["event_type"] == "booking_approved"
        assert approval_notifications.json()["items"][0]["booking_id"] == first_data["id"]

        cannot_reapprove = client.patch(
            f"/api/v1/bookings/{first_data['id']}/status",
            json={"status": "rejected"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert cannot_reapprove.status_code == 409

        student_cancel = client.patch(
            f"/api/v1/bookings/{second_id}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_cancel.status_code == 200, student_cancel.text
        assert student_cancel.json()["status"] == "cancelled"

        cancellation_notifications = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert cancellation_notifications.status_code == 200
        assert cancellation_notifications.json()["items"][0]["event_type"] == "booking_cancelled"
        assert cancellation_notifications.json()["items"][0]["booking_id"] == second_id
        assert cancellation_notifications.json()["unread_count"] >= 1

        mark_all_read = client.patch(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert mark_all_read.status_code == 200, mark_all_read.text
        assert mark_all_read.json()["updated_count"] == cancellation_notifications.json()["unread_count"]
        read_all_state = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert read_all_state.json()["unread_count"] == 0

        second_approve = client.patch(
            f"/api/v1/bookings/{third_booking.json()['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert second_approve.status_code == 200, second_approve.text
        assert second_approve.json()["room_name"] == "Room 2"
        assert second_approve.json()["seat_number"] == 1

        cannot_remove_occupied_room = client.patch(
            f"/api/v1/listings/{listing_id}",
            json={"rooms": [listing_response.json()["rooms"][1]]},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert cannot_remove_occupied_room.status_code == 409

        seat_taken_during_review = client.patch(
            f"/api/v1/bookings/{fourth_booking.json()['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert seat_taken_during_review.status_code == 200
        assert seat_taken_during_review.json()["status"] == "rejected"
        assert "No seats remain available" in seat_taken_during_review.json()["resolution_note"]

        rejection_notifications = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert rejection_notifications.status_code == 200
        assert any(
            item["event_type"] == "booking_rejected"
            and item["booking_id"] == fourth_booking.json()["id"]
            for item in rejection_notifications.json()["items"]
        )

        no_seats = client.post(
            "/api/v1/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert no_seats.status_code == 409
        assert "No seats are available" in no_seats.json()["detail"]

        later_booking = client.post(
            "/api/v1/bookings",
            json={
                **booking_payload,
                "move_in_date": (date.today() + timedelta(days=240)).isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert later_booking.status_code == 201, later_booking.text
        later_approval = client.patch(
            f"/api/v1/bookings/{later_booking.json()['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert later_approval.status_code == 200, later_approval.text
        assert later_approval.json()["room_name"] == "Room 1"
        assert later_approval.json()["seat_number"] == 1

        student_cancel_approved = client.patch(
            f"/api/v1/bookings/{later_booking.json()['id']}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_cancel_approved.status_code == 200, student_cancel_approved.text
        assert student_cancel_approved.json()["status"] == "cancelled"
        assert student_cancel_approved.json()["cancelled_at"]
        assert student_cancel_approved.json()["cancelled_by"]

        replacement_booking = client.post(
            "/api/v1/bookings",
            json={
                **booking_payload,
                "move_in_date": (date.today() + timedelta(days=240)).isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert replacement_booking.status_code == 201, replacement_booking.text
        replacement_approval = client.patch(
            f"/api/v1/bookings/{replacement_booking.json()['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert replacement_approval.status_code == 200, replacement_approval.text
        assert replacement_approval.json()["room_name"] == "Room 1"
        assert replacement_approval.json()["seat_number"] == 1

        for approved_booking_id in (first_data["id"], third_booking.json()["id"]):
            owner_cancel = client.patch(
                f"/api/v1/bookings/{approved_booking_id}/status",
                json={"status": "cancelled"},
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert owner_cancel.status_code == 200, owner_cancel.text

        move_in_today_booking = client.post(
            "/api/v1/bookings",
            json={
                **booking_payload,
                "move_in_date": date.today().isoformat(),
                "duration_months": 1,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert move_in_today_booking.status_code == 201, move_in_today_booking.text
        move_in_today_approval = client.patch(
            f"/api/v1/bookings/{move_in_today_booking.json()['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert move_in_today_approval.status_code == 200, move_in_today_approval.text

        student_cancel_after_move_in = client.patch(
            f"/api/v1/bookings/{move_in_today_booking.json()['id']}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_cancel_after_move_in.status_code == 403
        owner_cancel_after_move_in = client.patch(
            f"/api/v1/bookings/{move_in_today_booking.json()['id']}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_cancel_after_move_in.status_code == 200, owner_cancel_after_move_in.text
        assert owner_cancel_after_move_in.json()["status"] == "cancelled"

        admin_cancel_booking = client.post(
            "/api/v1/bookings",
            json={
                **booking_payload,
                "move_in_date": date.today().isoformat(),
                "duration_months": 1,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert admin_cancel_booking.status_code == 201, admin_cancel_booking.text
        admin_cancel_approval = client.patch(
            f"/api/v1/bookings/{admin_cancel_booking.json()['id']}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert admin_cancel_approval.status_code == 200, admin_cancel_approval.text
        app.dependency_overrides[get_current_user] = lambda: admin
        try:
            admin_cancel = client.patch(
                f"/api/v1/bookings/{admin_cancel_booking.json()['id']}/status",
                json={"status": "cancelled"},
            )
            assert admin_cancel.status_code == 200, admin_cancel.text
            assert admin_cancel.json()["status"] == "cancelled"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        past_booking = client.post(
            "/api/v1/bookings",
            json={
                **booking_payload,
                "move_in_date": (date.today() - timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert past_booking.status_code == 422
