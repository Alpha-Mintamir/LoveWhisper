from flask import Flask, request, Response
import logging
import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, InlineQueryHandler
import time

from config import TELEGRAM_TOKEN, RESPONSE_STYLES
from user_manager import UserManager
from ai_handler import AIHandler
from main import start, help_command, style_command, button_callback, set_name_command, add_detail_command, handle_message, inline_query

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize user manager and AI handler
user_manager = UserManager()
ai_handler = AIHandler()

# Get environment variables
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://lovewhisper-5vbu.onrender.com')

# Initialize bot application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("style", style_command))
application.add_handler(CommandHandler("setname", set_name_command))
application.add_handler(CommandHandler("adddetail", add_detail_command))
application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(InlineQueryHandler(inline_query))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook route
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
async def webhook():
    """Handle incoming webhook updates from Telegram."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
    return Response('ok', status=200)

# Health check route
@app.route('/')
def index():
    return 'Bot is running!'

# Setup webhook function
async def setup_webhook():
    """Set up the webhook asynchronously."""
    url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook()
    await bot.set_webhook(url=url)
    logger.info(f"Webhook set to {url}")

# Set up the webhook using the Telegram Bot API directly
def set_webhook_sync():
    """Set up webhook using requests (synchronous)."""
    import requests
    url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url}"
    response = requests.get(api_url)
    logger.info(f"Webhook set to {url}. Response: {response.text}")

# Call the synchronous version at startup
set_webhook_sync()

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=PORT) 