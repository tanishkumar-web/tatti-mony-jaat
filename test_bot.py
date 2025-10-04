import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from config
BOT_TOKEN = "7835457395:AAHOVKzTw2PXo1GR_fy1-szjQdmBhhSWF7I"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with inline buttons"""
    keyboard = [
        [InlineKeyboardButton("Test Button 1", callback_data="button1")],
        [InlineKeyboardButton("Test Button 2", callback_data="button2")],
        [InlineKeyboardButton("_payments Menu", callback_data="payments_menu")],
        [InlineKeyboardButton("🎮 Games", callback_data="games_menu")],
        [InlineKeyboardButton("💡 Daily Quote", callback_data="daily_quote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text('Test bot with buttons:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "button1":
        await query.edit_message_text("You pressed Button 1!")
    elif query.data == "button2":
        await query.edit_message_text("You pressed Button 2!")
    elif query.data == "payments_menu":
        await query.edit_message_text("_payments Menu - This would show payment options")
    elif query.data == "games_menu":
        await query.edit_message_text("🎮 Games Menu - This would show games")
    elif query.data == "daily_quote":
        await query.edit_message_text("💡 Daily Quote - This would show a quote")

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Test bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()