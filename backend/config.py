import os


APP_NAME = "GETER IDX API"
APP_VERSION = "0.1.0"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

IDX_BINARY = os.getenv("IDX_BINARY", "idx")

# Untuk Tahap 1 frontend lokal.
# Sebelum production, CORS akan diperketat.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
