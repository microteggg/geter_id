import asyncio
import json
import re
from typing import Any

from .config import IDX_BINARY


SYMBOL_RE = re.compile(
    r"^[A-Z0-9]{1,12}$"
)


class IDXClientError(RuntimeError):
    pass


async def _run_idx(
    *args: str,
) -> Any:

    try:
        proc = await asyncio.create_subprocess_exec(
            IDX_BINARY,
            "-o",
            "json",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    except FileNotFoundError as exc:

        raise IDXClientError(
            "IDX engine tidak ditemukan di server."
        ) from exc


    stdout, stderr = (
        await proc.communicate()
    )


    if proc.returncode != 0:

        error_message = stderr.decode(
            errors="replace"
        ).strip()

        raise IDXClientError(
            error_message
            or f"idx exit code {proc.returncode}"
        )


    try:

        return json.loads(
            stdout.decode()
        )

    except json.JSONDecodeError as exc:

        raise IDXClientError(
            "IDX engine mengembalikan JSON tidak valid."
        ) from exc


def clean_symbol(
    symbol: str,
) -> str:

    value = (
        symbol
        .strip()
        .upper()
        .removesuffix(".JK")
    )


    if not SYMBOL_RE.fullmatch(value):

        raise IDXClientError(
            "Kode saham tidak valid."
        )


    return value


async def version():

    return await _run_idx(
        "version",
    )


async def quote(
    symbol: str,
):

    symbol = clean_symbol(
        symbol
    )

    return await _run_idx(
        "stocks",
        "quote",
        symbol,
    )


async def history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
    limit: int = 30,
):

    symbol = clean_symbol(
        symbol
    )


    allowed_periods = {
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y",
        "10y",
        "ytd",
        "max",
    }


    allowed_intervals = {
        "5m",
        "15m",
        "30m",
        "1h",
        "1d",
        "1wk",
        "1mo",
    }


    if (
        period not in allowed_periods
        or interval not in allowed_intervals
    ):

        raise IDXClientError(
            "Period atau interval tidak didukung."
        )


    limit = max(
        1,
        min(limit, 500),
    )


    return await _run_idx(
        "stocks",
        "history",
        symbol,
        "--period",
        period,
        "--interval",
        interval,
        "--limit",
        str(limit),
    )


async def technical(
    symbol: str,
    period: str = "1y",
):

    symbol = clean_symbol(
        symbol
    )

    return await _run_idx(
        "stocks",
        "technical",
        symbol,
        "--period",
        period,
    )


async def market_overview(
    top: int = 10,
):

    top = max(
        1,
        min(top, 50),
    )


    return await _run_idx(
        "market",
        "overview",
        "--top",
        str(top),
    )
