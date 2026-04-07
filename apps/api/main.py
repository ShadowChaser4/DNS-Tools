from fastapi import FastAPI
from pydantic import BaseModel

from .dns.router import router as dns_router

app = FastAPI(
    title="DNS Tools API",
    description="A simple API for performing DNS lookups and related operations.",
    version="0.0.1",
)


class RootResponseModel(BaseModel):
    message: str


@app.get("/", response_model=RootResponseModel)
async def root() -> RootResponseModel:
    return RootResponseModel(
        message="Welcome to the DNS Tools API! Use the /dns endpoint to perform DNS lookups."
    )


app.include_router(dns_router)
