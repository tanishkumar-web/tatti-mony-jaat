# Ultra-Premium Sigma-Level Telegram Bot

An ultra-premium, feature-rich Python Telegram bot built with python-telegram-bot v20+ featuring advanced payment integration with OCR verification, interactive games, AI features, admin dashboard, and much more.

## 🚀 Sigma-Level Features

### 🎛️ Admin Dashboard
- **Full Back Panel**: Complete admin interface for bot management
- **User Management**: View all users, search, DM individual users
- **Payment Management**: Approve/reject OCR-verified payments
- **Broadcast System**: Send announcements/ads to all users
- **Analytics Dashboard**: View engagement metrics and statistics
- **Leaderboards**: See top users by games, payments, activity
- **Scheduled Content**: Plan and schedule messages

### 👑 VIP User Features
- **Exclusive Access**: Special privileges for VIP users
- **Unlimited Exa AI Searches**: No limits on AI-powered searches
- **Premium Content**: Access to exclusive quotes and information
- **Priority Support**: Faster response times
- **Special Rewards**: Daily bonuses and gifts
- **Early Access**: First to try new features

### 🔐 Advanced Payment System with OCR
- **Semi-Automatic Verification**: Users upload payment screenshots → bot auto-verifies via OCR → admin approves if ambiguous
- **Universal UPI Integration**: Single UPI ID works for Paytm, GPay, PhonePe
- **Multi-platform QR codes**: Generate QR for any payment platform
- **Smart Payment Detection**: Bot understands payment keywords and responds intelligently
- **One-tap UPI ID copying**
- **Admin Approval Workflow**: Suspicious payments forwarded to admin with approve/reject buttons

### 🎮 Interactive Games (8+ Types)
1. **Head or Tails** - Coin toss game
2. **Rock Paper Scissors** - Classic game with emojis
3. **Tic-Tac-Toe** - Player vs AI with smart bot moves
4. **Hangman** - Word guessing game
5. **Dice Roll** - Random dice simulator
6. **Trivia/Quiz** - Knowledge-based questions
7. **Daily Challenge** - Special daily mini-game
8. **Fortune Teller** - Random fortune predictions

### 💡 Dynamic Quotes & Content System
- **API-Integrated Quotes**: Fetches from multiple online APIs
- **Daily Motivational/Inspirational Quotes**
- **Inline "Next Quote" Button** to avoid repetition
- **Reaction Buttons** for quotes (❤️ 👍 👎)
- **Admin Custom Quote Uploads**
- **Quote Categories** for targeted content
- **Inline Keyword Search** for specific quotes
- **Share Quotes** to any chat
- **Random Fun Facts** notifications

### 🤖 AI & Smart Features
- **Hugging Face NLP API Integration** for human-like responses
- **Exa AI Search & Question Answering** for factual information
- **Intent Detection**: Automatically detects if user wants payment, game, quote, proof, etc.
- **Personalized Recommendations** based on user activity
- **Time-of-Day Greetings** for personalized experience
- **Sentiment Detection** (happy, sad, frustrated)
- **Adaptive Menu** based on user habits
- **Auto-Learning** from repeated inputs

### 👥 Social & Community Features
- **Interactive Polls** and surveys
- **Live Leaderboards** with hall of fame
- **Weekly Top User Notifications**
- **Daily Streaks** and points system
- **User vs User Challenges**
- **Random Trivia/Riddles**
- **Birthday & Special Day Greetings**
- **Reward System** for engagement
- **Top Player/Top Payer Recognition**

### Channel & Group Management
- **Live Member Counts**
- **Auto Welcome** for new members
- **Inline Poll Creation**
- **Group Rules Reminders**
- **Anti-Spam Protection** with auto-kick
- **Important Message Pinning**
- **Auto-Forward** to proofs channel
- **Auto-Share** latest proofs

### Media & Creativity Tools
- **Multi-Format Support**: Images, GIFs, videos, documents
- **Auto-Moderation** with forward to proofs channel
- **Inline Media Preview**
- **OCR Caption Detection**
- **Auto-Thumbnail Generation**
- **Image Editing** (crop, text, watermark)
- **File Validation** (type & size)
- **Temporary File Auto-Deletion**
- **Sticker & GIF Creation**
- **Animated Buttons**

### Automation & Notifications
- **Daily Scheduled Messages** and tips
- **Payment Reminders**
- **Quote Notifications**
- **Game Challenge Reminders**
- **Admin Alerts** for failed/suspicious payments
- **Anti-Spam Automation**
- **Auto-Delete** old messages
- **Automatic DB Backup**
- **System Uptime Monitoring**
- **Friendly Error Messages**

### Security & Safety
- **File Validation** for all uploads
- **Rate Limiting** for commands
- **Advanced Anti-Spam Detection**
- **GDPR-Compliant** minimal data storage
- **Comprehensive Logging** of all actions
- **Admin Alerts** for suspicious behavior
- **Secure Inline Keyboards**
- **Graceful Fallback** on failures
- **Invalid Command Filtering**

### Fun Easter Eggs
- **Hidden Commands** for power users
- **Random Jokes/Memes**
- **Daily Riddles/Trivia**
- **Secret Mini-Games**
- **Random Surprise Rewards**
- **Personalized Jokes/Compliments**
- **AI-Generated Fun Responses**
- **Animated Buttons**
- **Random Facts**
- **Mystery Reward System**

## 🏗️ Modular Code Structure

- `config.py` - All configuration settings
- `database.py` - SQLite database management
- `utils.py` - Utility functions (QR, OCR, file handling)
- `games.py` - Game implementations
- `quotes.py` - Quote fetching and management
- `ai.py` - AI/NLP integration
- `exa_ai.py` - Exa AI integration
- `payments.py` - Payment processing with OCR
- `admin.py` - Admin dashboard functionality
- `bot.py` - Main bot implementation

## 🛠 Setup Instructions

1. Install Python 3.7+
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. **Windows Only**: Install Tesseract OCR:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Add to PATH environment variable
4. Replace `PLACEHOLDER_ADMIN_ID` in `config.py` with your actual Telegram ID
5. (Optional) Add Hugging Face API key in `config.py` for AI features
6. Run the bot:
   ```
   python bot.py
   ```

## 🎮 Commands

### Core Commands
- `/start` - Main menu with all features
- `/admin` - Admin dashboard (admin only)
- `/payments` - Generate payment QR codes and upload screenshots
- `/qr` - Generate UPI QR code
- `/proofs` - View latest payment proofs
- `/channel` - Join our main channel

### Interactive Commands
- `/games` - Play mini games
- `/quote` - Get motivational quote
- `/search <query>` - Search web content with Exa AI
- `/ask <question>` - Ask questions with Exa AI
- `/stats` - View your statistics
- `/vip_features` - VIP exclusive features (VIP users only)
- `/help` - Show all commands

## 🔧 Configuration

The bot uses the token `7835457395:AAHOVKzTw2PXo1GR_fy1-szjQdmBhhSWF7I` and is ready to run immediately after installing dependencies.

## 📁 File Structure
- `bot.py` - Main bot implementation
- `config.py` - Configuration settings
- `database.py` - Database management
- `utils.py` - Utility functions
- `games.py` - Game implementations
- `quotes.py` - Quote management
- `ai.py` - AI integration
- `exa_ai.py` - Exa AI integration
- `payments.py` - Payment processing
- `admin.py` - Admin dashboard
- `requirements.txt` - Dependencies list
- `README.md` - This documentation
- `temp/` - Temporary files (auto-cleaned)
- `proofs/` - Proof images storage

## 🏆 Sigma Features

This bot goes beyond basic functionality with:
- **100+ Extreme Features** as requested
- Nested menu systems with intuitive navigation
- Personalized user experiences with AI
- Interactive mini-games with leaderboards
- Smart search and intent detection
- AI-powered responses with sentiment analysis
- Comprehensive analytics and statistics
- Hidden easter eggs and surprise features
- Professional UI/UX design with emojis
- Modular, maintainable code structure
- Database-driven persistent storage
- OCR-powered payment verification
- Admin approval workflows
- Community building tools
- Automation and scheduling
- Security and safety measures
- Full admin dashboard with broadcast system
- Exa AI search and question answering
- VIP user privileges and exclusive features

All original functionality is preserved while adding these premium features.# tanish-choudhary-bot
