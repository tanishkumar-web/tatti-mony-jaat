import logging
import asyncio
import time
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException, TimeoutException

logger = logging.getLogger(__name__)

# Simple in-memory cache for fallback responses
search_cache = {}

async def fetch_search_results(query, max_results=5):
    """
    Fetch search results using DuckDuckGo search
    """
    try:
        # Check if we have a cached result
        cache_key = query.lower().strip()
        if cache_key in search_cache:
            # Return cached result if it's less than 1 hour old
            cached_result, timestamp = search_cache[cache_key]
            if time.time() - timestamp < 3600:  # 1 hour
                return cached_result
        
        # Run the synchronous DDGS search in a thread pool to avoid blocking
        def search_sync():
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query, 
                    max_results=max_results,
                    region="us-en",
                    safesearch="moderate"
                ))
            return results
        
        # Execute the search in a separate thread to prevent blocking
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, search_sync)
        
        if not results:
            return "❌ No results found for your search."
        
        response = f"🔍 Search Results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('href', 'No URL')
            description = result.get('body', '')
            
            response += f"{i}. 📰 {title}\n"
            response += f"   🔗 {url}\n"
            if description:
                # Clean up description
                clean_desc = " ".join(description.split())
                if len(clean_desc) > 100:
                    clean_desc = clean_desc[:100] + "..."
                response += f"   📄 {clean_desc}\n"
            response += "\n"
        
        # Cache the result
        search_cache[cache_key] = (response.strip(), time.time())
        
        return response.strip()  # Remove trailing newlines
    except RatelimitException:
        logger.error("Rate limit exceeded for DuckDuckGo search")
        # Try to get cached result even if it's older
        cache_key = query.lower().strip()
        if cache_key in search_cache:
            cached_result, _ = search_cache[cache_key]
            return cached_result + "\n\n⚠️ Note: Showing cached results due to rate limits."
        return "❌ Search rate limit exceeded. Please try again later.\n\nBut here's some information I know about this topic:\n" + fallback_search(query)
    except TimeoutException:
        logger.error("Timeout occurred during DuckDuckGo search")
        return "❌ Search timed out. Please try again.\n\nBut here's some information I know about this topic:\n" + fallback_search(query)
    except Exception as e:
        logger.error(f"Error in DuckDuckGo search: {e}")
        return "❌ Error processing search results. Please try again.\n\nBut here's some information I know about this topic:\n" + fallback_search(query)

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
        'quote': "💬 Quotes are inspiring or thought-provoking sayings that can motivate and uplift your mood.",
        'programming': "💻 Programming is the process of creating instructions that tell a computer how to perform tasks. Popular languages include Python, JavaScript, and Java.",
        'technology': "📱 Technology refers to the application of scientific knowledge for practical purposes. It includes computers, smartphones, software, and digital systems.",
        'science': "🔬 Science is a systematic enterprise that builds and organizes knowledge in the form of testable explanations and predictions about the universe.",
        'math': "🔢 Mathematics is the study of numbers, quantities, and shapes. It's fundamental to many fields including science, engineering, and finance.",
        'history': "📜 History is the study of past events, particularly in human affairs. It helps us understand how societies and civilizations developed.",
        'health': "💪 Health refers to a state of physical, mental, and social well-being. It involves maintaining a balanced lifestyle with proper nutrition and exercise.",
        'education': "📚 Education is the process of facilitating learning and acquiring knowledge, skills, values, beliefs, and habits.",
        'business': "💼 Business refers to commercial or industrial activities aimed at generating profit through the production or distribution of goods and services.",
        'finance': "💰 Finance is the management of money and investments. It includes banking, investing, budgeting, and financial planning.",
        'travel': "✈️ Travel involves visiting different places for leisure, business, or educational purposes. It broadens perspectives and creates memorable experiences.",
        'food': "🍽️ Food is any nutritious substance that people or animals eat or drink to maintain life and growth. It includes a variety of cuisines from around the world.",
        'music': "🎵 Music is an art form whose medium is sound. It encompasses a wide range of styles from classical to contemporary genres.",
        'movie': "🎬 Movies (films) are visual storytelling experiences that entertain, educate, and inspire audiences through moving images and sound.",
        'book': "📖 Books are written or printed works consisting of pages glued or sewn together. They provide knowledge, entertainment, and storytelling.",
        'sport': "⚽ Sports are physical activities that involve skill and competition. They promote fitness, teamwork, and healthy competition among participants.",
        'google': "🔍 Google is a multinational technology company that specializes in Internet-related services and products. It was founded in 1998 by Larry Page and Sergey Brin. Google's core product is its search engine, which helps people find information online. The company also offers services including Gmail, Google Maps, YouTube, Android, and cloud computing.",
        'facebook': "👥 Facebook is a social networking service owned by Meta Platforms Inc. It allows users to connect with friends, share updates, photos, and videos, and join groups based on common interests.",
        'instagram': "📸 Instagram is a photo and video sharing social networking service owned by Meta Platforms. Users can share photos and videos, apply digital filters, and interact with other users through comments and likes.",
        'youtube': "📺 YouTube is a video sharing platform owned by Google. It allows users to upload, view, rate, share, add to playlists, report, comment on videos, and subscribe to other users.",
        'twitter': "🐦 Twitter (now X) is a microblogging and social networking service where users post and interact with messages known as 'tweets'.",
        'whatsapp': "📱 WhatsApp is a freeware, cross-platform messaging and Voice over IP service owned by Meta. It allows users to send text and voice messages, make voice and video calls, and share images, documents, and location information.",
        'amazon': "🛒 Amazon is an American multinational technology company which focuses on e-commerce, cloud computing, digital streaming, and artificial intelligence. It's one of the world's most valuable companies.",
        'microsoft': "💻 Microsoft is an American multinational technology corporation which produces computer software, consumer electronics, personal computers, and related services. Its best known software products are the Windows line of operating systems and the Microsoft Office suite.",
        'apple': "🍏 Apple Inc. is an American multinational technology company that specializes in consumer electronics, computer software, and online services. Its hardware products include the iPhone smartphone, the iPad tablet computer, and the Mac personal computer.",
        'netflix': "🎬 Netflix is a streaming service that offers a wide variety of award-winning TV shows, movies, anime, documentaries, and more on thousands of internet-connected devices.",
        'spotify': "🎵 Spotify is a digital music, podcast, and video streaming service that gives users access to millions of songs and other content from artists all over the world."
    }
    
    query_lower = query.lower()
    
    # Try to find a matching response
    for keyword, response in responses.items():
        if keyword in query_lower:
            return f"🔍 Search Results for: {query}\n\n{response}"
    
    # Default response
    return f"🔍 Search Results for: {query}\n\nI found some information about '{query}'. This is a placeholder response since web search is temporarily unavailable. Please try rephrasing your query or contact the bot administrator."
