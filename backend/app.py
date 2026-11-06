from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.staticfiles import (
    StaticFiles,
)

from .config import (
    APP_NAME,
    APP_VERSION,
    CORS_ORIGINS,
)

from . import idx_client


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def fail(
    exc: Exception,
):

    raise HTTPException(
        status_code=503,
        detail=str(exc),
    ) from exc


@app.get(
    "/api/health"
)
async def health():

    try:

        await idx_client.version()

        engine = "online"

    except Exception as exc:

        engine = (
            f"offline: {exc}"
        )


    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "idx_engine": engine,
    }


@app.get(
    "/api/quote/{symbol}"
)
async def quote(
    symbol: str,
):

    try:

        return await idx_client.quote(
            symbol
        )

    except idx_client.IDXClientError as exc:

        fail(exc)


@app.get(
    "/api/history/{symbol}"
)
async def history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
    limit: int = Query(
        30,
        ge=1,
        le=500,
    ),
):

    try:

        return await idx_client.history(
            symbol,
            period,
            interval,
            limit,
        )

    except idx_client.IDXClientError as exc:

        fail(exc)


@app.get(
    "/api/technical/{symbol}"
)
async def technical(
    symbol: str,
    period: str = "1y",
):

    try:

        return await idx_client.technical(
            symbol,
            period,
        )

    except idx_client.IDXClientError as exc:

        fail(exc)


@app.get(
    "/api/market"
)
async def market(
    top: int = Query(
        10,
        ge=1,
        le=50,
    ),
):

    try:

        return await (
            idx_client.market_overview(
                top
            )
        )

    except idx_client.IDXClientError as exc:

        fail(exc)


app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True,
    ),
    name="frontend",
)
