from contextlib import asynccontextmanager
from pathlib import Path

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models import Booking, Listing, Review, User
from app.routers import admin, auth, bookings, listings, reviews

UPLOAD_PATH = Path(settings.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    await client.admin.command("ping")
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Listing, Booking, Review],
    )
    app.state.mongo_client = client
    yield
    client.close()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_PATH)), name="uploads")

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(listings.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings.router, prefix=settings.API_V1_PREFIX)
app.include_router(reviews.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["health"])
async def root():
    return {"name": settings.APP_NAME, "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
