FROM node:22-bookworm-slim AS engine
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
# Pin sumber upstream agar rebuild tidak mengikuti perubahan main secara diam-diam.
ARG IDX_COMMIT=5b32d8cb1e6633656e6f23aca72568a8645ce2b7
RUN npm install --prefix /opt/idx --global "github:fzn0x/idx#${IDX_COMMIT}" && /opt/idx/bin/idx --version

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=engine /usr/local/bin/node /usr/local/bin/node
COPY --from=engine /opt/idx /opt/idx
ENV PATH="/opt/idx/bin:${PATH}" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000 IDX_BINARY=idx IDX_PROGRESS=never IDX_PROVIDER=auto
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 app
COPY --chown=app:app backend ./backend
COPY --chown=app:app frontend ./frontend
USER app
# Pastikan binary juga dapat diakses user non-root.
RUN idx --version
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/health',timeout=3)"
CMD ["sh", "-c", "exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-proxy-headers"]
