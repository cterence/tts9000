FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv && \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["python", "main.py"]

LABEL org.opencontainers.container.app="tts9000"
