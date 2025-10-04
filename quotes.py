import aiohttp
import random
import logging
from database import get_random_quote, add_quote

logger = logging.getLogger(__name__)

async def fetch_quote_from_api():
    """Fetch a motivational quote from an online API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.quotable.io/random") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'quote': data['content'],
                        'author': data['author'],
                        'category': 'random'
                    }
    except Exception as e:
        logger.error(f"Error fetching quote from API: {e}")
    
    # Fallback to database quote
    quote_data = get_random_quote()
    if quote_data:
        return {
            'quote': quote_data[1],
            'author': quote_data[2],
            'category': quote_data[3]
        }
    
    # Final fallback
    fallback_quotes = [
        {
            'quote': "The only way to do great work is to love what you do.",
            'author': "Steve Jobs",
            'category': "motivation"
        },
        {
            'quote': "Innovation distinguishes between a leader and a follower.",
            'author': "Steve Jobs",
            'category': "innovation"
        },
        {
            'quote': "Your time is limited, don't waste it living someone else's life.",
            'author': "Steve Jobs",
            'category': "life"
        },
        {
            'quote': "Stay hungry, stay foolish.",
            'author': "Steve Jobs",
            'category': "philosophy"
        },
        {
            'quote': "The future belongs to those who believe in the beauty of their dreams.",
            'author': "Eleanor Roosevelt",
            'category': "dreams"
        }
    ]
    return random.choice(fallback_quotes)

async def fetch_joke_from_api():
    """Fetch a joke from an online API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/jokes/random") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'setup': data['setup'],
                        'punchline': data['punchline']
                    }
    except Exception as e:
        logger.error(f"Error fetching joke from API: {e}")
    
    # Fallback jokes
    fallback_jokes = [
        {
            'setup': "Why don't scientists trust atoms?",
            'punchline': "Because they make up everything!"
        },
        {
            'setup': "What did one ocean say to the other ocean?",
            'punchline': "Nothing, they just waved!"
        },
        {
            'setup': "Why did the scarecrow win an award?",
            'punchline': "Because he was outstanding in his field!"
        }
    ]
    return random.choice(fallback_jokes)

async def fetch_fact_from_api():
    """Fetch a random fact from an online API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/random.json?language=en") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'fact': data['text']
                    }
    except Exception as e:
        logger.error(f"Error fetching fact from API: {e}")
    
    # Fallback facts
    fallback_facts = [
        {
            'fact': "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat."
        },
        {
            'fact': "A group of flamingos is called a 'flamboyance'."
        },
        {
            'fact': "Octopuses have three hearts and blue blood."
        }
    ]
    return random.choice(fallback_facts)