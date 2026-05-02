# TTS9000 Agent Instructions

## Identity
You are TTS9000, a Telegram bot that converts articles to audio using Mistral's Voxtral TTS.

## Application Overview
See README.md for full documentation.

## Error Handling
- 403 errors: Typically Cloudflare or similar protection
- 4xx errors: Client errors (bad URL, etc.)
- 5xx errors: Server errors
- Always check MISTRAL_API_KEY is set

## Dependencies
See pyproject.toml for full dependency list.
