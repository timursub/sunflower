#!/usr/bin/env python3
"""
Simple Telegram Bot
This bot demonstrates basic message handling and commands.
"""

import os
import signal
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import time
import asyncio


from suno_api import generate_music, check_generation_status

# Load environment variables from .env file
load_dotenv()

# Set up logging to see what's happening
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user_name = update.effective_user.first_name
    welcome_message = f"""
🤖 Hello {user_name}! Welcome to my learning bot!

I'm a simple bot created during Workshop 2. Here's what I can do:

🎯 Commands:
/start - Show this welcome message
/help - Show help information
/about - Learn about this bot

💬 You can also send me any message and I'll echo it back to you!

Try sending me a message or use one of the commands above.
    """
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {user_name} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = """
🆘 Help Information

This is a learning bot created in Workshop 2. Here are the available commands:

/start - Welcome message and bot introduction
/help - Show this help message
/about - Information about this bot

You can also send me any text message and I'll echo it back to you!

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

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo back any text message"""
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    response = f"You said: '{user_message}'\n\n🔄 I'm echoing your message back to you, {user_name}!"
    
    await update.message.reply_text(response)
    logger.info(f"Echoed message from {user_name}: {user_message}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

max_wait_time = 300
poll_interval = 30

async def gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.effective_user.first_name

    logger.info(f"Generating by prompt: {user_message}")
    result = generate_music(user_message)
    if not result['success']:
        await update.message.reply_text(f"Error: {result}")
        return
    
    task_id = result["task_id"]

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_time:
            await update.message.reply_text(f"Error: Generation timed out")
            return
        
        status_result = check_generation_status(task_id)
        
        if not status_result['success']:
            continue

        if status_result['status'] == 'failed':
            logger.error(f"Generation error: {status_result}")
            await update.message.reply_text(f"Error: Generation failed")
            return

        if status_result['status'] == 'completed':
            audio_url = status_result['audio_url']
            logger.info(f"Complete: {audio_url}")
            await update.message.reply_text(f"Done: {audio_url}")
            return
        
        
        await update.message.reply_text(f"⏳ Processing... ({elapsed:.0f}s)")
        await asyncio.sleep(poll_interval)

    
async def shutdown(application: Application):
    logger.info("🛑 Shutting down bot gracefully...")
    await application.stop()
    await application.shutdown()
    logger.info("✅ Bot shutdown complete")


def main():
    logger.info("🤖 Starting the bot...")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("gen", gen_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_error_handler(error_handler)

    loop = asyncio.get_event_loop()

    async def run():
        await application.initialize()
        await application.start()
        await application.bot.initialize()
        await application.updater.start_polling()
        logger.info("✅ Bot is running")

        # Wait forever until signal
        await asyncio.Event().wait()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(application))
        )

    try:
        loop.run_until_complete(run())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
    
    


