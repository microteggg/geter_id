from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    APP_NAME,
    APP_VERSION,
    CORS_ORIGINS,
)
from .idx_client import (
    IDXClientError,
    get_quote,
)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Backend API untuk Dashboard Saham Indonesia.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/api/quote/{symbol}")
async def quote(symbol: str):
    try:
        data = await get_quote(symbol)

        return {
            "status": "ok",
            "symbol": symbol.upper(),
            "data": data,
        }

    except IDXClientError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
