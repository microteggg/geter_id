FROM node:22-bookworm-slim AS idx

RUN npm install -g github:fzn0x/idx \
    && idx version


FROM python:3.12-slim


COPY --from=idx \
    /usr/local/ \
    /usr/local/


WORKDIR /app


COPY requirements.txt .


RUN pip install \
    --no-cache-dir \
    -r requirements.txt


COPY backend ./backend

COPY frontend ./frontend


ENV IDX_BINARY=idx

ENV PORT=8000


EXPOSE 8000


CMD [
    "sh",
    "-c",
    "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"
]
