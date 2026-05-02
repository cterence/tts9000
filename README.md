# TTS9000

Telegram bot that converts articles to audio using Mistral's Voxtral TTS. Extracts article text from URLs, cleans it with Mistral, and converts to audio.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended)
- ffmpeg (for audio processing)

## Features

- Telegram bot for URL processing
- Automatic language detection (English/French)
- Caching of generated audio files
- Proper audio duration calculation using ffmpeg
- MP3 header fixing for accurate duration in Telegram
- Progress updates in Telegram bot

## Usage

### Environment Variables

- `MISTRAL_API_KEY`: Required for Mistral API access
- `TELEGRAM_BOT_TOKEN`: Required for Telegram bot
- `ALLOWED_USERS`: Comma-separated list of Telegram usernames allowed to use the bot (empty = all users allowed)

### Docker

```bash
# Build
docker build -t tts9000 .

# Run as Telegram bot
docker run -e MISTRAL_API_KEY=your_key -e TELEGRAM_BOT_TOKEN=your_token tts9000
```

### Direct Execution

```bash
# Install dependencies
uv sync

# Run Telegram bot
uv run main.py
```

### Telegram Bot

Send any URL to the bot to receive the article as audio.

### AI Disclosure

AI was used to write code for this application.
