import sqlite3
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DB_FILE, ADMIN_IDS
from database import get_user_stats, get_all_users, get_pending_payments, get_payment_stats, get_engagement_metrics, get_top_users_by_stat

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Admin dashboard for managing the bot"""
    
    def __init__(self):
        self.pending_broadcasts = {}  # chat_id -> message
        
    async def is_admin(self, user_id):
        """Check if user is admin"""
        return str(user_id) in ADMIN_IDS
    
    async def show_dashboard(self, update, context):
        """Show admin dashboard"""
        user = update.effective_user
        if not await self.is_admin(user.id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
        
        # Get quick stats
        users = get_all_users(1)
        total_users = len(get_all_users(1000)) if users else 0
        
        payment_stats = get_payment_stats()
        engagement = get_engagement_metrics()
        
        dashboard_message = (
            "🎛️ Admin Dashboard\n\n"
            f"📊 Quick Stats:\n"
            f"👥 Total Users: {total_users}\n"
            f"💳 Total Payments: {payment_stats['total']}\n"
            f"✅ Verified: {payment_stats['verified']}\n"
            f"❌ Rejected: {payment_stats['rejected']}\n"
            f"⏳ Pending: {payment_stats['pending']}\n"
            f"⚡ Active (24h): {engagement['active_24h']}\n\n"
            "Select an option:"
        )
        
        keyboard = [
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("💳 Payment Management", callback_data="admin_payments")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="admin_leaderboard")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(dashboard_message, reply_markup=reply_markup)
    
    async def show_user_management(self, update, context):
        """Show user management options"""
        query = update.callback_query
        await query.answer()
        
        message = "👥 User Management\n\nSelect an option:"
        
        keyboard = [
            [InlineKeyboardButton("📋 List All Users", callback_data="admin_list_users")],
            [InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user")],
            [InlineKeyboardButton("💬 View User Messages", callback_data="admin_user_messages")],
            [InlineKeyboardButton("📤 DM User", callback_data="admin_dm_user")],
            [InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban_unban")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_payment_management(self, update, context):
        """Show payment management options"""
        query = update.callback_query
        await query.answer()
        
        payment_stats = get_payment_stats()
        
        message = (
            "💳 Payment Management\n\n"
            f"📊 Statistics:\n"
            f"Total: {payment_stats['total']}\n"
            f"Verified: {payment_stats['verified']}\n"
            f"Rejected: {payment_stats['rejected']}\n"
            f"Pending: {payment_stats['pending']}\n\n"
            "Select an option:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 View Pending Payments", callback_data="admin_pending_payments")],
            [InlineKeyboardButton("✅ View Verified Payments", callback_data="admin_verified_payments")],
            [InlineKeyboardButton("❌ View Rejected Payments", callback_data="admin_rejected_payments")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_broadcast_menu(self, update, context):
        """Show broadcast options"""
        query = update.callback_query
        await query.answer()
        
        message = "📢 Broadcast Message\n\nSelect an option:"
        
        keyboard = [
            [InlineKeyboardButton("📝 Create Broadcast", callback_data="admin_create_broadcast")],
            [InlineKeyboardButton("🕒 Schedule Broadcast", callback_data="admin_schedule_broadcast")],
            [InlineKeyboardButton("📋 View Scheduled", callback_data="admin_scheduled_broadcasts")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_analytics(self, update, context):
        """Show analytics dashboard"""
        query = update.callback_query
        await query.answer()
        
        # Get analytics data
        engagement = get_engagement_metrics()
        payment_stats = get_payment_stats()
        
        message = (
            "📊 Bot Analytics\n\n"
            f"👥 User Engagement:\n"
            f"Active (24h): {engagement['active_24h']}\n"
            f"Active (7d): {engagement['active_7d']}\n"
            f"Active (30d): {engagement['active_30d']}\n\n"
            f"💳 Payment Statistics:\n"
            f"Total: {payment_stats['total']}\n"
            f"Verified: {payment_stats['verified']}\n"
            f"Rejected: {payment_stats['rejected']}\n"
            f"Pending: {payment_stats['pending']}\n\n"
            "Select an option:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📈 Detailed Analytics", callback_data="admin_detailed_analytics")],
            [InlineKeyboardButton("🕒 Engagement Metrics", callback_data="admin_engagement")],
            [InlineKeyboardButton("🏆 Top Users", callback_data="admin_top_users")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_leaderboard(self, update, context):
        """Show comprehensive leaderboard"""
        query = update.callback_query
        await query.answer()
        
        message = "🏆 Leaderboard\n\nSelect category:"
        
        keyboard = [
            [InlineKeyboardButton("🎮 Games Played", callback_data="admin_lb_games")],
            [InlineKeyboardButton("💰 Payments Made", callback_data="admin_lb_payments")],
            [InlineKeyboardButton("💡 Quotes Read", callback_data="admin_lb_quotes")],
            [InlineKeyboardButton("⭐ Most Active", callback_data="admin_lb_active")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def list_all_users(self, update, context):
        """List all users"""
        query = update.callback_query
        await query.answer()
        
        users = get_all_users(10)
        
        if not users:
            message = "👥 No users found."
        else:
            message = "👥 All Users (Last 10):\n\n"
            for user in users:
                user_id, username, first_name, last_name, join_date, last_interaction, games_played, quotes_read, payments_requested, successful_payments = user
                username_str = f"@{username}" if username else "No username"
                
                # Check if user is banned
                from database import is_user_banned
                is_banned = is_user_banned(user_id)
                ban_status = "🚫 Banned" if is_banned else "✅ Active"
                
                message += f"👤 {first_name} ({username_str})\n"
                message += f"   ID: {user_id}\n"
                message += f"   Status: {ban_status}\n"
                message += f"   Games: {games_played} | Payments: {payments_requested}\n"
                message += f"   Quotes: {quotes_read} | Successful Payments: {successful_payments}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_list_users")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_pending_payments(self, update, context):
        """Show pending payments"""
        query = update.callback_query
        await query.answer()
        
        payments = get_pending_payments(10)
        
        if not payments:
            message = "💳 No pending payments."
        else:
            message = "💳 Pending Payments (Last 10):\n\n"
            for payment in payments:
                payment_id, user_id, first_name, username, amount, upi_id, txn_id, timestamp = payment
                username_str = f"@{username}" if username else "No username"
                message += f"🔢 ID: {payment_id}\n"
                message += f"👤 User: {first_name} ({username_str})\n"
                message += f"   ID: {user_id}\n"
                message += f"💰 Amount: {amount or 'Unknown'}\n"
                message += f"📱 UPI: {upi_id or 'Unknown'}\n"
                message += f"🧾 Txn: {txn_id or 'Unknown'}\n"
                message += f"🕒 Time: {timestamp}\n"
                message += f"[✅ Approve](callback_data='approve_payment_{user_id}_{payment_id}') | [❌ Reject](callback_data='reject_payment_{user_id}_{payment_id}')\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_pending_payments")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_payments")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def create_broadcast_prompt(self, update, context):
        """Prompt admin to create a broadcast"""
        query = update.callback_query
        await query.answer()
        
        message = "📢 Create Broadcast\n\nPlease send the message you want to broadcast to all users."
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Set state to wait for broadcast message
        context.user_data['awaiting_broadcast'] = True
    
    async def send_broadcast(self, update, context):
        """Send broadcast to all users"""
        if not context.user_data.get('awaiting_broadcast'):
            return
        
        # Get broadcast message
        broadcast_message = update.message.text
        
        # Get all users
        users = get_all_users(1000)
        
        # Send message to all users
        success_count = 0
        for user in users:
            user_id = user[0]  # First field is user_id
            try:
                await context.bot.send_message(chat_id=user_id, text=f"📢 Broadcast:\n\n{broadcast_message}")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user_id}: {e}")
        
        # Confirm to admin
        await update.message.reply_text(
            f"📢 Broadcast sent successfully!\n"
            f"✅ Delivered to {success_count} users\n"
            f"❌ Failed to deliver to {len(users) - success_count} users"
        )
        
        # Reset state
        context.user_data['awaiting_broadcast'] = False
    
    async def dm_user_prompt(self, update, context):
        """Prompt admin to DM a user"""
        query = update.callback_query
        await query.answer()
        
        message = "📤 Direct Message\n\nPlease enter the user ID and message in this format:\n\nUSER_ID:MESSAGE"
        
        keyboard = [
            [InlineKeyboardButton("📋 List Users", callback_data="admin_list_users")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
            [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Set state to wait for DM
        context.user_data['awaiting_dm'] = True
    
    async def send_dm(self, update, context):
        """Send direct message to a user"""
        if not context.user_data.get('awaiting_dm'):
            return
        
        # Parse the message
        text = update.message.text
        if ':' not in text:
            await update.message.reply_text("❌ Invalid format. Please use: USER_ID:MESSAGE")
            return
        
        user_id, message = text.split(':', 1)
        user_id = user_id.strip()
        message = message.strip()
        
        try:
            user_id = int(user_id)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please enter a valid number.")
            return
        
        # Send DM
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📩 Message from Admin:\n\n{message}"
            )
            await update.message.reply_text("✅ Message sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
            await update.message.reply_text("❌ Failed to send message. User may have blocked the bot.")
        
        # Reset state
        context.user_data['awaiting_dm'] = False

    async def handle_ban_unban(self, update, context):
        """Handle ban/unban command from admin"""
        if not context.user_data.get('awaiting_ban_unban'):
            return
        
        # Parse the command
        text = update.message.text
        if ':' not in text:
            await update.message.reply_text("❌ Invalid format. Please use: USER_ID:BAN or USER_ID:UNBAN")
            return
        
        user_id, action = text.split(':', 1)
        user_id = user_id.strip()
        action = action.strip().upper()
        
        try:
            user_id = int(user_id)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please enter a valid number.")
            return
        
        # Perform ban/unban action
        try:
            if action == "BAN":
                from database import ban_user
                ban_user(user_id)
                await update.message.reply_text(f"✅ User {user_id} has been banned!")
                
                # Notify the banned user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🚫 You have been banned from using this bot."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify banned user {user_id}: {e}")
                    
            elif action == "UNBAN":
                from database import unban_user
                unban_user(user_id)
                await update.message.reply_text(f"✅ User {user_id} has been unbanned!")
                
                # Notify the unbanned user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="✅ You have been unbanned and can use the bot again."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify unbanned user {user_id}: {e}")
            else:
                await update.message.reply_text("❌ Invalid action. Please use BAN or UNBAN.")
                return
                
        except Exception as e:
            logger.error(f"Failed to {action} user {user_id}: {e}")
            await update.message.reply_text(f"❌ Failed to {action.lower()} user. Please try again.")
        
        # Reset state
        context.user_data['awaiting_ban_unban'] = False

    async def show_top_users(self, update, context, category="games_played"):
        """Show top users by category"""
        query = update.callback_query
        await query.answer()
        
        # Map categories to database fields
        category_map = {
            "admin_lb_games": "games_played",
            "admin_lb_payments": "successful_payments",
            "admin_lb_quotes": "quotes_read",
            "admin_lb_active": "games_played"  # For now, use games as proxy for activity
        }
        
        stat_field = category_map.get(category, "games_played")
        top_users = get_top_users_by_stat(stat_field, 10)
        
        category_names = {
            "admin_lb_games": "Games Played",
            "admin_lb_payments": "Payments Made",
            "admin_lb_quotes": "Quotes Read",
            "admin_lb_active": "Most Active"
        }
        
        category_name = category_names.get(category, "Games Played")
        
        if not top_users:
            message = f"🏆 Top Users by {category_name}\n\nNo users found."
        else:
            message = f"🏆 Top Users by {category_name}\n\n"
            for i, (user_id, first_name, stat_value) in enumerate(top_users, 1):
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                message += f"{medal} {first_name} - {stat_value}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data=category)],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_leaderboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def ban_unban_user_prompt(self, update, context):
        """Prompt admin to ban/unban a user"""
        query = update.callback_query
        await query.answer()
        
        message = "🚫 Ban/Unban User\n\nPlease enter the user ID and action in this format:\n\nUSER_ID:BAN or USER_ID:UNBAN"
        
        keyboard = [
            [InlineKeyboardButton("📋 List Users", callback_data="admin_list_users")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Set state to wait for ban/unban command
        context.user_data['awaiting_ban_unban'] = True
