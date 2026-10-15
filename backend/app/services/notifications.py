async def send_booking_notification(email: str, subject: str, message: str) -> dict:
    # Local prototype adapter: integrate SMTP or a transactional email provider later.
    return {"sent": False, "mode": "mock", "recipient": email, "subject": subject, "message": message}
