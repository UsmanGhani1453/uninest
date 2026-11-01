import asyncio
from getpass import getpass

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.security import hash_password
from app.models import Booking, Listing, Review, User


async def create_admin(full_name: str, email: str, password: str) -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command("ping")
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[User, Listing, Booking, Review],
        )
        normalized_email = email.strip().lower()
        if await User.find_one(User.email == normalized_email):
            raise ValueError(f"An account already exists for {normalized_email}; no account was changed.")

        user = User(
            full_name=full_name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            role="admin",
        )
        await user.insert()
    finally:
        client.close()


def main() -> None:
    full_name = input("Admin name: ").strip()
    email = input("Admin email: ").strip()
    password = getpass("Admin password (8-128 characters): ")
    confirmation = getpass("Confirm admin password: ")

    if len(full_name) < 2:
        raise ValueError("Admin name must contain at least 2 characters.")
    if not 8 <= len(password) <= 128:
        raise ValueError("Admin password must contain between 8 and 128 characters.")
    if password != confirmation:
        raise ValueError("Passwords do not match.")

    asyncio.run(create_admin(full_name, email, password))
    print(f"Admin account created for {email.lower()}.")


if __name__ == "__main__":
    main()
