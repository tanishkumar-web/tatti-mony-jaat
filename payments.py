import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import extract_text_from_image, extract_upi_details, is_valid_image, is_valid_file_type, is_valid_file_size
from config import UPI_ID, ADMIN_IDS
from database import log_payment, update_payment_status

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """Handles payment verification and processing"""
    
    def __init__(self):
        self.pending_payments = {}  # user_id -> payment_data
    
    async def process_payment_screenshot(self, update, context):
        """Process a payment screenshot uploaded by user"""
        user = update.effective_user
        
        # Immediately acknowledge the upload with a more engaging message
        try:
            await update.message.reply_text(
                "📸 Payment screenshot received! ⚡\n\n"
                "🤖 AI is now analyzing your payment...\n"
                "🔎 Extracting UPI ID, amount, and transaction details...\n\n"
                "🕒 Please wait just 30-60 seconds!\n"
                "You'll get a confirmation message shortly! 🚀"
            )
        except Exception as e:
            logger.error(f"Error sending payment acknowledgment: {e}")
        
        # Check if photo exists
        if not update.message.photo:
            try:
                await update.message.reply_text("❌ No photo found in your message. Please upload a payment screenshot.")
            except Exception as e:
                logger.error(f"Error sending no photo message: {e}")
            return
        
        photo = update.message.photo[-1]  # Get the largest photo
        
        # Download the photo
        try:
            file = await photo.get_file()
            file_path = f"temp/payment_{user.id}_{photo.file_id}.jpg"
            await file.download_to_drive(file_path)
        except Exception as e:
            logger.error(f"Error downloading payment screenshot: {e}")
            try:
                await update.message.reply_text("❌ Error downloading your payment screenshot. Please try again.")
            except Exception as e2:
                logger.error(f"Error sending download error message: {e2}")
            return
        
        # Validate file
        if not is_valid_file_type(file_path):
            try:
                await update.message.reply_text("❌ Invalid file type. Please upload an image (JPG, PNG, etc.)")
            except Exception as e:
                logger.error(f"Error sending file type error message: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        if not is_valid_file_size(file_path):
            try:
                await update.message.reply_text("❌ File too large. Please upload an image smaller than 10MB")
            except Exception as e:
                logger.error(f"Error sending file size error message: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # Extract text using OCR with better error handling
        try:
            extracted_text = extract_text_from_image(file_path)
            upi_details = extract_upi_details(extracted_text)
        except Exception as e:
            logger.error(f"Error extracting text from payment screenshot: {e}")
            try:
                await update.message.reply_text("❌ Error processing your payment screenshot. Please try again or contact support.")
            except Exception as e2:
                logger.error(f"Error sending OCR error message: {e2}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # Log payment attempt
        try:
            payment_id = log_payment(
                user_id=user.id,
                amount=upi_details.get('amount'),
                upi_id=upi_details.get('upi_id'),
                transaction_id=upi_details.get('transaction_id'),
                status='processing'
            )
        except Exception as e:
            logger.error(f"Error logging payment: {e}")
            try:
                await update.message.reply_text("❌ Error logging your payment. Please try again.")
            except Exception as e2:
                logger.error(f"Error sending logging error message: {e2}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # Check if we have enough information
        confidence_score = self.calculate_confidence(upi_details)
        
        if confidence_score >= 0.8:
            # High confidence - auto-verify
            try:
                update_payment_status(payment_id, 'verified')
                await update.message.reply_text("✅ Payment verified successfully! 🎉")
                
                # Notify user with enhanced message
                keyboard = [
                    [InlineKeyboardButton("🎮 Play Games", callback_data="games_menu")],
                    [InlineKeyboardButton("💡 Get Quote", callback_data="daily_quote")],
                    [InlineKeyboardButton("📺 Join Channel", url="https://t.me/+IImrx0b9OxswNTk1")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=user.id,
                    text="🎉 Your payment has been verified! Enjoy premium features!\n\n"
                         "🚀 You now have access to:\n"
                         "• All mini-games unlocked\n"
                         "• Premium quotes & content\n"
                         "• Exclusive channel access\n"
                         "• Priority support\n\n"
                         "🎮 Start playing games or get inspired with a quote!",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error in high-confidence payment verification: {e}")
        else:
            # Low confidence - send to admin for approval
            self.pending_payments[user.id] = {
                'payment_id': payment_id,
                'file_path': file_path,
                'upi_details': upi_details,
                'extracted_text': extracted_text
            }
            
            # Notify admin with better formatting
            admin_message = (
                f"🔍 Payment verification needed\n\n"
                f"👤 User: {user.first_name} (@{user.username})\n"
                f"🆔 User ID: {user.id}\n\n"
                f"📄 Extracted Details:\n"
                f"📱 UPI ID: {upi_details.get('upi_id', 'Not found')}\n"
                f"💰 Amount: {upi_details.get('amount', 'Not found')}\n"
                f"🔢 Transaction ID: {upi_details.get('transaction_id', 'Not found')}\n\n"
                f"📊 Confidence Score: {confidence_score:.2f}/1.00"
            )
            
            keyboard = [
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{user.id}_{payment_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{user.id}_{payment_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                # Send to all admins
                for admin_id in ADMIN_IDS:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=open(file_path, 'rb'),
                        caption=admin_message,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Error sending payment to admins: {e}")
                # Fallback: send without photo to all admins
                try:
                    for admin_id in ADMIN_IDS:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=admin_message,
                            reply_markup=reply_markup
                        )
                except Exception as e2:
                    logger.error(f"Error sending payment message to admins: {e2}")

            # Notify user with more engaging message
            try:
                await update.message.reply_text(
                    "⏳ Your payment is being reviewed by our team.\n\n"
                    "🤖 Our AI has analyzed your payment, and a human expert will now verify it.\n"
                    "🔔 You'll receive a confirmation within 1-2 minutes!\n\n"
                    "Thank you for your patience! 🙏"
                )
            except Exception as e:
                logger.error(f"Error sending review message to user: {e}")
        
        # Clean up temp file only if not needed for admin review
        # File will be cleaned up after admin approval/rejection
    
    def calculate_confidence(self, upi_details):
        """Calculate confidence score for payment verification"""
        score = 0.0
        
        # Check UPI ID
        if upi_details.get('upi_id'):
            score += 0.4
        
        # Check amount
        if upi_details.get('amount'):
            score += 0.3
        
        # Check transaction ID
        if upi_details.get('transaction_id'):
            score += 0.3
        
        return min(score, 1.0)  # Ensure score doesn't exceed 1.0
    
    async def handle_admin_approval(self, update, context, user_id, approved=True):
        """Handle admin approval/rejection of payment"""
        query = update.callback_query
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Error answering admin callback: {e}")
        
        # Check if we have this user's pending payment
        if user_id not in self.pending_payments:
            try:
                await query.edit_message_text("❌ Payment request not found or already processed.")
            except Exception as e:
                logger.error(f"Error sending not found message: {e}")
            return
        
        payment_data = self.pending_payments[user_id]
        payment_id = payment_data['payment_id']
        
        if approved:
            # Approve payment
            try:
                update_payment_status(payment_id, 'verified')
            except Exception as e:
                logger.error(f"Error updating payment status to verified: {e}")
                try:
                    await query.edit_message_text("❌ Error updating payment status.")
                except Exception as e2:
                    logger.error(f"Error sending status update error: {e2}")
                return
            
            # Notify user with enhanced message
            keyboard = [
                [InlineKeyboardButton("🎮 Play Games", callback_data="games_menu")],
                [InlineKeyboardButton("💡 Get Quote", callback_data="daily_quote")],
                [InlineKeyboardButton("📺 Join Channel", url="https://t.me/+IImrx0b9OxswNTk1")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 Your payment has been VERIFIED by our team! 🚀\n\n"
                         "🔓 You now have FULL ACCESS to premium features:\n"
                         "• ✅ All games unlocked\n"
                         "• ✅ Premium quotes & content\n"
                         "• ✅ Exclusive channel access\n"
                         "• ✅ Priority support\n\n"
                         "🎮 Start playing games or get inspired with a quote!\n"
                         "Thank you for your support! 💎",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id} about payment approval: {e}")
            
            # Update admin message
            try:
                await query.edit_message_text(
                    f"✅ Payment APPROVED for user {user_id}\n\n"
                    f"🆔 Payment ID: {payment_id}\n"
                    f"⏰ {context._application.loop.time() if context._application else 'N/A'}"
                )
            except Exception as e:
                logger.error(f"Error updating admin approval message: {e}")
        else:
            # Reject payment
            try:
                update_payment_status(payment_id, 'rejected')
            except Exception as e:
                logger.error(f"Error updating payment status to rejected: {e}")
                try:
                    await query.edit_message_text("❌ Error updating payment status.")
                except Exception as e2:
                    logger.error(f"Error sending status update error: {e2}")
                return
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Your payment could not be verified.\n\n"
                         "Possible reasons:\n"
                         "• Image unclear or cropped\n"
                         "• Incorrect UPI ID or amount\n"
                         "• Transaction not completed\n\n"
                         "Please try again with a clear screenshot, or contact @IIG_DARK_YT for assistance."
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id} about payment rejection: {e}")
            
            # Update admin message
            try:
                await query.edit_message_text(
                    f"❌ Payment REJECTED for user {user_id}\n\n"
                    f"🆔 Payment ID: {payment_id}\n"
                    f"⏰ {context._application.loop.time() if context._application else 'N/A'}"
                )
            except Exception as e:
                logger.error(f"Error updating admin rejection message: {e}")
        
        # Clean up
        if 'file_path' in payment_data and os.path.exists(payment_data['file_path']):
            try:
                os.remove(payment_data['file_path'])
            except Exception as e:
                logger.error(f"Error removing payment file: {e}")
        if user_id in self.pending_payments:
            del self.pending_payments[user_id]