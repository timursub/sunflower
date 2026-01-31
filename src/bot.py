#!/usr/bin/env python3
"""Sunflower Telegram Bot"""

import asyncio
import logging
import os
import signal
import time

from dotenv import load_dotenv
from telegram import InputMediaAudio, Message, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from suno_api import create_generating_tasks, get_generated_tracks, download_audio

# Load environment variables from .env file
load_dotenv()

# Set up logging to see what's happening
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

commands_description = """ 

 Available Commands
 /start - Start the bot and see a quick introduction.
 /gen <your prompt>
   Generate music using Suno AI.
   Example: /gen chill lofi beat with soft piano and rain sounds
 /help - Show help menu with information about the bot and its commands.
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    if not update.effective_user:
        return
    user_name = update.effective_user.first_name
    welcome_message = f"""
Hello {user_name}! Welcome to Sunflower Music Generator Bot!

This bot lets you generate music tracks using Suno AI.
Describe the music you want, and the bot will generate 6 unique tracks and send them to you as MP3 files.
{commands_description}
    """

    if update.message:
        await update.message.reply_text(welcome_message)
    logger.info(f"User {user_name} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = f"""
Help Information
{commands_description}

If any trouble occurred, try to restart the bot using the /start command
"""

    if update.message:
        await update.message.reply_text(help_text)
    logger.info("Help command used")



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text
    if not text or not text.startswith("/gen"):
        await update.message.reply_text("wrong format")
        return

    prompt = text[4:]

    user_name = "unknown"
    if update.effective_user:
        user_name = update.effective_user.first_name

    if not prompt:
        await update.message.reply_text("Prompt is required")
        return

    logger.info(f"Generating for {user_name} by prompt: {prompt}")

    context.application.create_task(_gen_and_send(update.message, prompt))


GENERATION_TIMEOUT = 300
SLEEP_INTERVAL = 30
TASKS_COUNT = 1


async def _gen_and_send(message: Message, prompt: str):
    try:
        all_tracks = await _gen_tracks(message, prompt)

        if not all_tracks:
            return

        await _send_tracks(message, all_tracks)

    except Exception as ex:
        logger.exception(ex)
        await message.reply_text("An error occurred during generation")


async def _gen_tracks(message: Message, prompt):
    tasks_ids = await create_generating_tasks(prompt, count=TASKS_COUNT)

    all_tracks = []

    msg = await message.reply_text("Processing...")
    start_time = time.time()
    unfinished_tasks = set(tasks_ids)
    while unfinished_tasks:
        await asyncio.sleep(SLEEP_INTERVAL)

        elapsed = time.time() - start_time
        if elapsed > GENERATION_TIMEOUT:
            await message.reply_text("Generation timed out, try again")
            return

        await msg.edit_text(f"Processing... ({elapsed:.0f}s)")

        for task_id in tuple(unfinished_tasks):
            tracks = await get_generated_tracks(task_id)
            if tracks:
                all_tracks.extend(tracks)
                unfinished_tasks.remove(task_id)

    await msg.delete()

    return all_tracks



async def _send_tracks(message: Message, all_tracks):
    msg = await message.reply_text("Downloading")
    downloaded_files = []
    for idx, (url, title) in enumerate(all_tracks):
        filename = f"{idx + 1}-{title}.mp3"
        try:
            audio_data = await download_audio(url)
            downloaded_files.append((audio_data, filename))
            await msg.edit_text(f"Downloading ({idx}/{len(all_tracks)})")
        except Exception as e:
            logger.error(f"Failed to download {title}: {e}")

    if not downloaded_files:
        await message.reply_text("Failed to download audio files")
        return
    await msg.edit_text("Sending tracks")
    media = [
        InputMediaAudio(media=data, filename=name) for data, name in downloaded_files
    ]

    await message.reply_media_group(media=media)
    await msg.delete()


def main():
    logger.info(" Starting bot...")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gen", gen_command))
    application.add_handler(CommandHandler("start", start_command))

    application.add_error_handler(error_handler)

    application.run_polling(
        poll_interval=1.0,
        stop_signals=[signal.SIGINT, signal.SIGTERM],
    )


if __name__ == "__main__":
    main()
