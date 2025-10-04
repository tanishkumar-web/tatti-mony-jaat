import os
import qrcode
from PIL import Image
import cv2
import numpy as np
import logging
import easyocr
from datetime import datetime

logger = logging.getLogger(__name__)

def init_directories():
    """Initialize required directories"""
    dirs = ['temp', 'proofs']
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            logger.info(f"Created directory: {dir_name}")

def generate_qr_code(data, filename):
    """Generate QR code for given data"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
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

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        for filename in os.listdir('temp'):
            file_path = os.path.join('temp', filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        logger.info("Temporary files cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        # Initialize EasyOCR reader
        reader = easyocr.Reader(['en'])  # English language
        
        # Read text from image
        result = reader.readtext(image_path)
        
        # Extract text from results
        extracted_text = ""
        for (bbox, text, prob) in result:
            extracted_text += text + " "
        
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return None

def process_payment_screenshot(image_path):
    """Process payment screenshot to extract payment details"""
    try:
        # Extract text from image
        text = extract_text_from_image(image_path)
        
        if not text:
            return "❌ Could not extract text from the image."
        
        # Simple keyword matching for payment details
        upi_keywords = ['upi', 'vpa', '@', 'paytm', 'gpay', 'phonepe', 'bhim']
        amount_keywords = ['amount', 'rs', 'inr', '₹', 'rupees']
        
        # Check if it contains UPI related information
        has_upi = any(keyword in text.lower() for keyword in upi_keywords)
        has_amount = any(keyword in text.lower() for keyword in amount_keywords)
        
        if has_upi and has_amount:
            return f"✅ Payment details detected!\n\nExtracted text:\n{text[:200]}..."
        elif has_upi:
            return f"✅ UPI information detected!\n\nExtracted text:\n{text[:200]}..."
        else:
            return f"🔍 Processed image but couldn't find clear payment information.\n\nExtracted text:\n{text[:200]}..."
            
    except Exception as e:
        logger.error(f"Error processing payment screenshot: {e}")
        return "❌ Error processing the payment screenshot."

def extract_upi_details(text):
    """Extract UPI details from text"""
    upi_id = None
    amount = None
    transaction_id = None
    
    # Look for UPI ID patterns
    import re
    upi_patterns = [
        r'\d{10,12}@[a-zA-Z]+',
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r'[a-zA-Z0-9]+@[a-zA-Z]+'
    ]
    
    for pattern in upi_patterns:
        matches = re.findall(pattern, text)
        if matches:
            upi_id = matches[0]
            break
    
    # Look for amount patterns
    amount_patterns = [
        r'₹\s*(\d+(?:\.\d+)?)',
        r'Rs\.*\s*(\d+(?:\.\d+)?)',
        r'amount.*?(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*rs',
        r'(\d+(?:\.\d+)?)\s*inr'
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            amount = matches[0]
            break
    
    # Look for transaction ID patterns
    txn_patterns = [
        r'(?:txn|transaction).*?([A-Z0-9]{8,})',
        r'([A-Z0-9]{8,})\s*(?:ref|reference)',
        r'(?:ref|reference).*?([A-Z0-9]{8,})'
    ]
    
    for pattern in txn_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            transaction_id = matches[0]
            break
    
    return {
        'upi_id': upi_id,
        'amount': amount,
        'transaction_id': transaction_id
    }

def is_valid_image(file_path):
    """Check if file is a valid image"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def get_file_extension(file_path):
    """Get file extension"""
    return os.path.splitext(file_path)[1].lower()

def is_valid_file_type(file_path):
    """Check if file type is valid"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    return get_file_extension(file_path) in valid_extensions

def is_valid_file_size(file_path, max_size_mb=10):
    """Check if file size is within limit"""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return file_size_mb <= max_size_mb

def format_datetime(dt):
    """Format datetime for display"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_time_based_greeting():
    """Get time-based greeting"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 21:
        return "Good evening"
    else:
        return "Good night"