import os


APP_NAME = "GETER IDX API"
APP_VERSION = "0.2.0"

IDX_BINARY = os.getenv(
    "IDX_BINARY",
    "idx",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "*",
    ).split(",")
    if origin.strip()
]
