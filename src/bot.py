#!/usr/bin/env python3
"""Sunflower Telegram Bot"""

import asyncio
import logging
import os
import signal
import time

from dotenv import load_dotenv
from telegram import InputMediaAudio, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

from suno_api import create_generating_tasks, get_generated_tracks

# Load environment variables from .env file
load_dotenv()

# Set up logging to see what's happening
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

commands_description = """ 
Commands:
/gen - generate music by prompt
/help - Show help information
/about - Learn about this bot
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user_name = update.effective_user.first_name
    welcome_message = f"""
🤖 Hello {user_name}! Welcome to my learning bot!
{commands_description}
    """

    await update.message.reply_text(welcome_message)
    logger.info(f"User {user_name} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = f"""
Help Information
{commands_description}
If you're having trouble, try restarting with /start
    """

    await update.message.reply_text(help_text)
    logger.info("Help command used")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /about command"""
    about_text = """
ℹ️ About This Bot

🎓 Created during: FortuneTunes Workshop 2
🐍 Language: Python
📚 Library: python-telegram-bot
👨‍💻 Purpose: Learning bot development basics

This bot demonstrates:
• Command handling (/start, /help, /about)
• Message echoing
• Basic error handling
• Logging and monitoring

Keep learning and building! 🚀
    """

    await update.message.reply_text(about_text)
    logger.info("About command used")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.startswith("/gen"):
        await update.message.reply_text("wrong format")
        return

    prompt = text[4:]

    user_name = update.effective_user.first_name

    if not prompt:
        await update.message.reply_text("Prompt is required")
        return

    logger.info(f"Generating for {user_name} by prompt: {prompt}")

    try:
        all_tracks = await _gen_tracks(update, prompt)

        if not all_tracks:
            return

        media = []
        for idx, (url, title) in enumerate(all_tracks):
            media.append(InputMediaAudio(media=url, title=f"{idx + 1}-{title}"))

        await update.message.reply_media_group(media=media)
    except Exception as ex:
        await update.message.reply_text(f"Error: {ex}")
        logger.exception(ex)


GENERATION_TIMEOUT = 300
SLEEP_INTERVAL = 30
TASKS_COUNT = 1


async def _gen_tracks(update: Update, prompt):
    tasks_ids = create_generating_tasks(prompt, count=TASKS_COUNT)

    all_tracks = []

    msg = await update.message.reply_text("⏳ Processing...")
    start_time = time.time()
    unfinished_tasks = set(tasks_ids)
    while unfinished_tasks:
        elapsed = time.time() - start_time
        if elapsed > GENERATION_TIMEOUT:
            await update.message.reply_text("Generation timed out, try again")
            return

        await asyncio.sleep(SLEEP_INTERVAL)
        await msg.edit_text(f"⏳ Processing... ({elapsed:.0f}s)")

        for task_id in tuple(unfinished_tasks):
            tracks = get_generated_tracks(task_id)
            if tracks:
                all_tracks.extend(tracks)
                unfinished_tasks.remove(task_id)

    return all_tracks


def main():
    logger.info("🤖 Starting bot...")

    request = HTTPXRequest(
        connect_timeout=10,
        read_timeout=600,
    )

    application = Application.builder().token(BOT_TOKEN).request(request).build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("gen", gen_command))
    application.add_handler(CommandHandler("start", start_command))

    application.add_error_handler(error_handler)

    # IMPORTANT for Render:
    application.run_polling(
        stop_signals=[signal.SIGINT, signal.SIGTERM],
        close_loop=False,
    )


if __name__ == "__main__":
    main()
