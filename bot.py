import logging
import os
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, ADMIN_IDS, UPI_ID, OWNER_LINK, PROOFS_CHANNEL, GROUP_LINK, MAIN_CHANNEL_LINK
from database import init_db, create_user, get_user, update_user_interaction, update_user_stats, get_user_stats, get_leaderboard, is_user_banned
from utils import init_directories, generate_qr_code, cleanup_temp_files
from games import TicTacToe, Hangman, coin_toss, rock_paper_scissors, dice_roll
from quotes import fetch_quote_from_api, fetch_joke_from_api, fetch_fact_from_api
from ai import fetch_ai_response, fetch_search_results_wrapper, detect_user_intent, get_personalized_recommendation
from payments import PaymentProcessor
from admin import AdminDashboard
from keep_alive import keep_alive

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
payment_processor = PaymentProcessor()
admin_dashboard = AdminDashboard()
user_game_states = {}  # user_id -> game_state

def initialize_bot():
    """Initialize bot components"""
    init_db()
    init_directories()
    logger.info("Bot initialized successfully")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a dynamic welcome message"""
    user = update.effective_user
    create_user(user.id, user.username, user.first_name, user.last_name)
    update_user_interaction(user.id)
    
    logger.info(f"User {user.first_name} ({user.id}) started the bot")
    
    # Check if this is the special user
    from ai import special_user_feature
    special_message = await special_user_feature(user.id)
    
    if special_message:
        # Special welcome for VIP user
        welcome_message = (
            f"{special_message}\n\n"
            f"✨ Welcome, {user.first_name}!\n\n"
            "🔐 Your gateway to premium features\n\n"
            "👤 OWNER: @IIG_DARK_YT\n"
            f"📱 UPI: {UPI_ID}\n"
            "📂 PROOFS: @PROOFSxxDARK\n"
            "📺 CHANNEL: Premium Content\n"
            "👥 GROUP: Community Hub\n"
            "📢 STATUS: DARK HERE ✅\n\n"
            "Available Commands:\n"
            "💳 /payments - Generate Payment QR\n"
            "📸 /proofs - View Latest Proofs\n"
            "📺 /channel - Join Main Channel\n"
            "🎮 /games - Play Mini Games\n"
            "💡 /quote - Get Motivational Quote\n"
            "🔍 /search - Search Content\n"
            "📊 /stats - View Statistics\n"
            "🆘 /help - List All Commands"
        )
    else:
        # Regular welcome message with user's first name
        welcome_message = (
            f"✨ Welcome, {user.first_name}!\n\n"
            "🔐 Your gateway to premium features\n\n"
            "👤 OWNER: @IIG_DARK_YT\n"
            f"📱 UPI: {UPI_ID}\n"
            "📂 PROOFS: @PROOFSxxDARK\n"
            "📺 CHANNEL: Premium Content\n"
            "👥 GROUP: Community Hub\n"
            "📢 STATUS: DARK HERE ✅\n\n"
            "Available Commands:\n"
            "💳 /payments - Generate Payment QR\n"
            "📸 /proofs - View Latest Proofs\n"
            "📺 /channel - Join Main Channel\n"
            "🎮 /games - Play Mini Games\n"
            "💡 /quote - Get Motivational Quote\n"
            "🔍 /search - Search Content\n"
            "📊 /stats - View Statistics\n"
            "🆘 /help - List All Commands"
        )
    
    # Enhanced inline keyboard with nested menus
    keyboard = [
        [InlineKeyboardButton("👤 Owner", url=OWNER_LINK)],
        [InlineKeyboardButton("📺 Main Channel", url=MAIN_CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Community Group", url=GROUP_LINK)],
        [InlineKeyboardButton("📂 Proofs Channel", url=PROOFS_CHANNEL)],
        [InlineKeyboardButton("💳 Payments", callback_data="payments_menu")],
        [InlineKeyboardButton("🎮 Games", callback_data="games_menu")],
        [InlineKeyboardButton("💡 Daily Quote", callback_data="daily_quote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        await update.message.reply_text("Sorry, something went wrong!")

# --- Admin Dashboard Handlers ---

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin dashboard"""
    await admin_dashboard.show_dashboard(update, context)

# --- Admin Dashboard Callback Handlers ---

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin dashboard callbacks"""
    query = update.callback_query
    user = query.from_user
    
    # Check if user is admin
    from config import ADMIN_IDS
    if str(user.id) not in ADMIN_IDS:
        await query.answer("❌ Access denied. Admin only.", show_alert=True)
        return
    
    await query.answer()
    
    # Route to appropriate handler based on callback data
    if query.data == "admin_dashboard":
        await admin_dashboard.show_dashboard(update, context)
    elif query.data == "admin_users":
        await admin_dashboard.show_user_management(update, context)
    elif query.data == "admin_payments":
        await admin_dashboard.show_payment_management(update, context)
    elif query.data == "admin_broadcast":
        await admin_dashboard.show_broadcast_menu(update, context)
    elif query.data == "admin_analytics":
        await admin_dashboard.show_analytics(update, context)
    elif query.data == "admin_leaderboard":
        await admin_dashboard.show_leaderboard(update, context)
    elif query.data == "admin_list_users":
        await admin_dashboard.list_all_users(update, context)
    elif query.data == "admin_pending_payments":
        await admin_dashboard.show_pending_payments(update, context)
    elif query.data == "admin_create_broadcast":
        await admin_dashboard.create_broadcast_prompt(update, context)
    elif query.data == "admin_dm_user":
        await admin_dashboard.dm_user_prompt(update, context)
    elif query.data.startswith("admin_lb_"):
        await admin_dashboard.show_top_users(update, context, query.data)
    elif query.data == "admin_verified_payments":
        try:
            await query.answer("Verified payments view coming soon!")
        except Exception as e:
            logger.error(f"Error answering verified payments: {e}")
    elif query.data == "admin_rejected_payments":
        try:
            await query.answer("Rejected payments view coming soon!")
        except Exception as e:
            logger.error(f"Error answering rejected payments: {e}")
    elif query.data == "admin_search_user":
        try:
            await query.answer("User search coming soon!")
        except Exception as e:
            logger.error(f"Error answering user search: {e}")
    elif query.data == "admin_user_messages":
        try:
            await query.answer("User messages view coming soon!")
        except Exception as e:
            logger.error(f"Error answering user messages: {e}")
    elif query.data == "admin_schedule_broadcast":
        try:
            await query.answer("Scheduled broadcasts coming soon!")
        except Exception as e:
            logger.error(f"Error answering scheduled broadcasts: {e}")
    elif query.data == "admin_scheduled_broadcasts":
        try:
            await query.answer("View scheduled broadcasts coming soon!")
        except Exception as e:
            logger.error(f"Error answering view scheduled broadcasts: {e}")
    elif query.data == "admin_detailed_analytics":
        try:
            await query.answer("Detailed analytics coming soon!")
        except Exception as e:
            logger.error(f"Error answering detailed analytics: {e}")
    elif query.data == "admin_engagement":
        try:
            await query.answer("Engagement metrics coming soon!")
        except Exception as e:
            logger.error(f"Error answering engagement metrics: {e}")
    elif query.data == "admin_top_users":
        try:
            await query.answer("Top users view coming soon!")
        except Exception as e:
            logger.error(f"Error answering top users: {e}")
    elif query.data == "admin_settings":
        try:
            await query.answer("Settings coming soon!")
        except Exception as e:
            logger.error(f"Error answering settings: {e}")
    elif query.data == "admin_ban_unban":
        await admin_dashboard.ban_unban_user_prompt(update, context)
    return

# --- Payment Handlers ---

async def payments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /payments command - show payment options menu"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    # Create the payment menu message
    payment_message = (
        "💳 Payment Options\n\n"
        "Works for all payments: Paytm / GPay / PhonePe\n"
        f"UPI ID: {UPI_ID}\n\n"
        "Select an option below:"
    )
    
    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton("📱 Generate QR", callback_data="generate_qr")],
        [InlineKeyboardButton("📋 Copy UPI ID", callback_data="copy_upi_id")],
        [InlineKeyboardButton("📸 Upload Payment Screenshot", callback_data="upload_payment")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.message.reply_text(payment_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error sending payments menu: {e}")
        await update.message.reply_text("❌ Sorry, unable to display payments menu at the moment!")

async def payments_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show payment options menu"""
    query = update.callback_query
    await query.answer()
    
    payment_message = (
        "💳 Payment Options\n\n"
        "Works for all payments: Paytm / GPay / PhonePe\n"
        f"UPI ID: {UPI_ID}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📱 Generate QR", callback_data="generate_qr")],
        [InlineKeyboardButton("📋 Copy UPI ID", callback_data="copy_upi_id")],
        [InlineKeyboardButton("📸 I Paid (Upload Screenshot)", callback_data="upload_payment")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(payment_message, reply_markup=reply_markup)

async def generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send UPI QR code"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'payments_requested')
    
    logger.info(f"User {user.first_name} requested QR code")
    
    try:
        # Generate QR code
        qr_filename = f"temp/upi_{user.id}.png"
        if generate_qr_code(UPI_ID, qr_filename):
            # Send photo with caption
            with open(qr_filename, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=f"📱 Scan & Pay: {UPI_ID}\n\n✅ Works for all payments: Paytm / GPay / PhonePe"
                )
            
            # Delete the image file
            os.remove(qr_filename)
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Sorry, unable to generate QR code at the moment!"
            )
        
        # Return to payments menu
        await payments_menu(update, context)
            
    except Exception as e:
        logger.error(f"Error generating/sending QR code: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Sorry, unable to generate QR code at the moment!"
        )

async def copy_upi_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send UPI ID for copying"""
    query = update.callback_query
    await query.answer(text=f"UPI ID: {UPI_ID} (Copied to clipboard)", show_alert=True)
    
    user = query.from_user
    update_user_stats(user.id, 'payments_requested')
    
    # Return to payments menu
    await payments_menu(update, context)

async def upload_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to upload payment screenshot"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📸 Please upload a screenshot of your payment.\n\n"
        "I'll automatically verify the details using OCR technology!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back", callback_data="payments_menu")
        ]])
    )

# --- Game Handlers ---

async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show games menu"""
    query = update.callback_query
    await query.answer()
    
    games_message = (
        "🎮 Mini Games\n\n"
        "Choose a game to play:"
    )
    
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
    
    await query.edit_message_text(games_message, reply_markup=reply_markup)

async def game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Head or Tails game"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'games_played')
    
    message = coin_toss()
    
    keyboard = [
        [InlineKeyboardButton("👑 Heads", callback_data="coin_heads")],
        [InlineKeyboardButton("🔄 Tails", callback_data="coin_tails")],
        [InlineKeyboardButton("🔄 New Game", callback_data="game_coin")],
        [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def game_rps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Rock Paper Scissors game"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'games_played')
    
    message = rock_paper_scissors()
    
    keyboard = [
        [InlineKeyboardButton("✊ Rock", callback_data="rps_rock")],
        [InlineKeyboardButton("✋ Paper", callback_data="rps_paper")],
        [InlineKeyboardButton("✌️ Scissors", callback_data="rps_scissors")],
        [InlineKeyboardButton("🔄 New Game", callback_data="game_rps")],
        [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def game_ttt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Tic Tac Toe game"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'games_played')
    
    # Initialize game
    user_game_states[user.id] = TicTacToe()
    game = user_game_states[user.id]
    
    message = game.display_board()
    message += "\n\nChoose a position (1-9):\n1 2 3\n4 5 6\n7 8 9"
    
    # Create keyboard for positions
    keyboard = []
    for i in range(1, 10, 3):
        keyboard.append([
            InlineKeyboardButton(str(i), callback_data=f"ttt_{i}"),
            InlineKeyboardButton(str(i+1), callback_data=f"ttt_{i+1}"),
            InlineKeyboardButton(str(i+2), callback_data=f"ttt_{i+2}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔄 New Game", callback_data="game_ttt")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="games_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def game_hangman(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Hangman game"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'games_played')
    
    # Initialize game
    user_game_states[user.id] = Hangman()
    game = user_game_states[user.id]
    
    message = game.display_game()
    message += "\n\nGuess a letter:"
    
    # Create keyboard for letters
    keyboard = []
    for i in range(0, 26, 4):
        row = []
        for j in range(4):
            if i + j < 26:
                letter = chr(65 + i + j)
                row.append(InlineKeyboardButton(letter, callback_data=f"hangman_{letter}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 New Game", callback_data="game_hangman")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="games_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Dice Roll game"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'games_played')
    
    message = dice_roll()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Roll Again", callback_data="game_dice")],
        [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show games leaderboard"""
    query = update.callback_query
    await query.answer()
    
    leaderboard_data = get_leaderboard(10)
    
    if not leaderboard_data:
        message = "🏆 Games Leaderboard\n\nNo games played yet!"
    else:
        message = "🏆 Games Leaderboard\n\n"
        for i, (user_id, first_name, games_played) in enumerate(leaderboard_data, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            message += f"{medal} {first_name or 'Unknown'} - {games_played} games\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="leaderboard")],
        [InlineKeyboardButton("🎮 Play Games", callback_data="games_menu")],
        [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

# --- Game Interaction Handlers ---

async def handle_coin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle coin toss game interaction"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract choice from callback data
    choice = "Heads" if "heads" in query.data else "Tails"
    message = coin_toss(choice)
    
    keyboard = [
        [InlineKeyboardButton("👑 Heads", callback_data="coin_heads")],
        [InlineKeyboardButton("🔄 Tails", callback_data="coin_tails")],
        [InlineKeyboardButton("🔄 New Game", callback_data="game_coin")],
        [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def handle_rps_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Rock Paper Scissors choice"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Extract choice from callback data
    choice_map = {"rps_rock": "Rock", "rps_paper": "Paper", "rps_scissors": "Scissors"}
    choice = choice_map.get(query.data, "Rock")
    
    message = rock_paper_scissors(choice)
    
    keyboard = [
        [InlineKeyboardButton("✊ Rock", callback_data="rps_rock")],
        [InlineKeyboardButton("✋ Paper", callback_data="rps_paper")],
        [InlineKeyboardButton("✌️ Scissors", callback_data="rps_scissors")],
        [InlineKeyboardButton("🔄 New Game", callback_data="game_rps")],
        [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def handle_ttt_move(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Tic Tac Toe move"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if user.id not in user_game_states:
        await query.edit_message_text("❌ Game not found. Please start a new game!")
        return
    
    game = user_game_states[user.id]
    
    # Extract position from callback data
    try:
        position = int(query.data.split("_")[1])
        message = game.make_move(position)
        
        # Check if game is over
        if game.game_over:
            keyboard = [
                [InlineKeyboardButton("🔄 New Game", callback_data="game_ttt")],
                [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
            ]
            del user_game_states[user.id]  # Clean up
        else:
            # Continue game
            keyboard = []
            for i in range(1, 10, 3):
                keyboard.append([
                    InlineKeyboardButton(str(i), callback_data=f"ttt_{i}"),
                    InlineKeyboardButton(str(i+1), callback_data=f"ttt_{i+1}"),
                    InlineKeyboardButton(str(i+2), callback_data=f"ttt_{i+2}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔄 New Game", callback_data="game_ttt")])
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="games_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error in Tic Tac Toe game: {e}")
        await query.edit_message_text("❌ Something went wrong!", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="game_ttt")],
            [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
        ]))

async def handle_hangman_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Hangman letter guess"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if user.id not in user_game_states:
        await query.edit_message_text("❌ Game not found. Please start a new game!")
        return
    
    game = user_game_states[user.id]
    
    # Extract letter from callback data
    letter = query.data.split("_")[1]
    
    message = game.make_guess(letter)
    
    # Check if game is over
    if "Congratulations" in message or "Game Over" in message:
        keyboard = [
            [InlineKeyboardButton("🔄 New Game", callback_data="game_hangman")],
            [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
        ]
        del user_game_states[user.id]  # Clean up
    else:
        # Continue game
        # Create keyboard for letters
        keyboard = []
        for i in range(0, 26, 4):
            row = []
            for j in range(4):
                if i + j < 26:
                    letter_btn = chr(65 + i + j)
                    row.append(InlineKeyboardButton(letter_btn, callback_data=f"hangman_{letter_btn}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔄 New Game", callback_data="game_hangman")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="games_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)

# --- Quote Handlers ---

async def daily_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a motivational quote"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    update_user_stats(user.id, 'quotes_read')
    
    # Fetch quote from API or database
    quote_data = await fetch_quote_from_api()
    
    quote_message = f"💡 Daily Motivation\n\n\"{quote_data['quote']}\"\n- {quote_data['author']}"
    
    keyboard = [
        [InlineKeyboardButton("⏭ Next Quote", callback_data="daily_quote")],
        [InlineKeyboardButton("❤️ Like", callback_data="like_quote")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(quote_message, reply_markup=reply_markup)

async def like_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quote like"""
    query = update.callback_query
    await query.answer(text="❤️ Quote liked!", show_alert=True)

# --- Main Menu ---

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user(user.id)
    
    welcome_message = (
        f"✨ Welcome, {user.first_name}!\n\n"
        "🔐 Your gateway to premium features\n\n"
        "👤 OWNER: @IIG_DARK_YT\n"
        f"📱 UPI: {UPI_ID}\n"
        "📂 PROOFS: @PROOFSxxDARK\n"
        "📺 CHANNEL: Premium Content\n"
        "👥 GROUP: Community Hub\n"
        "📢 STATUS: DARK HERE ✅\n\n"
        "Available Commands:\n"
        "💳 /payments - Generate Payment QR\n"
        "📸 /proofs - View Latest Proofs\n"
        "📺 /channel - Join Main Channel\n"
        "🎮 /games - Play Mini Games\n"
        "💡 /quote - Get Motivational Quote\n"
        "🔍 /search - Search Content\n"
        "📊 /stats - View Statistics\n"
        "🆘 /help - List All Commands"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 Owner", url=OWNER_LINK)],
        [InlineKeyboardButton("📺 Main Channel", url=MAIN_CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Community Group", url=GROUP_LINK)],
        [InlineKeyboardButton("📂 Proofs Channel", url=PROOFS_CHANNEL)],
        [InlineKeyboardButton("💳 Payments", callback_data="payments_menu")],
        [InlineKeyboardButton("🎮 Games", callback_data="games_menu")],
        [InlineKeyboardButton("💡 Daily Quote", callback_data="daily_quote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome_message, reply_markup=reply_markup)

# --- Original Command Handlers ---

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send UPI QR code (original command)"""
    user = update.effective_user
    update_user_stats(user.id, 'payments_requested')
    
    logger.info(f"User {user.first_name} requested QR code via command")
    
    try:
        # Generate QR code
        qr_filename = f"temp/upi_{user.id}.png"
        if generate_qr_code(UPI_ID, qr_filename):
            # Send photo with caption
            with open(qr_filename, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📱 Scan & Pay: {UPI_ID}\n\n✅ Works for all payments: Paytm / GPay / PhonePe"
                )
            
            # Delete the image file
            os.remove(qr_filename)
        else:
            await update.message.reply_text("❌ Sorry, unable to generate QR code at the moment!")
            
    except Exception as e:
        logger.error(f"Error generating/sending QR code: {e}")
        await update.message.reply_text("❌ Sorry, unable to generate QR code at the moment!")

async def proofs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send proof channel link"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    logger.info(f"User {user.first_name} requested proofs")
    
    try:
        message = f"📸 Latest Verified Proofs\n\n📂 See all proofs here: {PROOFS_CHANNEL}"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error sending proofs link: {e}")
        await update.message.reply_text("❌ Sorry, unable to provide proofs link at the moment!")

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send channel link"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    logger.info(f"User {user.first_name} requested channel link")
    
    try:
        message = f"📺 Join Our Premium Channel: {MAIN_CHANNEL_LINK}"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error sending channel link: {e}")
        await update.message.reply_text("❌ Sorry, unable to provide channel link at the moment!")

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /games command"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    await games_menu(update, context)

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quote command"""
    user = update.effective_user
    update_user_stats(user.id, 'quotes_read')
    
    # Fetch quote from API or database
    quote_data = await fetch_quote_from_api()
    
    quote_message = f"💡 Daily Motivation\n\n\"{quote_data['quote']}\"\n- {quote_data['author']}"
    
    await update.message.reply_text(quote_message)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    user_stats = get_user_stats(user.id)
    
    if not user_stats:
        stats_message = "📊 No statistics available yet!"
    else:
        stats_message = (
            f"📊 {user.first_name}'s Stats\n\n"
            f"🎮 Games Played: {user_stats['games_played']}\n"
            f"💡 Quotes Read: {user_stats['quotes_read']}\n"
            f"💳 Payments Requested: {user_stats['payments_requested']}\n"
            f"✅ Successful Payments: {user_stats['successful_payments']}"
        )
    
    await update.message.reply_text(stats_message)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command with simple search"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    # Get search query from command arguments
    query = " ".join(context.args) if context.args else ""
    
    if not query:
        await update.message.reply_text(
            "🔍 Simple Web Search\n\n"
            "Usage: /search <your query>\n\n"
            "Examples:\n"
            "/search artificial intelligence\n"
            "/search python programming\n"
            "/search latest technology news"
        )
        return
    
    await update.message.reply_text("🔍 Searching for information...")
    
    # Use simple search
    result = await fetch_search_results_wrapper(query)
    await update.message.reply_text(result)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ask command with AI response"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    # Get question from command arguments
    question = " ".join(context.args) if context.args else ""
    
    if not question:
        await update.message.reply_text(
            "❓ Ask a Question\n\n"
            "Usage: /ask <your question>\n\n"
            "Examples:\n"
            "/ask What is quantum computing?\n"
            "/ask How does photosynthesis work?\n"
            "/ask What are the latest AI developments?"
        )
        return
    
    await update.message.reply_text("🤔 Thinking...")
    result = await fetch_ai_response(question)
    await update.message.reply_text(f"🤖 {result}")

async def similar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /similar command - not available with simple search"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    await update.message.reply_text(
        "❌ The 'similar content' feature is not available with the simple search system.\n"
        "Please use the /search command instead."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    logger.info(f"User {user.first_name} requested help")
    
    # Check if this is the VIP user
    is_vip = user.id == 5550412770
    
    help_text = (
        "🆘 Complete Command List\n\n"
        "Core Commands:\n"
        "⭐ /start - Main menu with all features\n"
        "💳 /payments - Generate payment QR codes\n"
        "📱 /qr - Generate UPI QR code\n"
        "📸 /proofs - View latest payment proofs\n"
        "📺 /channel - Join our main channel\n\n"
        "Fun & Interactive:\n"
        "🎮 /games - Play mini games\n"
        "💡 /quote - Get motivational quote\n"
        "📊 /stats - View your statistics\n"
        "🔍 /search <query> - Search web content\n"
        "❓ /ask <question> - Ask questions with AI\n"
        "📖 /ocr - Extract text from images\n"
        "🎛️ /admin - Admin dashboard (admin only)\n"
    )
    
    if is_vip:
        help_text += "👑 /vip_features - VIP exclusive features\n"
    
    help_text += (
        "🆘 /help - Show this help message\n\n"
        "AI Features:\n"
        "• Web Search - Find latest information on any topic\n"
        "• AI Question Answering - Get answers to your questions\n"
        "• OCR Text Extraction - Extract text from images\n"
        "• Hugging Face AI - Conversational responses\n\n"
        "All features are accessible through the interactive menu too!"
    )
    
    try:
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Error sending help message: {e}")
        await update.message.reply_text("❌ Sorry, unable to display help at the moment!")

# --- Message Handlers ---

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo uploads (payment screenshots)"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    # Check if we're expecting a payment screenshot or OCR request
    # This would be handled by the payment processor or OCR processor
    await payment_processor.process_payment_screenshot(update, context)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads (images for OCR)"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    # Check if this is an image file for OCR processing
    document = update.message.document
    if document:
        # Check file type
        if document.mime_type and document.mime_type.startswith('image/'):
            await update.message.reply_text("🔍 Processing image for text extraction...")
            
            # Download the file
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp/{user.id}_{document.file_id}.jpg"
            
            # Download the file
            await file.download_to_drive(file_path)
            
            # Process with OCR
            from utils import process_payment_screenshot
            result = process_payment_screenshot(file_path)
            
            # Clean up the file
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
            
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("❌ Please upload an image file (JPG, PNG, etc.) for text extraction.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages"""
    user = update.effective_user
    
    # Check if user is banned (cached for performance)
    if is_user_banned(user.id):
        try:
            await update.message.reply_text("🚫 You have been banned from using this bot.")
        except Exception as e:
            logger.error(f"Error sending ban message to user {user.id}: {e}")
        return
    
    update_user_interaction(user.id)
    text = update.message.text
    
    # Check if we're waiting for a broadcast message from admin
    if context.user_data.get('awaiting_broadcast'):
        await admin_dashboard.send_broadcast(update, context)
        return
    
    # Check if we're waiting for a DM from admin
    if context.user_data.get('awaiting_dm'):
        await admin_dashboard.send_dm(update, context)
        return
    
    # Check if we're waiting for a ban/unban command from admin
    if context.user_data.get('awaiting_ban_unban'):
        await admin_dashboard.handle_ban_unban(update, context)
        return
    
    # Special feature for user ID 5550412770
    if user.id == 5550412770 and text.lower() in ['vip', 'special', 'tanish']:
        await update.message.reply_text(
            "👑 VIP ACCESS GRANTED 👑\n\n"
            "🎉 Welcome TANISH! You have access to exclusive features:\n\n"
            "✨ Unlimited searches\n"
            "🎮 All games unlocked\n"
            "💎 Premium quotes and content\n"
            "🚀 Priority support\n"
            "🎁 Special rewards and bonuses\n\n"
            "Type /vip_features to see all your exclusive privileges!"
        )
        return
    
    # Detect user intent with error handling
    try:
        intent = await detect_user_intent(text)
    except Exception as e:
        logger.error(f"Error detecting user intent: {e}")
        intent = 'unknown'
    
    if intent == 'payment':
        await update.message.reply_text(
            "💳 Payment Information\n\n"
            f"📱 UPI ID: {UPI_ID}\n"
            "✅ Works for all payments: Paytm / GPay / PhonePe\n\n"
            "Use /payments to generate a QR code or upload a payment screenshot!"
        )
    elif intent == 'game':
        await games_menu(update, context)
    elif intent == 'quote':
        await quote_command(update, context)
    elif intent == 'help':
        await help_command(update, context)
    elif intent == 'search':
        # Handle search queries
        search_query = text.replace('search', '').replace('find', '').replace('look for', '').strip()
        if search_query:
            try:
                await update.message.reply_text("🔍 Searching for information...")
                result = await fetch_search_results_wrapper(search_query)
                await update.message.reply_text(result)
            except Exception as e:
                logger.error(f"Error processing search query: {e}")
                await update.message.reply_text("❌ Sorry, there was an error processing your search. Please try again.")
        else:
            await update.message.reply_text("❓ What would you like me to search for? Try: 'search quantum computing'")
    elif intent == 'question':
        # Handle questions with AI
        try:
            await update.message.reply_text("🤔 Thinking...")
            result = await fetch_ai_response(text)
            await update.message.reply_text(f"🤖 {result}")
        except Exception as e:
            logger.error(f"Error processing AI question: {e}")
            await update.message.reply_text("❌ Sorry, there was an error processing your question. Please try again.")
    else:
        # Use AI to generate response with better error handling
        try:
            ai_response = await fetch_ai_response(text)
            await update.message.reply_text(f"🤖 {ai_response}")
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            # Fallback response
            await update.message.reply_text("🤖 I'm here to help! Try using commands like /games, /quote, /search, or /payments.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries"""
    query = update.callback_query
    user = query.from_user
    
    # Immediately acknowledge the callback to prevent button loading issues
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")
        return
    
    # Check if user is banned
    if is_user_banned(user.id):
        try:
            await query.answer("🚫 You have been banned from using this bot.", show_alert=True)
        except Exception as e:
            logger.error(f"Error sending ban message to user {user.id}: {e}")
        return
    
    # Process the callback with error handling
    try:
        # Check if this is an admin callback
        if query.data.startswith("admin_"):
            # Check if user is admin
            from config import ADMIN_IDS
            if str(user.id) not in ADMIN_IDS:
                try:
                    await query.answer("❌ Access denied. Admin only.", show_alert=True)
                except Exception as e:
                    logger.error(f"Error answering admin access denied: {e}")
                return
            
            # Route to admin dashboard handlers
            await handle_admin_callback(update, context)
            return
        
        # Route to appropriate handler based on callback data
        if query.data == "payments_menu":
            await payments_menu(update, context)
        elif query.data == "main_menu":
            await main_menu(update, context)
        elif query.data == "generate_qr":
            await generate_qr(update, context)
        elif query.data == "copy_upi_id":
            await copy_upi_id(update, context)
        elif query.data == "upload_payment":
            await upload_payment(update, context)
        elif query.data == "games_menu":
            await games_menu(update, context)
        elif query.data == "game_coin":
            await game_coin(update, context)
        elif query.data == "game_rps":
            await game_rps(update, context)
        elif query.data == "game_ttt":
            await game_ttt(update, context)
        elif query.data == "game_hangman":
            await game_hangman(update, context)
        elif query.data == "game_dice":
            await game_dice(update, context)
        elif query.data == "leaderboard":
            await leaderboard(update, context)
        elif query.data.startswith("coin_"):
            await handle_coin_choice(update, context)
        elif query.data.startswith("rps_"):
            await handle_rps_choice(update, context)
        elif query.data.startswith("ttt_"):
            await handle_ttt_move(update, context)
        elif query.data.startswith("hangman_"):
            await handle_hangman_guess(update, context)
        elif query.data == "daily_quote":
            await daily_quote(update, context)
        elif query.data == "like_quote":
            await like_quote(update, context)
        elif query.data.startswith("approve_payment_"):
            parts = query.data.split("_")
            if len(parts) >= 4:
                user_id = int(parts[-2])
                payment_id = int(parts[-1])
                await payment_processor.handle_admin_approval(update, context, user_id, approved=True)
            else:
                user_id = int(query.data.split("_")[-1])
                await payment_processor.handle_admin_approval(update, context, user_id, approved=True)
        elif query.data.startswith("reject_payment_"):
            parts = query.data.split("_")
            if len(parts) >= 4:
                user_id = int(parts[-2])
                payment_id = int(parts[-1])
                await payment_processor.handle_admin_approval(update, context, user_id, approved=False)
            else:
                user_id = int(query.data.split("_")[-1])
                await payment_processor.handle_admin_approval(update, context, user_id, approved=False)
        else:
            # For unknown callbacks, just acknowledge and return to main menu
            try:
                await query.answer("Feature coming soon!")
            except Exception as e:
                logger.error(f"Error answering unknown callback: {e}")
            await main_menu(update, context)
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        try:
            await query.answer("❌ An error occurred. Please try again.")
        except Exception as e2:
            logger.error(f"Error answering callback query error: {e2}")
        # Try to return to main menu as fallback
        try:
            await main_menu(update, context)
        except Exception as e3:
            logger.error(f"Error returning to main menu: {e3}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

async def vip_features_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Special VIP features command for user ID 5550412770"""
    user = update.effective_user
    
    if user.id != 5550412770:
        await update.message.reply_text("❌ This feature is only available for VIP users.")
        return
    
    vip_message = (
        "👑 TANISH - VIP USER PRIVILEGES 👑\n\n"
        "🌟 Exclusive Features Unlocked:\n\n"
        "🔍 Unlimited searches\n"
        "🎮 All Games with Special Bonuses\n"
        "💡 Premium Quote Collections\n"
        "💳 Priority Payment Processing\n"
        "🏆 Leaderboard Immunity\n"
        "🎁 Daily VIP Rewards\n"
        "🚀 24/7 Priority Support\n"
        "🔒 Early Access to New Features\n"
        "🎭 Personalized Bot Responses\n"
        "🎊 Special Events Invitation\n\n"
        "Enjoy your premium experience! 🎉"
    )
    
    await update.message.reply_text(vip_message)

async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ocr command - extract text from uploaded image"""
    user = update.effective_user
    update_user_interaction(user.id)
    
    await update.message.reply_text(
        "📸 OCR Text Extraction\n\n"
        "Please upload an image containing text, and I'll extract the text for you!\n\n"
        "Supported formats: JPG, PNG, GIF, BMP, TIFF, WEBP\n"
        "Maximum file size: 10MB"
    )

def main() -> None:
    """Start the bot"""
    # Initialize bot components
    initialize_bot()
    
    # Keep the bot alive (for platforms like Replit)
    from keep_alive import keep_alive
    keep_alive()
    
    # Create the Application and pass it your bot's token
    from telegram.ext import Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("qr", qr_command))
    application.add_handler(CommandHandler("proofs", proofs_command))
    application.add_handler(CommandHandler("channel", channel_command))
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("similar", similar_command))
    application.add_handler(CommandHandler("vip_features", vip_features_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("payments", payments_command))
    application.add_handler(CommandHandler("ocr", ocr_command))  # Add OCR command
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))  # Add document handler for OCR
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Run the bot until the user presses Ctrl-C
    logger.info("EXTREME SIGMA Bot started successfully!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()