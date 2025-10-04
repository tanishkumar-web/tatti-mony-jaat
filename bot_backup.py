import logging
import os
import qrcode
import json
import random
import asyncio
import aiohttp
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from PIL import Image

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and configuration
BOT_TOKEN = "7762063253:AAEqP6LHGCuRx0ToS84ne_gLqpwoXX_J03k"
UPI_ID = "9193896075-3@ibl"

# Links
OWNER_LINK = "https://t.me/IIG_DARK_YT"
PROOFS_CHANNEL = "https://t.me/PROOFSxxDARK"
GROUP_LINK = "https://t.me/+EYYrooTFGEdiZWE1"
MAIN_CHANNEL_LINK = "https://t.me/+IImrx0b9OxswNTk1"

# User data storage
user_data = {}

# Hangman words
HANGMAN_WORDS = [
    "PYTHON", "TELEGRAM", "BOT", "PAYMENT", "UPI", "SECURE", "SIGMA", "DARK", 
    "CHANNEL", "PROOFS", "GAME", "QUOTE", "INNOVATION", "TECHNOLOGY"
]

# Anti-spam tracking
user_message_count = {}

# API Keys (placeholders - replace with actual free API keys)
HUGGING_FACE_API_KEY = "API_KEY_HERE"
OPENWEATHER_API_KEY = "API_KEY_HERE"

# --- Utility Functions ---

def get_user_data(user_id):
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "first_name": "",
            "games_played": 0,
            "quotes_read": 0,
            "payments_requested": 0,
            "last_command": "",
            "game_state": {},
            "spam_count": 0,
            "last_interaction": datetime.now()
        }
    return user_data[user_id]

def check_spam(user_id):
    """Check if user is spamming"""
    current_time = datetime.now().timestamp()
    
    if user_id not in user_message_count:
        user_message_count[user_id] = []
    
    # Remove messages older than 10 seconds
    user_message_count[user_id] = [
        timestamp for timestamp in user_message_count[user_id] 
        if current_time - timestamp < 10
    ]
    
    # Add current message
    user_message_count[user_id].append(current_time)
    
    # If more than 5 messages in 10 seconds, it's spam
    if len(user_message_count[user_id]) > 5:
        user_data[user_id]["spam_count"] = user_data[user_id].get("spam_count", 0) + 1
        return True
    return False

async def fetch_quote_from_api():
    """Fetch a motivational quote from an online API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.quotable.io/random") as response:
                if response.status == 200:
                    data = await response.json()
                    return f"{data['content']} - {data['author']}"
    except Exception as e:
        logger.error(f"Error fetching quote from API: {e}")
    
    # Fallback quotes
    fallback_quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Your time is limited, don't waste it living someone else's life. - Steve Jobs",
        "Stay hungry, stay foolish. - Steve Jobs",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt"
    ]
    return random.choice(fallback_quotes)

async def fetch_joke_from_api():
    """Fetch a joke from an online API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/jokes/random") as response:
                if response.status == 200:
                    data = await response.json()
                    return f"{data['setup']}\n\n{data['punchline']}"
    except Exception as e:
        logger.error(f"Error fetching joke from API: {e}")
    
    # Fallback jokes
    fallback_jokes = [
        "Why don't scientists trust atoms?\n\nBecause they make up everything!",
        "What did one ocean say to the other ocean?\n\nNothing, they just waved!",
        "Why did the scarecrow win an award?\n\nBecause he was outstanding in his field!"
    ]
    return random.choice(fallback_jokes)

async def fetch_fact_from_api():
    """Fetch a random fact from an online API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/random.json?language=en") as response:
                if response.status == 200:
                    data = await response.json()
                    return data['text']
    except Exception as e:
        logger.error(f"Error fetching fact from API: {e}")
    
    # Fallback facts
    fallback_facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
        "A group of flamingos is called a 'flamboyance'.",
        "Octopuses have three hearts and blue blood."
    ]
    return random.choice(fallback_facts)

async def fetch_ai_response(prompt):
    """Fetch AI response from Hugging Face API"""
    try:
        headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
        payload = {"inputs": prompt}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api-inference.huggingface.co/models/gpt2",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0]['generated_text']
    except Exception as e:
        logger.error(f"Error fetching AI response: {e}")
    
    # Fallback response
    fallback_responses = [
        "That's an interesting point! Tell me more.",
        "I'm not sure I understand completely. Could you explain further?",
        "Thanks for sharing that with me!",
        "I appreciate your input on this topic."
    ]
    return random.choice(fallback_responses)

async def fetch_weather(city="London"):
    """Fetch weather information from OpenWeather API"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"Weather in {city}: {weather_desc}, Temperature: {temp}°C"
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
    
    return "Sorry, I couldn't fetch the weather information right now."

# --- Game Functions ---

def coin_toss(user_choice=None):
    """Head or Tails game"""
    choices = ["Heads", "Tails"]
    result = random.choice(choices)
    
    if user_choice is None:
        return "🎮 Head or Tails\n\nChoose your side:"
    
    if user_choice == result:
        outcome = "You win! 🎉"
    else:
        outcome = "I win! 😎"
    
    return f"🎮 Head or Tails\n\nYou chose: {user_choice}\nResult: {result}\n\n{outcome}"

def rock_paper_scissors(user_choice=None):
    """Rock Paper Scissors game"""
    choices = ["Rock", "Paper", "Scissors"]
    bot_choice = random.choice(choices)
    
    if user_choice is None:
        return "🎮 Rock Paper Scissors\n\nChoose your weapon:"
    
    # Determine winner
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == "Rock" and bot_choice == "Scissors") or \
         (user_choice == "Paper" and bot_choice == "Rock") or \
         (user_choice == "Scissors" and bot_choice == "Paper"):
        result = "You win! 🎉"
    else:
        result = "I win! 😎"
    
    emojis = {"Rock": "✊", "Paper": "✋", "Scissors": "✌️"}
    
    return f"🎮 Rock Paper Scissors\n\nYou: {emojis[user_choice]} {user_choice}\nMe: {emojis[bot_choice]} {bot_choice}\n\n{result}"

def initialize_tic_tac_toe_board():
    """Initialize Tic Tac Toe board"""
    return [
        ['_', '_', '_'],
        ['_', '_', '_'],
        ['_', '_', '_']
    ]

def display_tic_tac_toe_board(board):
    """Display Tic Tac Toe board"""
    board_str = "🎮 Tic Tac Toe\n\n"
    for i, row in enumerate(board):
        board_str += " | ".join(row) + "\n"
        if i < 2:
            board_str += "---------\n"
    return board_str

def make_tic_tac_toe_move(user_id, position):
    """Make a move in Tic Tac Toe"""
    user = get_user_data(user_id)
    
    if "tic_tac_toe" not in user["game_state"]:
        user["game_state"]["tic_tac_toe"] = {
            "board": initialize_tic_tac_toe_board(),
            "current_player": "X",  # User is X, bot is O
            "game_over": False
        }
    
    game = user["game_state"]["tic_tac_toe"]
    
    if game["game_over"]:
        return display_tic_tac_toe_board(game["board"]) + "\nGame over! Start a new game."
    
    # Convert position to row and column
    row = (position - 1) // 3
    col = (position - 1) % 3
    
    # Check if position is valid and empty
    if row < 0 or row > 2 or col < 0 or col > 2 or game["board"][row][col] != "_":
        return display_tic_tac_toe_board(game["board"]) + "\nInvalid move! Choose an empty position."
    
    # Make user move
    game["board"][row][col] = "X"
    
    # Check for win or tie
    result = check_tic_tac_toe_winner(game["board"])
    if result:
        game["game_over"] = True
        return display_tic_tac_toe_board(game["board"]) + f"\n{result}"
    
    # Bot's turn
    bot_move = get_tic_tac_toe_bot_move(game["board"])
    if bot_move:
        game["board"][bot_move[0]][bot_move[1]] = "O"
        result = check_tic_tac_toe_winner(game["board"])
        if result:
            game["game_over"] = True
            return display_tic_tac_toe_board(game["board"]) + f"\n{result}"
    
    return display_tic_tac_toe_board(game["board"])

def check_tic_tac_toe_winner(board):
    """Check for Tic Tac Toe winner"""
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != "_":
            return f"{'You win!' if row[0] == 'X' else 'I win!'} 🎉"
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != "_":
            return f"{'You win!' if board[0][col] == 'X' else 'I win!'} 🎉"
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != "_":
        return f"{'You win!' if board[0][0] == 'X' else 'I win!'} 🎉"
    if board[0][2] == board[1][1] == board[2][0] != "_":
        return f"{'You win!' if board[0][2] == 'X' else 'I win!'} 🎉"
    
    # Check for tie
    if all(cell != "_" for row in board for cell in row):
        return "It's a tie! 🤝"
    
    return None

def get_tic_tac_toe_bot_move(board):
    """Get bot move for Tic Tac Toe (simple AI)"""
    # Try to win
    for i in range(3):
        for j in range(3):
            if board[i][j] == "_":
                board[i][j] = "O"
                if check_tic_tac_toe_winner(board):
                    board[i][j] = "_"
                    return (i, j)
                board[i][j] = "_"
    
    # Try to block player
    for i in range(3):
        for j in range(3):
            if board[i][j] == "_":
                board[i][j] = "X"
                if check_tic_tac_toe_winner(board):
                    board[i][j] = "_"
                    return (i, j)
                board[i][j] = "_"
    
    # Take center if available
    if board[1][1] == "_":
        return (1, 1)
    
    # Take corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [corner for corner in corners if board[corner[0]][corner[1]] == "_"]
    if available_corners:
        return random.choice(available_corners)
    
    # Take any available spot
    for i in range(3):
        for j in range(3):
            if board[i][j] == "_":
                return (i, j)
    
    return None

def hangman_game(user_id, guess=None):
    """Hangman game"""
    user = get_user_data(user_id)
    
    if "hangman" not in user["game_state"]:
        # Start new game
        word = random.choice(HANGMAN_WORDS)
        user["game_state"]["hangman"] = {
            "word": word,
            "guessed_letters": set(),
            "incorrect_guesses": 0,
            "max_incorrect": 6
        }
    
    game = user["game_state"]["hangman"]
    
    if guess is None:
        # Display initial state
        display_word = " ".join([letter if letter in game["guessed_letters"] else "_" for letter in game["word"]])
        return f"🎮 Hangman\n\nWord: {display_word}\nIncorrect guesses: {game['incorrect_guesses']}/{game['max_incorrect']}\n\nGuess a letter:"
    
    # Process guess
    guess = guess.upper()
    
    if guess in game["guessed_letters"]:
        display_word = " ".join([letter if letter in game["guessed_letters"] else "_" for letter in game["word"]])
        return f"🎮 Hangman\n\nYou already guessed '{guess}'!\n\nWord: {display_word}\nIncorrect guesses: {game['incorrect_guesses']}/{game['max_incorrect']}\n\nGuess a letter:"
    
    game["guessed_letters"].add(guess)
    
    if guess in game["word"]:
        # Correct guess
        if all(letter in game["guessed_letters"] for letter in game["word"]):
            # Won
            del user["game_state"]["hangman"]
            return f"🎉 Congratulations! You won!\n\nThe word was: {game['word']}"
    else:
        # Incorrect guess
        game["incorrect_guesses"] += 1
        if game["incorrect_guesses"] >= game["max_incorrect"]:
            # Lost
            del user["game_state"]["hangman"]
            return f"😢 Game Over!\n\nThe word was: {game['word']}\nBetter luck next time!"
    
    # Display current state
    display_word = " ".join([letter if letter in game["guessed_letters"] else "_" for letter in game["word"]])
    return f"🎮 Hangman\n\nWord: {display_word}\nIncorrect guesses: {game['incorrect_guesses']}/{game['max_incorrect']}\n\nGuess a letter:"

def dice_roll():
    """Dice rolling simulator"""
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    dice_emojis = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅"
    }
    
    return f"🎲 Dice Roll\n\n{dice_emojis[dice1]} + {dice_emojis[dice2]} = {total}\n\nRoll again?"

# --- Payment Functions ---

async def generate_qr_code(data, filename):
    """Generate QR code for given data"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)
        return True
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return False

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a dynamic welcome message with enhanced inline buttons"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["first_name"] = user.first_name
    user_info["last_command"] = "/start"
    
    logger.info(f"User {user.first_name} ({user.id}) started the bot")
    
    # Dynamic welcome message with user's first name
    welcome_message = (
        f"✨ Welcome, {user.first_name}, to Guy's Bot!\n\n"
        "🔐 Your gateway to secure payments & verified proofs\n\n"
        "👤 OWNER: @IIG_DARK_YT\n"
        "📱 UPI: 9193896075-3@ibl\n"
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
        [InlineKeyboardButton("📱 Paytm", callback_data="generate_qr")],
        [InlineKeyboardButton("🟢 Google Pay", callback_data="generate_qr")],
        [InlineKeyboardButton("🔵 PhonePe", callback_data="generate_qr")],
        [InlineKeyboardButton("📋 Copy UPI ID", callback_data="copy_upi_id")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(payment_message, reply_markup=reply_markup)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/start"
    
    welcome_message = (
        f"✨ Welcome, {user.first_name}, to Guy's Bot!\n\n"
        "🔐 Your gateway to secure payments & verified proofs\n\n"
        "👤 OWNER: @IIG_DARK_YT\n"
        "📱 UPI: 9193896075-3@ibl\n"
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

async def generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send UPI QR code"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_info = get_user_data(user.id)
    user_info["payments_requested"] = user_info.get("payments_requested", 0) + 1
    
    logger.info(f"User {user.first_name} requested QR code")
    
    try:
        # Generate QR code
        if await generate_qr_code(UPI_ID, "upi.png"):
            # Send photo with caption
            with open("upi.png", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=f"📱 Scan & Pay: {UPI_ID}\n\n✅ Works for all payments: Paytm / GPay / PhonePe"
                )
            
            # Delete the image file
            os.remove("upi.png")
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
    user_info = get_user_data(user.id)
    user_info["payments_requested"] = user_info.get("payments_requested", 0) + 1
    
    # Return to payments menu
    await payments_menu(update, context)

# --- Game Menu ---

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
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(games_message, reply_markup=reply_markup)

async def game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start Head or Tails game"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/game_coin"
    user_info["games_played"] = user_info.get("games_played", 0) + 1
    
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
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/game_rps"
    user_info["games_played"] = user_info.get("games_played", 0) + 1
    
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
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/game_ttt"
    user_info["games_played"] = user_info.get("games_played", 0) + 1
    
    # Initialize game
    user_info["game_state"]["tic_tac_toe"] = {
        "board": initialize_tic_tac_toe_board(),
        "current_player": "X",
        "game_over": False
    }
    
    game = user_info["game_state"]["tic_tac_toe"]
    message = display_tic_tac_toe_board(game["board"])
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
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/game_hangman"
    user_info["games_played"] = user_info.get("games_played", 0) + 1
    
    message = hangman_game(user.id)
    
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
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/game_dice"
    user_info["games_played"] = user_info.get("games_played", 0) + 1
    
    message = dice_roll()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Roll Again", callback_data="game_dice")],
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
    user_info = get_user_data(user.id)
    
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
    user_info = get_user_data(user.id)
    
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
    user_info = get_user_data(user.id)
    
    # Extract position from callback data
    try:
        position = int(query.data.split("_")[1])
        message = make_tic_tac_toe_move(user.id, position)
        
        # Check if game is over
        game = user_info["game_state"].get("tic_tac_toe", {})
        if game.get("game_over", False):
            keyboard = [
                [InlineKeyboardButton("🔄 New Game", callback_data="game_ttt")],
                [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
            ]
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
    user_info = get_user_data(user.id)
    
    # Extract letter from callback data
    letter = query.data.split("_")[1]
    
    message = hangman_game(user.id, letter)
    
    # Check if game is over
    if "Congratulations" in message or "Game Over" in message:
        keyboard = [
            [InlineKeyboardButton("🔄 New Game", callback_data="game_hangman")],
            [InlineKeyboardButton("⬅️ Back", callback_data="games_menu")]
        ]
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

async def daily_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a motivational quote"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_info = get_user_data(user.id)
    user_info["quotes_read"] = user_info.get("quotes_read", 0) + 1
    
    # Fetch quote from API or use default
    quote = await fetch_quote_from_api()
    
    quote_message = f"💡 Daily Motivation\n\n{quote}"
    
    keyboard = [
        [InlineKeyboardButton("⏭ Next Quote", callback_data="daily_quote")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(quote_message, reply_markup=reply_markup)

async def daily_joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a joke"""
    query = update.callback_query
    await query.answer()
    
    # Fetch joke from API or use default
    joke = await fetch_joke_from_api()
    
    joke_message = f"😂 Daily Joke\n\n{joke}"
    
    keyboard = [
        [InlineKeyboardButton("😂 Next Joke", callback_data="daily_joke")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(joke_message, reply_markup=reply_markup)

async def daily_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a fun fact"""
    query = update.callback_query
    await query.answer()
    
    # Fetch fact from API or use default
    fact = await fetch_fact_from_api()
    
    fact_message = f"🧠 Did You Know?\n\n{fact}"
    
    keyboard = [
        [InlineKeyboardButton("🧠 Next Fact", callback_data="daily_fact")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(fact_message, reply_markup=reply_markup)

# --- Original Command Handlers ---

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send UPI QR code (original command)"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/qr"
    user_info["payments_requested"] = user_info.get("payments_requested", 0) + 1
    
    logger.info(f"User {user.first_name} requested QR code")
    
    try:
        # Generate QR code
        if await generate_qr_code(UPI_ID, "upi.png"):
            # Send photo with caption
            with open("upi.png", "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📱 Scan & Pay: {UPI_ID}\n\n✅ Works for all payments: Paytm / GPay / PhonePe"
                )
            
            # Delete the image file
            os.remove("upi.png")
        else:
            await update.message.reply_text("❌ Sorry, unable to generate QR code at the moment!")
            
    except Exception as e:
        logger.error(f"Error generating/sending QR code: {e}")
        await update.message.reply_text("❌ Sorry, unable to generate QR code at the moment!")

async def proofs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send proof channel link when /proofs command is issued"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/proofs"
    
    logger.info(f"User {user.first_name} requested proofs")
    
    try:
        message = f"📸 Latest Verified Proofs\n\n📂 See all proofs here: {PROOFS_CHANNEL}"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error sending proofs link: {e}")
        await update.message.reply_text("❌ Sorry, unable to provide proofs link at the moment!")

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send channel link when /channel command is issued"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/channel"
    
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
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/games"
    
    await games_menu_callback(update, context)

async def games_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show games menu for /games command"""
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
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(games_message, reply_markup=reply_markup)

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quote command"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/quote"
    user_info["quotes_read"] = user_info.get("quotes_read", 0) + 1
    
    # Fetch quote from API or use default
    quote = await fetch_quote_from_api()
    
    quote_message = f"💡 Daily Motivation\n\n{quote}"
    
    await update.message.reply_text(quote_message)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/search"
    
    search_message = (
        "🔍 Search Content\n\n"
        "Enter a keyword to search for proofs, channels, or content:\n\n"
        "Example: 'payment', 'verification', 'tutorial'"
    )
    
    await update.message.reply_text(search_message)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    
    stats_message = (
        f"📊 {user.first_name}'s Stats\n\n"
        f"🎮 Games Played: {user_info.get('games_played', 0)}\n"
        f"💡 Quotes Read: {user_info.get('quotes_read', 0)}\n"
        f"💳 Payments Requested: {user_info.get('payments_requested', 0)}\n"
        f"🕒 Joined: {user_info.get('join_date', 'Unknown')}"
    )
    
    await update.message.reply_text(stats_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages for search functionality and easter eggs"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    text = update.message.text.lower()
    
    # Anti-spam check
    if check_spam(user.id):
        if user_info["spam_count"] > 3:
            await update.message.reply_text("🚫 You're sending messages too quickly! Please slow down.")
            return
        else:
            await update.message.reply_text("⚠️ Please slow down with your messages.")
    
    # Check for payment-related keywords
    if any(keyword in text for keyword in ["upi", "payment", "paytm", "gpay", "phonepay", "google pay"]):
        user_info["payments_requested"] = user_info.get("payments_requested", 0) + 1
        response = (
            f"💳 Payment Information\n\n"
            f"📱 UPI ID: {UPI_ID}\n"
            f"✅ Works for all payments: Paytm / GPay / PhonePe\n\n"
            f"Use /qr to generate a payment QR code"
        )
        await update.message.reply_text(response)
        return
    
    # Check for quote-related keywords
    if "quote" in text or "motivat" in text:
        user_info["quotes_read"] = user_info.get("quotes_read", 0) + 1
        quote = await fetch_quote_from_api()
        await update.message.reply_text(f"💡 {quote}")
        return
    
    # Check for joke-related keywords
    if "joke" in text or "funny" in text:
        joke = await fetch_joke_from_api()
        await update.message.reply_text(f"😂 {joke}")
        return
    
    # Check for fact-related keywords
    if "fact" in text or "know" in text:
        fact = await fetch_fact_from_api()
        await update.message.reply_text(f"🧠 {fact}")
        return
    
    # Check for weather-related keywords
    if "weather" in text or "temperature" in text:
        city = "London"  # Default city
        # Try to extract city name from message
        words = text.split()
        if len(words) > 1:
            city = words[-1].capitalize()
        weather = await fetch_weather(city)
        await update.message.reply_text(weather)
        return
    
    # Check for game-related keywords
    if "game" in text:
        await games_menu_callback(update, context)
        return
    
    # Check if user was in search mode
    if user_info["last_command"] == "/search":
        # Simple keyword matching
        if "payment" in text or "pay" in text or "upi" in text:
            response = (
                "💳 Payment Related Content:\n\n"
                "📱 UPI QR Code: /qr\n"
                f"📋 UPI ID: {UPI_ID}\n"
                f"📸 Payment Proofs: {PROOFS_CHANNEL}"
            )
        elif "proof" in text or "verify" in text:
            response = (
                "📸 Verification Content:\n\n"
                f"📂 All Proofs: {PROOFS_CHANNEL}\n"
                "📊 Channel Stats: 1,250+ Members\n"
                "✅ 99.8% Success Rate"
            )
        elif "channel" in text or "group" in text:
            response = (
                "📺 Community Content:\n\n"
                f"📺 Main Channel: {MAIN_CHANNEL_LINK}\n"
                f"👥 Community Group: {GROUP_LINK}\n"
                f"👤 Owner: {OWNER_LINK}"
            )
        else:
            # Use AI to generate response
            ai_response = await fetch_ai_response(text)
            response = f"🤖 AI Response:\n\n{ai_response}"
        
        keyboard = [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup)
    else:
        # Easter egg for hidden commands
        if text in ["sigma", "boss", "dark"]:
            await update.message.reply_text("🎯 Sigma detected! You've found a hidden command. Respect++")
        elif text in ["cheat", "hack", "bypass"]:
            await update.message.reply_text("🚫 No cheating allowed, be a good user!")
        elif text in ["love", "heart", "<3"]:
            await update.message.reply_text("❤️ Love is in the air! Thanks for using our bot!")
        elif text.isdigit():
            # If user sends a number, assume it's for number guessing game
            if user_info["last_command"] == "/game_ttt":
                await update.message.reply_text("⭕ Please use the game interface to play!\nType /games to start a new game.")
            else:
                # General number input
                await update.message.reply_text(f"🔢 You entered: {text}\n\nNot sure what you want to do with this number. Try /games or /help for options!")
        else:
            # Use AI to generate response for unknown keywords
            ai_response = await fetch_ai_response(text)
            await update.message.reply_text(f"🤖 {ai_response}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send enhanced help message when /help command is issued"""
    user = update.effective_user
    user_info = get_user_data(user.id)
    user_info["last_command"] = "/help"
    
    logger.info(f"User {user.first_name} requested help")
    
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
        "🔍 /search - Search content by keyword\n"
        "📊 /stats - View your statistics\n"
        "🆘 /help - Show this help message\n\n"
        "All features are accessible through the interactive menu too!"
    )
    
    try:
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Error sending help message: {e}")
        await update.message.reply_text("❌ Sorry, unable to display help at the moment!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries"""
    query = update.callback_query
    user = query.from_user
    user_info = get_user_data(user.id)
    user_info["last_interaction"] = datetime.now()
    
    # Route to appropriate handler based on callback data
    if query.data == "payments_menu":
        await payments_menu(update, context)
    elif query.data == "main_menu":
        await main_menu(update, context)
    elif query.data == "generate_qr":
        await generate_qr(update, context)
    elif query.data == "copy_upi_id":
        await copy_upi_id(update, context)
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
    elif query.data == "daily_joke":
        await daily_joke(update, context)
    elif query.data == "daily_fact":
        await daily_fact(update, context)
    else:
        await query.answer("Feature coming soon!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

def main() -> None:
    """Start the bot"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("qr", qr_command))
    application.add_handler(CommandHandler("proofs", proofs_command))
    application.add_handler(CommandHandler("channel", channel_command))
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Run the bot until the user presses Ctrl-C
    logger.info("EXTREME SIGMA Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()