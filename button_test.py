import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token - using the same as main bot for testing
BOT_TOKEN = "7835457395:AAHOVKzTw2PXo1GR_fy1-szjQdmBhhSWF7I"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with all the main buttons"""
    keyboard = [
        [InlineKeyboardButton("👤 Owner", url="https://t.me/IIG_DARK_YT")],
        [InlineKeyboardButton("📺 Main Channel", url="https://t.me/+IImrx0b9OxswNTk1")],
        [InlineKeyboardButton("👥 Community Group", url="https://t.me/+EYYrooTFGEdiZWE1")],
        [InlineKeyboardButton("📂 Proofs Channel", url="https://t.me/PROOFSxxDARK")],
        [InlineKeyboardButton("💳 Payments", callback_data="payments_menu")],
        [InlineKeyboardButton("🎮 Games", callback_data="games_menu")],
        [InlineKeyboardButton("💡 Daily Quote", callback_data="daily_quote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✨ Welcome to Button Test!\n\n"
        "Click any button to test if it works:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button presses"""
    query = update.callback_query
    await query.answer()
    
    # Handle different button presses
    if query.data == "payments_menu":
        keyboard = [
            [InlineKeyboardButton("📱 Generate QR", callback_data="generate_qr")],
            [InlineKeyboardButton("📋 Copy UPI ID", callback_data="copy_upi_id")],
            [InlineKeyboardButton("📸 I Paid (Upload Screenshot)", callback_data="upload_payment")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💳 Payment Options\n\nWorks for all payments: Paytm / GPay / PhonePe", reply_markup=reply_markup)
        
    elif query.data == "games_menu":
        keyboard = [
            [InlineKeyboardButton("🪙 Head or Tails", callback_data="game_coin")],
            [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="game_rps")],
            [InlineKeyboardButton("⭕ Tic Tac Toe", callback_data="game_ttt")],
            [InlineKeyboardButton("🔤 Hangman", callback_data="game_hangman")],
            [InlineKeyboardButton("🎲 Dice Roll", callback_data="game_dice")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🎮 Mini Games\n\nChoose a game to play:", reply_markup=reply_markup)
        
    elif query.data == "daily_quote":
        await query.edit_message_text("💡 Daily Motivation\n\n\"The only way to do great work is to love what you do.\"\n- Steve Jobs")
        
    elif query.data == "main_menu":
        await start(update, context)
        
    else:
        await query.edit_message_text(f"You pressed: {query.data}")

def main() -> None:
    """Start the test bot"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Run the bot
    logger.info("Button test bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()