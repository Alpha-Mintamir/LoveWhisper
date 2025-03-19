import logging
import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, InlineQueryHandler
import time
import traceback
from quart import Quart, request, Response
import nest_asyncio

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

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Use Quart for async support
app = Quart(__name__)

# Initialize user manager and AI handler
user_manager = UserManager()
ai_handler = AIHandler()

# Get environment variables
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://lovewhisper-5vbu.onrender.com')

# Initialize bot application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Error handler
async def error_handler(update, context):
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update: {context.error}")
    logger.error(traceback.format_exc())

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("style", style_command))
application.add_handler(CommandHandler("setname", set_name_command))
application.add_handler(CommandHandler("adddetail", add_detail_command))
application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(InlineQueryHandler(inline_query))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_error_handler(error_handler)

# Initialize the application
async def initialize_application():
    await application.initialize()
    logger.info("Application initialized successfully")

# Run the initialization in the main thread
try:
    asyncio.run(initialize_application())
    logger.info("Application initialization completed")
except Exception as e:
    logger.error(f"Error initializing application: {e}")
    logger.error(traceback.format_exc())

# Webhook route - fully async
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
async def webhook():
    """Handle incoming webhook updates from Telegram."""
    try:
        logger.info("Received webhook request")
        update_json = await request.get_json()
        logger.info(f"Update JSON: {update_json}")
        
        update = Update.de_json(update_json, application.bot)
        await application.process_update(update)
        logger.info("Update processed successfully")
        
        return Response('ok', status=200)
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        logger.error(traceback.format_exc())
        return Response('error', status=500)

# Health check route
@app.route('/')
async def index():
    return 'Bot is running!'

# Set up the webhook using the Telegram Bot API directly
def set_webhook_sync():
    """Set up webhook using requests (synchronous)."""
    try:
        import requests
        url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url}"
        response = requests.get(api_url)
        logger.info(f"Webhook set to {url}. Response: {response.text}")
        
        # Also check if the bot can connect to Telegram API
        me_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        me_response = requests.get(me_url)
        logger.info(f"Bot info: {me_response.text}")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        logger.error(traceback.format_exc())

# Test Telegram connection
def test_telegram_connection():
    try:
        import requests
        response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe")
        logger.info(f"Telegram connection test: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram connection test failed: {e}")
        return False

# Call the synchronous version at startup
set_webhook_sync()

# Test connection
if test_telegram_connection():
    logger.info("Successfully connected to Telegram API")
else:
    logger.error("Failed to connect to Telegram API - check your network and token")

if __name__ == '__main__':
    # Run the Quart app
    app.run(host='0.0.0.0', port=PORT) 