import aiohttp
import logging
import random
from config import HUGGING_FACE_API_KEY

# Import our ddg search module
SEARCH_AVAILABLE = False
fetch_search_results = None
try:
    from ddg_search import fetch_search_results
    SEARCH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"DDG search module not available: {e}")

logger = logging.getLogger(__name__)

# Define fallback functions first
def fallback_search(query):
    """
    Simple fallback search with predefined responses
    """
    # Simple keyword matching for common queries
    responses = {
        'ai': "🤖 Artificial Intelligence (AI) refers to the simulation of human intelligence in machines. AI systems can learn, reason, and make decisions.",
        'machine learning': "💻 Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.",
        'python': "🐍 Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and AI.",
        'telegram': "📱 Telegram is a cloud-based instant messaging service that focuses on security and speed.",
        'bot': "🤖 A bot is a software application that performs automated tasks. In Telegram, bots can provide various services and entertainment.",
        'payment': "💳 Payments can be made through various methods including UPI, Paytm, GPay, and PhonePe.",
        'game': "🎮 Games provide entertainment and fun. This bot offers several mini-games like Tic-Tac-Toe, Hangman, and Rock-Paper-Scissors.",
        'quote': "💬 Quotes are inspiring or thought-provoking sayings that can motivate and uplift your mood."
    }
    
    query_lower = query.lower()
    
    # Try to find a matching response
    for keyword, response in responses.items():
        if keyword in query_lower:
            return f"🔍 Search Results for: {query}\n\n{response}"
    
    # Default response
    return f"🔍 Search Results for: {query}\n\nI found some information about '{query}'. This is a placeholder response since web search is not configured. Please try rephrasing your query or contact the bot administrator."

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
                    if isinstance(data, list) and len(data) > 0:
                        response_text = data[0]['generated_text']
                        # Clean up the response to make it more readable
                        clean_response = " ".join(response_text.split())
                        # Return only the response part that's relevant to the prompt
                        if prompt in clean_response:
                            # Extract text after the prompt
                            prompt_index = clean_response.find(prompt)
                            if prompt_index != -1:
                                result = clean_response[prompt_index + len(prompt):].strip()
                                if result:
                                    return result
                        return clean_response
                    else:
                        return str(data)
    except Exception as e:
        logger.error(f"Error fetching AI response: {e}")
    
    # Fallback response with more personality and better responses for common queries
    fallback_responses = {
        'google': "Google is a multinational technology company that specializes in Internet-related services and products. It was founded in 1998 by Larry Page and Sergey Brin while they were Ph.D. students at Stanford University. Google's core product is its search engine, which helps people find information online. The company also offers a wide range of services including Gmail (email), Google Maps, YouTube (video sharing), Android (mobile operating system), and cloud computing services.",
        'what is': "That's a great question! I'd be happy to help explain that to you.",
        'how to': "I'd be glad to help you with that! Here's what I know:",
        'why': "That's an interesting question! Let me think about that for a moment.",
        'when': "That's a good question about timing. Here's what I can tell you:",
        'where': "I can help you with that location question! Here's what I know:",
        'who': "That's a question about a person or entity. Here's what I can tell you:"
    }
    
    # Check for specific patterns in the prompt
    prompt_lower = prompt.lower()
    for key, response in fallback_responses.items():
        if key in prompt_lower:
            return f"🤖 {response}"
    
    # General fallback responses
    general_fallbacks = [
        "That's an interesting point! Tell me more. 🤔",
        "I'm not sure I understand completely. Could you explain further? 🙇‍♂️",
        "Thanks for sharing that with me! 🙏",
        "I appreciate your input on this topic! 💡",
        "That's a fascinating perspective! 👏",
        "I'd love to hear more about that! 🗣️",
        "Thanks for bringing that up! 🎯",
        "That's really thought-provoking! 🧠",
        "Wow, I hadn't thought of it that way! ✨",
        "That's a great question! Let me think... 🤔💭"
    ]
    return "🤖 " + random.choice(general_fallbacks)

async def fetch_search_results_wrapper(query):
    """Fetch search results using ddg search"""
    if SEARCH_AVAILABLE and fetch_search_results is not None:
        try:
            return await fetch_search_results(query)
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return fallback_search(query)
    else:
        return fallback_search(query)

async def detect_user_intent(text):
    """Detect user intent from text"""
    text = text.lower()
    
    intents = {
        'payment': ['pay', 'payment', 'upi', 'qr', 'paytm', 'gpay', 'phonepe', 'transaction', 'paisa', 'bharna'],
        'game': ['game', 'play', 'challenge', 'compete', 'fun', 'khel', 'maze', 'enjoy'],
        'quote': ['quote', 'motivat', 'inspir', 'wisdom', 'saying', 'soch', 'vichar'],
        'proof': ['proof', 'verify', 'verification', 'screenshot', 'evidence', 'praman', 'verify'],
        'help': ['help', 'support', 'assist', 'guide', 'how to', 'madad', 'sahayata'],
        'stats': ['stat', 'score', 'leaderboard', 'rank', 'performance', 'ank', 'stithi'],
        'search': ['search', 'find', 'look', 'research', 'information', 'latest', 'news', 'article', 'khoj', 'dhoondh'],
        'question': ['what', 'how', 'why', 'when', 'where', 'who', '?', 'explain', 'tell me about', 'batao', 'kya', 'kaise'],
        'similar': ['similar', 'related to', 'like this', 'comparable', 'same', 'milti', 'jaisa'],
        'advanced_search': ['advanced', 'detailed', 'comprehensive', 'thorough', 'gahra', 'vistarit']
    }
    
    for intent, keywords in intents.items():
        if any(keyword in text for keyword in keywords):
            return intent
    
    return 'unknown'

async def get_personalized_recommendation(user_stats):
    """Get personalized recommendation based on user stats"""
    if user_stats['games_played'] == 0:
        return "🎮 Why not try playing a game? Type /games to see options! 🎲"
    
    if user_stats['quotes_read'] == 0:
        return "💡 Want some motivation? Type /quote to get a daily inspirational quote! ✨"
    
    if user_stats['payments_requested'] == 0:
        return "💳 Need to make a payment? Type /payments to generate a QR code! 📱"
    
    # Based on what they use most
    max_activity = max(user_stats, key=user_stats.get)
    
    recommendations = {
        'games_played': "🎮 You seem to enjoy games! Try a new challenge with /games 🎯",
        'quotes_read': "💡 You like inspirational content! Get your daily dose with /quote 🌟",
        'payments_requested': "💳 Frequent payer? Generate quick payments with /payments ⚡",
        'successful_payments': "✅ You're a premium user! Check out exclusive content in our channel 🎉"
    }
    
    return recommendations.get(max_activity, "✨ Try exploring something new! Use /help to see all options 🚀")

async def special_user_feature(user_id):
    """Special feature for a specific user (ID: 5550412770)"""
    if user_id == 5550412770:
        # This is for TANISH user
        special_messages = [
            "🌟 Hey TANISH! You're a VIP user with special access! 🎉",
            "👑 Welcome back, TANISH! You have exclusive privileges here! 💎",
            "⭐ TANISH, you're part of the elite group! Special features unlocked! 🔓",
            "🎯 Hello TANISH! As a premium member, you get special treatment! 🎁",
            "🔥 TANISH, you're the chosen one! Access to secret features granted! 🕶️"
        ]
        
        import random
        return random.choice(special_messages)
    
    return None