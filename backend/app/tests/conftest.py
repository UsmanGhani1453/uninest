import asyncio
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


@pytest.fixture(autouse=True)
def isolated_mongodb_database():
    original_database_name = settings.DATABASE_NAME
    test_database_name = f"{original_database_name}_test_{uuid4().hex}"
    settings.DATABASE_NAME = test_database_name
    try:
        yield
    finally:
        async def drop_test_database():
            client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
            try:
                await client.drop_database(test_database_name)
            finally:
                client.close()

        try:
            asyncio.run(drop_test_database())
        finally:
            settings.DATABASE_NAME = original_database_name
