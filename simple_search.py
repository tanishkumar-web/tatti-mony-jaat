import aiohttp
import json
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

async def simple_web_search(query, num_results=5):
    """
    Perform a simple web search using a free API
    """
    try:
        # Using a simple search API (this is a placeholder - you might want to use a real API)
        search_url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract relevant information
                    results = []
                    
                    # Add abstract if available
                    if data.get('Abstract'):
                        results.append({
                            'title': data.get('Heading', 'Result'),
                            'url': data.get('AbstractURL', 'No URL'),
                            'description': data.get('Abstract', 'No description')
                        })
                    
                    # Add related topics
                    related_topics = data.get('RelatedTopics', [])
                    for topic in related_topics[:num_results-1]:
                        if 'FirstURL' in topic:
                            results.append({
                                'title': topic.get('Text', 'Result')[:50] + '...' if len(topic.get('Text', '')) > 50 else topic.get('Text', 'Result'),
                                'url': topic.get('FirstURL', 'No URL'),
                                'description': ''
                            })
                    
                    return results
    except Exception as e:
        logger.error(f"Error in simple web search: {e}")
    
    return []

async def fetch_search_results(query):
    """
    Fetch search results and format them nicely
    """
    try:
        results = await simple_web_search(query, 5)
        
        if not results:
            return "❌ No results found for your search."
        
        response = f"🔍 Search Results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            description = result.get('description', '')
            
            response += f"{i}. 📰 {title}\n"
            response += f"   🔗 {url}\n"
            if description:
                # Clean up description
                clean_desc = " ".join(description.split())
                if len(clean_desc) > 100:
                    clean_desc = clean_desc[:100] + "..."
                response += f"   📄 {clean_desc}\n"
            response += "\n"
        
        return response.strip()  # Remove trailing newlines
    except Exception as e:
        logger.error(f"Error formatting search results: {e}")
        return "❌ Error processing search results. Please try again."

# Fallback search function for when web search is not available
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