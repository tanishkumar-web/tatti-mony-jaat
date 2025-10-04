import sqlite3
import json
import os
from datetime import datetime
from config import DB_FILE
from functools import lru_cache

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            games_played INTEGER DEFAULT 0,
            quotes_read INTEGER DEFAULT 0,
            payments_requested INTEGER DEFAULT 0,
            successful_payments INTEGER DEFAULT 0,
            spam_count INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    
    # Check if is_banned column exists, add it if not
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Create payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            upi_id TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_type TEXT,
            result TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create quotes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT,
            author TEXT,
            category TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_quotes table (to track which quotes users have seen)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quotes (
            user_id INTEGER,
            quote_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, quote_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (quote_id) REFERENCES quotes (id)
        )
    ''')
    
    # Insert some default quotes if table is empty
    cursor.execute('SELECT COUNT(*) FROM quotes')
    if cursor.fetchone()[0] == 0:
        default_quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs", "motivation"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs", "innovation"),
            ("Your time is limited, don't waste it living someone else's life.", "Steve Jobs", "life"),
            ("Stay hungry, stay foolish.", "Steve Jobs", "philosophy"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt", "dreams")
        ]
        cursor.executemany('INSERT INTO quotes (quote, author, category) VALUES (?, ?, ?)', default_quotes)
    
    conn.commit()
    conn.close()

# Add a cache for user ban status to improve performance
@lru_cache(maxsize=1000)
def _is_user_banned_cached(user_id):
    """Cached version of is_user_banned"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT is_banned FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] == 1 if result else False
    except sqlite3.OperationalError:
        # Handle case where column doesn't exist
        conn.close()
        return False

def get_user(user_id):
    """Get user data from database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        return None
    
    # Convert to dictionary
    columns = [column[0] for column in cursor.description]
    user_dict = dict(zip(columns, user))
    
    conn.close()
    return user_dict

def create_user(user_id, username, first_name, last_name):
    """Create a new user in the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()

def update_user_interaction(user_id):
    """Update user's last interaction timestamp"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET last_interaction = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def update_user_stats(user_id, field, increment=1):
    """Update user statistics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(f'''
        UPDATE users SET {field} = {field} + ? WHERE user_id = ?
    ''', (increment, user_id))
    
    conn.commit()
    conn.close()

def log_payment(user_id, amount=None, upi_id=None, transaction_id=None, status='pending'):
    """Log a payment attempt"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO payments (user_id, amount, upi_id, transaction_id, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, amount, upi_id, transaction_id, status))
    
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return payment_id

def update_payment_status(payment_id, status):
    """Update payment status"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE payments SET status = ? WHERE id = ?
    ''', (status, payment_id))
    
    conn.commit()
    conn.close()

def log_game(user_id, game_type, result):
    """Log a game result"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO games (user_id, game_type, result)
        VALUES (?, ?, ?)
    ''', (user_id, game_type, result))
    
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return game_id

def get_user_quotes(user_id):
    """Get quotes that a user has already seen"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT quote_id FROM user_quotes WHERE user_id = ?
    ''', (user_id,))
    
    quotes = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return quotes

def add_user_quote(user_id, quote_id):
    """Add a quote to user's seen list"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO user_quotes (user_id, quote_id)
        VALUES (?, ?)
    ''', (user_id, quote_id))
    
    conn.commit()
    conn.close()

def get_random_quote(exclude_ids=None):
    """Get a random quote, optionally excluding certain IDs"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if exclude_ids:
        placeholders = ','.join('?' * len(exclude_ids))
        cursor.execute(f'''
            SELECT id, quote, author, category FROM quotes
            WHERE id NOT IN ({placeholders})
            ORDER BY RANDOM() LIMIT 1
        ''', exclude_ids)
    else:
        cursor.execute('''
            SELECT id, quote, author, category FROM quotes
            ORDER BY RANDOM() LIMIT 1
        ''')
    
    quote = cursor.fetchone()
    conn.close()
    
    return quote

def add_quote(quote, author, category):
    """Add a new quote to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO quotes (quote, author, category)
        VALUES (?, ?, ?)
    ''', (quote, author, category))
    
    quote_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return quote_id

def get_leaderboard(limit=10):
    """Get top users by games played"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, first_name, games_played
        FROM users
        WHERE games_played > 0
        ORDER BY games_played DESC
        LIMIT ?
    ''', (limit,))
    
    leaderboard = cursor.fetchall()
    conn.close()
    
    return leaderboard

def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT games_played, quotes_read, payments_requested, successful_payments
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    
    stats = cursor.fetchone()
    conn.close()
    
    if stats:
        return {
            'games_played': stats[0],
            'quotes_read': stats[1],
            'payments_requested': stats[2],
            'successful_payments': stats[3]
        }
    
    return None

def get_user_messages(user_id, limit=10):
    """Get recent messages from a user"""
    # This would require a messages table to be created
    # For now, we'll return an empty list
    return []

def get_all_users(limit=100):
    """Get all users"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, join_date, last_interaction, 
               games_played, quotes_read, payments_requested, successful_payments
        FROM users
        ORDER BY last_interaction DESC
        LIMIT ?
    ''', (limit,))
    
    users = cursor.fetchall()
    conn.close()
    
    return users

def get_pending_payments(limit=50):
    """Get pending payments"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.user_id, u.first_name, u.username, p.amount, p.upi_id, p.transaction_id, p.timestamp
        FROM payments p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.status = 'pending'
        ORDER BY p.timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    payments = cursor.fetchall()
    conn.close()
    
    return payments

def get_payment_stats():
    """Get payment statistics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM payments")
    total_payments = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'verified'")
    verified_payments = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'rejected'")
    rejected_payments = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
    pending_payments = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total_payments,
        'verified': verified_payments,
        'rejected': rejected_payments,
        'pending': pending_payments
    }

def get_engagement_metrics():
    """Get engagement metrics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users active in last 24 hours
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_interaction > datetime('now', '-1 day')
    ''')
    active_24h = cursor.fetchone()[0]
    
    # Users active in last 7 days
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_interaction > datetime('now', '-7 days')
    ''')
    active_7d = cursor.fetchone()[0]
    
    # Users active in last 30 days
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_interaction > datetime('now', '-30 days')
    ''')
    active_30d = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'active_24h': active_24h,
        'active_7d': active_7d,
        'active_30d': active_30d
    }

def get_top_users_by_stat(stat, limit=10):
    """Get top users by a specific statistic"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    valid_stats = ['games_played', 'quotes_read', 'payments_requested', 'successful_payments']
    if stat not in valid_stats:
        stat = 'games_played'
    
    cursor.execute(f'''
        SELECT user_id, first_name, {stat}
        FROM users
        WHERE {stat} > 0
        ORDER BY {stat} DESC
        LIMIT ?
    ''', (limit,))
    
    users = cursor.fetchall()
    conn.close()
    
    return users

def ban_user(user_id):
    """Ban a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET is_banned = 1 WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    
    # Clear cache for this user
    _is_user_banned_cached.cache_clear()

def unban_user(user_id):
    """Unban a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET is_banned = 0 WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    
    # Clear cache for this user
    _is_user_banned_cached.cache_clear()

def is_user_banned(user_id):
    """Check if a user is banned (cached version)"""
    return _is_user_banned_cached(user_id)