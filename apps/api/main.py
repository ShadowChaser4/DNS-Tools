from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to the DNS Tools API! Use the /dns endpoint to perform DNS lookups."
    }
