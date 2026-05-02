import argparse
import base64
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from mistralai.client import Mistral
from fastapi import FastAPI, HTTPException, Response
import uvicorn
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import io


def extract_article_text(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning(f"Cloudflare or similar block detected for {url}")
            raise Exception(
                f"Access blocked (403) for {url}. Site may have Cloudflare or similar protection."
            )
        elif e.response.status_code >= 400 and e.response.status_code < 500:
            raise Exception(f"Client error ({e.response.status_code}) for {url}")
        elif e.response.status_code >= 500:
            raise Exception(f"Server error ({e.response.status_code}) for {url}")
        else:
            raise Exception(f"HTTP error ({e.response.status_code}) for {url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed for {url}: {str(e)}")


def clean_text_with_mistral(text, api_key):
    client = Mistral(api_key=api_key)
    prompt = f"""Remove all headers, footers, navigation menus, advertisements, and any non-article content from the following text. Return only the clean article text:

{text}
"""
    response = client.chat.complete(
        model="mistral-medium-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content


def detect_language(text):
    try:
        from langdetect import detect

        return detect(text)
    except:
        return "en"


def generate_tts(text, api_key):
    client = Mistral(api_key=api_key)
    language = detect_language(text)
    voice_id = "gb_jane_neutral" if language == "en" else "fr_marie_neutral"
    response = client.audio.speech.complete(
        model="voxtral-mini-tts-2603",
        input=text,
        voice_id=voice_id,
        response_format="mp3",
    )
    return base64.b64decode(response.audio_data)


def sanitize_url(url):
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    clean = urlunparse(
        parsed._replace(fragment="", query="", path=parsed.path.rstrip("/"))
    )
    return clean


def get_cache_filename(url):
    clean_url = sanitize_url(url)
    url_hash = hashlib.md5(clean_url.encode()).hexdigest()
    return f"generated/{url_hash}.mp3"


def sanitize_filename(text):
    import re
    text = re.sub(r'[<>:"\|?*\x00-\x1f]', '', text)
    return text[:100]


def get_article_filename(url, api_key):
    try:
        raw_text = extract_article_text(url)
        client = Mistral(api_key=api_key)
        prompt = f"""Extract the main title or headline from the following article text. Return only the title:

{raw_text[:2000]}
"""
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        title = response.choices[0].message.content.strip()
        return sanitize_filename(title) if title else "article"
    except Exception:
        return "article"


def process_url(url, api_key):
    cache_dir = Path("generated")
    cache_dir.mkdir(exist_ok=True)
    cache_file = Path(get_cache_filename(url))

    if cache_file.exists():
        print(f"Using cached file: {cache_file}")
        return cache_file.read_bytes()

    raw_text = extract_article_text(url)
    clean_text = clean_text_with_mistral(raw_text, api_key)
    audio_data = generate_tts(clean_text, api_key)
    cache_file.write_bytes(audio_data)
    return audio_data


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/generate")
async def generate_audio(url: str):
    logger.info(f"Processing URL: {url}")
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        logger.error("MISTRAL_API_KEY not set")
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY not set")
    try:
        audio_data = process_url(url, api_key)
        logger.info(f"Successfully generated audio for {url}")
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        error_msg = str(e)
        if "403" in error_msg or "blocked" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a URL and I'll convert the article to audio!"
    )


def get_article_title(url, api_key):
    try:
        raw_text = extract_article_text(url)
        client = Mistral(api_key=api_key)
        prompt = f"""Extract the main title or headline from the following article text. Return only the title:

{raw_text[:2000]}
"""
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        title = response.choices[0].message.content.strip()
        return title if title else "article"
    except Exception:
        return "article"


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(
            "Please send a valid URL starting with http:// or https://"
        )
        return

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        await update.message.reply_text("Server misconfigured. Please try again later.")
        return

    try:
        msg = await update.message.reply_text(f"Extracting text from {url}...")
        article_title = get_article_title(url, api_key)
        await msg.edit_text(f"Generating TTS for {article_title}...")
        audio_data = process_url(url, api_key)
        import ffmpeg
        cache_file = get_cache_filename(url)
        temp_file = cache_file + ".temp"
        Path(temp_file).write_bytes(audio_data)
        cache_file = get_cache_filename(url)
        try:
            (
                ffmpeg
                .input(temp_file)
                .output(cache_file, acodec='copy')
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            logger.error(f"ffmpeg error: {e.stderr.decode()}")
            raise
        probe = ffmpeg.probe(cache_file)
        duration = int(float(probe['format']['duration']))
        logger.info(f"Audio duration: {duration}s")
        Path(temp_file).unlink()
        await msg.delete()
        await update.message.reply_audio(
            audio=Path(cache_file).read_bytes(), title=article_title, duration=duration
        )
    except Exception as e:
        logger.error(f"Error processing URL for Telegram: {str(e)}")
        error_msg = str(e)
        if "403" in error_msg or "blocked" in error_msg.lower():
            error_msg = "🚫 Access blocked. This site may have Cloudflare or similar protection that prevents automated access."
        await update.message.reply_text(error_msg)


def run_telegram_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.run_polling()


def main():
    parser = argparse.ArgumentParser(
        description="TTS9000 - Text-to-Speech Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://example.com/article         # CLI mode (default)
  python main.py --mode server                      # Web server mode
  python main.py --mode telegram                    # Telegram bot mode
        """
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "server", "telegram"],
        default=None,
        help="Running mode: 'cli' processes a single URL, 'server' starts web API, 'telegram' starts bot"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL to process (required for CLI mode)"
    )
    args = parser.parse_args()

    mode = args.mode or os.getenv("MODE", "cli")

    if mode == "server":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif mode == "telegram":
        run_telegram_bot()
    else:
        if not args.url:
            print("Usage: uv run main.py [--mode cli|server|telegram] <URL>")
            sys.exit(1)

        url = args.url
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("MISTRAL_API_KEY environment variable not set")
            sys.exit(1)

        print(f"Extracting text from {url}...")
        raw_text = extract_article_text(url)

        print("Cleaning text with Mistral...")
        clean_text = clean_text_with_mistral(raw_text, api_key)

        article_name = get_article_filename(url, api_key)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"generated/{article_name}_{timestamp}.mp3"

        print(f"Generating TTS...")
        audio_data = generate_tts(clean_text, api_key)
        Path(output_filename).write_bytes(audio_data)
        print(f"Saved to {output_filename}")


if __name__ == "__main__":
    main()
