from fastapi import FastAPI, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .core import connect_to_mongo, close_mongo, initialize_odm
from .dns.router import router as dns_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to and close shared resources."""
    client = await connect_to_mongo()
    app.state.mongo_db = client
    await initialize_odm(app.state.mongo_db)
    try:
        yield
    finally:
        await close_mongo()
        app.state.mongo_db = None


app = FastAPI(
    title="DNS Tools API",
    description="A simple API for performing DNS lookups and related operations.",
    version="0.0.1",
    lifespan=lifespan,
)


class RootResponseModel(BaseModel):
    message: str


@app.get("/", response_model=RootResponseModel, tags=["Root"])
async def root() -> RootResponseModel:
    return RootResponseModel(
        message="Welcome to the DNS Tools API! Use the /dns endpoint to perform DNS lookups."
    )


@app.get("/health", response_model=RootResponseModel, tags=["Health"])
async def health(request: Request) -> RootResponseModel:
    try:
        app = request.app
        await app.state.mongo_db.command("ping")  # Check MongoDB connection
        return RootResponseModel(message="API is running smoothly.")
    except Exception as e:
        print(f"Health check failed: {e}", e)
        return RootResponseModel(message=f"API is not running smoothly")


app.include_router(dns_router)
