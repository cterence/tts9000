# TTS9000

Text-to-Speech service using Mistral's Voxtral TTS. Extracts article text from URLs, cleans it with Mistral, and converts to audio.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended)
- ffmpeg (for audio processing)

## Features

- Web server with `/generate?url=<URL>` endpoint
- Telegram bot for URL processing
- CLI for direct URL processing
- Automatic language detection (English/French)
- Caching of generated audio files
- Proper audio duration calculation using ffmpeg
- MP3 header fixing for accurate duration in Telegram
- Progress updates in Telegram bot

## Usage

### Environment Variables

- `MISTRAL_API_KEY`: Required for Mistral API access
- `TELEGRAM_BOT_TOKEN`: Required for Telegram bot mode
- `MODE`: Set to `cli`, `server`, or `telegram` (default: `cli`)
- `PORT`: Set to change the server port (default: `8000`)

### Docker

```bash
# Build
docker build -t tts9000 .

# Run as web server
docker run -p 8000:8000 -e MISTRAL_API_KEY=your_key tts9000

# Run as Telegram bot
docker run -e MISTRAL_API_KEY=your_key -e TELEGRAM_BOT_TOKEN=your_token -e MODE=telegram tts9000

# Run as CLI
docker run -e MISTRAL_API_KEY=your_key tts9000 --mode cli https://example.com/article
```

### Direct Execution

```bash
# Install dependencies
uv sync

# CLI mode (default)
uv run main.py https://example.com/article

# Web server mode
uv run main.py --mode server

# Telegram bot mode
uv run main.py --mode telegram
```

### API Endpoint

```
GET /generate?url=<URL>
```

Returns MP3 audio file directly.

### Telegram Bot

Send any URL to the bot to receive the article as audio.

### AI Disclosure

AI was used to write code for this application.
