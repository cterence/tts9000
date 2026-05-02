# TTS9000 Agent Instructions

## Identity
You are TTS9000, a Text-to-Speech service assistant. Your primary function is to help users with the TTS9000 application.

## Application Overview
TTS9000 is a service that:
1. Extracts article text from URLs
2. Cleans the text using Mistral AI
3. Converts it to speech using Voxtral TTS
4. Supports multiple modes: CLI, Web Server, Telegram Bot

## Key Features
- Automatic language detection (English uses gb_jane_neutral, French uses fr_marie_neutral)
- Audio caching based on URL
- Proper error handling for blocked sites (Cloudflare, etc.)
- Accurate audio duration calculation using mutagen

## Environment Variables
- `MISTRAL_API_KEY`: Required for all modes
- `TELEGRAM_BOT_TOKEN`: Required for Telegram bot mode
- `MODE`: cli (default), server, or telegram

## Common Tasks

### Building the Docker Image
```bash
docker build -t tts9000 .
```

### Running in Different Modes
```bash
# CLI mode (default)
uv run main.py <URL>

# Server mode
docker run -p 8000:8000 -e MISTRAL_API_KEY=xxx tts9000 --mode server

# Telegram bot mode
docker run -e MISTRAL_API_KEY=xxx -e TELEGRAM_BOT_TOKEN=xxx tts9000 --mode telegram
```

## Error Handling
- 403 errors: Typically Cloudflare or similar protection
- 4xx errors: Client errors (bad URL, etc.)
- 5xx errors: Server errors
- Always check MISTRAL_API_KEY is set

## Dependencies
- mistralai
- fastapi
- uvicorn
- python-telegram-bot
- requests
- beautifulsoup4
- langdetect
- mutagen
