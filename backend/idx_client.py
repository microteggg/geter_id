import asyncio
import json
from typing import Any

from .config import IDX_BINARY


class IDXClientError(RuntimeError):
    pass


async def _run_idx(*args: str) -> Any:
    """
    Menjalankan engine idx dan meminta output JSON.

    Tidak ada shell=True.
    Argumen diteruskan langsung agar lebih aman.
    """

    try:
        process = await asyncio.create_subprocess_exec(
            IDX_BINARY,
            "-o",
            "json",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise IDXClientError(
            "Binary idx belum terpasang pada server."
        ) from exc

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_message = stderr.decode(
            "utf-8",
            errors="replace",
        ).strip()

        raise IDXClientError(
            error_message or "idx command gagal dijalankan."
        )

    raw = stdout.decode(
        "utf-8",
        errors="replace",
    ).strip()

    if not raw:
        raise IDXClientError(
            "idx tidak mengembalikan data."
        )

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IDXClientError(
            "Output idx bukan JSON yang valid."
        ) from exc


async def get_quote(symbol: str) -> Any:
    symbol = symbol.upper().strip()

    if not symbol:
        raise IDXClientError(
            "Kode saham tidak boleh kosong."
        )

    if not symbol.isalnum():
        raise IDXClientError(
            "Kode saham tidak valid."
        )

    return await _run_idx(
        "stocks",
        "quote",
        symbol,
    )
