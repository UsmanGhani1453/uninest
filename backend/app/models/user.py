from datetime import datetime, timezone
from typing import Literal
from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    full_name: str = Field(min_length=2, max_length=100)
    email: Indexed(EmailStr, unique=True)
    phone: str | None = None
    password_hash: str
    role: Literal["student", "owner", "admin"] = "student"
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
