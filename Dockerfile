FROM python:3.14-alpine AS builder

WORKDIR /app

COPY pyproject.toml .

RUN apk add --no-cache ffmpeg && \
    pip install uv && \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --system -r requirements.txt

FROM python:3.14-alpine

WORKDIR /app

RUN apk add --no-cache ffmpeg

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /app .
COPY main.py .

ENTRYPOINT ["python", "main.py"]

LABEL org.opencontainers.container.app="tts9000"
