import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, InlineQueryHandler
import time

from config import TELEGRAM_TOKEN, RESPONSE_STYLES
from user_manager import UserManager
from ai_handler import AIHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize user manager and AI handler
user_manager = UserManager()
ai_handler = AIHandler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm your AI-powered romantic reply assistant. "
        f"Tag me in a conversation with @{context.bot.username} followed by your girlfriend's message, "
        f"and I'll help you craft the perfect response.\n\n"
        f"Use /help to see all available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Here's how to use me:\n\n"
        "1. Tag me in a conversation with @{} followed by your girlfriend's message\n"
        "2. I'll generate a thoughtful response for you\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/style - Change your response style\n"
        "/setname - Set your girlfriend's name\n"
        "/adddetail - Add a personal detail to remember\n"
    ).format(context.bot.username)
    
    await update.message.reply_text(help_text)

async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Change the response style."""
    keyboard = []
    for style, description in RESPONSE_STYLES.items():
        keyboard.append([InlineKeyboardButton(f"{style.capitalize()} - {description}", callback_data=f"style_{style}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your preferred response style:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("style_"):
        style = data.replace("style_", "")
        user_manager.update_style(user_id, style)
        await query.edit_message_text(f"Your response style has been updated to: {style.capitalize()}")
    
    elif data.startswith("copy_"):
        # Extract the message ID
        message_id = data.replace("copy_", "")
        
        # Find the response in the original message
        if query.message and query.message.text:
            # Extract the response from the HTML-formatted message
            response_text = query.message.text.split("\n\n")[1]
            
            # Show a notification that text is ready to copy
            await query.answer("Text ready to copy!")
            
            # We don't need to edit the message - the <code> tag already makes it easy to copy
    
    elif data.startswith("regen_"):
        # Extract the message ID
        message_id = data.replace("regen_", "")
        
        # Get the original message from context
        if context.user_data.get("messages") and message_id in context.user_data["messages"]:
            original_message = context.user_data["messages"][message_id]
            
            # Generate a new response
            user_data = user_manager.get_user(user_id)
            new_response = ai_handler.generate_response(original_message, user_data)
            
            # Add to history
            user_manager.add_to_history(user_id, (original_message, new_response))
            
            # Update the message with the new response
            keyboard = [
                [InlineKeyboardButton("📋 Copy Response", callback_data=f"copy_{message_id}")],
                [InlineKeyboardButton("🔄 Regenerate Response", callback_data=f"regen_{message_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Here's your response:\n\n<code>{new_response}</code>",
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await query.answer("Sorry, I couldn't find the original message.")

async def set_name_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set girlfriend's name."""
    if not context.args:
        await update.message.reply_text("Please provide your girlfriend's name. Example: /setname Emma")
        return
    
    name = " ".join(context.args)
    user_id = update.effective_user.id
    user_manager.update_girlfriend_name(user_id, name)
    
    await update.message.reply_text(f"Your girlfriend's name has been set to: {name}")

async def add_detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a personal detail."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Please provide a key and value. Example: /adddetail anniversary 'June 15th'"
        )
        return
    
    key = context.args[0]
    value = " ".join(context.args[1:])
    user_id = update.effective_user.id
    
    user_manager.add_personal_detail(user_id, key, value)
    await update.message.reply_text(f"Added personal detail: {key} = {value}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    message_text = update.message.text
    logger.info(f"Received message: {message_text}")
    
    # Get the bot's username
    bot_username = context.bot.username
    mention_text = f"@{bot_username}"
    
    # Check if this is a direct message to the bot or a mention
    is_direct_message = update.effective_chat.type == "private"
    is_mentioned = mention_text.lower() in message_text.lower()
    
    # Process the message if it's a direct message or a mention
    if is_direct_message or is_mentioned:
        # Extract the actual message content
        if is_mentioned:
            # Remove the mention from the message
            girlfriend_message = message_text.replace(mention_text, "").strip()
        else:
            girlfriend_message = message_text
        
        if not girlfriend_message:
            await update.message.reply_text(
                "Please include your girlfriend's message. For example: 'Hey, how was your day?'"
            )
            return
        
        user_id = update.effective_user.id
        user_data = user_manager.get_user(user_id)
        
        # Store the original message in user context for regeneration
        if not context.user_data.get("messages"):
            context.user_data["messages"] = {}
        
        # Generate a unique message ID
        message_id = f"msg_{user_id}_{int(time.time())}"
        context.user_data["messages"][message_id] = girlfriend_message
        
        # Generate AI response
        ai_response = ai_handler.generate_response(girlfriend_message, user_data)
        
        # Add to history
        user_manager.add_to_history(user_id, (girlfriend_message, ai_response))
        
        # Create a keyboard with copy and regenerate buttons
        keyboard = [
            [InlineKeyboardButton("📋 Copy Response", callback_data=f"copy_{message_id}")],
            [InlineKeyboardButton("🔄 Regenerate Response", callback_data=f"regen_{message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send response with buttons
        await update.message.reply_text(
            f"Here's your response:\n\n<code>{ai_response}</code>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline queries."""
    query = update.inline_query.query
    
    if not query:
        return
    
    logger.info(f"Received inline query: {query}")
    
    user_id = update.effective_user.id
    user_data = user_manager.get_user(user_id)
    
    try:
        # Generate AI response
        ai_response = ai_handler.generate_response(query, user_data)
        
        # Log the response for debugging
        logger.info(f"Generated AI response: {ai_response}")
        
        if not ai_response or ai_response.strip() == "":
            ai_response = "I couldn't generate a response. Please try a different message."
        
        # Create a result to send back
        results = [
            InlineQueryResultArticle(
                id="1",
                title="AI Response",
                description=f"Response to: {query[:30]}..." if len(query) > 30 else f"Response to: {query}",
                input_message_content=InputTextMessageContent(ai_response),
            )
        ]
        
        await update.inline_query.answer(results)
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        # Return a fallback response
        results = [
            InlineQueryResultArticle(
                id="error",
                title="Error generating response",
                description="Something went wrong. Please try again.",
                input_message_content=InputTextMessageContent("I encountered an error. Please try again with a different message."),
            )
        ]
        await update.inline_query.answer(results)

def run_polling():
    """Start the bot with polling (for development)."""
    # Create the Application
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

    # Log the bot's username when starting
    logger.info(f"Starting bot in polling mode...")
    
    # Run the bot with polling
    application.run_polling()

if __name__ == '__main__':
    run_polling()  # For local development