from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .core import connect_to_mongo, close_mongo, initialize_odm

from .dns.router import router as dns_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to and close shared resources."""
    await connect_to_mongo(app)
    await initialize_odm(app.state.mongo_db)
    try:
        yield
    finally:
        await close_mongo(app)


app = FastAPI(
    title="DNS Tools API",
    description="A simple API for performing DNS lookups and related operations.",
    version="0.0.1",
    lifespan=lifespan,
)


class RootResponseModel(BaseModel):
    message: str


@app.get("/", response_model=RootResponseModel)
async def root() -> RootResponseModel:
    return RootResponseModel(
        message="Welcome to the DNS Tools API! Use the /dns endpoint to perform DNS lookups."
    )


app.include_router(dns_router)
