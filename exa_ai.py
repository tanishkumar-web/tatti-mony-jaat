import os
import logging
from typing import Optional, Dict, Any
from config import EXA_API_KEY

logger = logging.getLogger(__name__)

# Try to import Exa AI
EXA_AVAILABLE = False
Exa = None
try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    logger.warning("exa-py not installed. Exa AI features will be disabled.")

class ExaAI:
    """Exa AI integration for advanced search and content retrieval"""
    
    def __init__(self):
        """Initialize Exa client"""
        self.exa: Optional[Any] = None
        if EXA_AVAILABLE and EXA_API_KEY and Exa is not None:
            try:
                self.exa = Exa(EXA_API_KEY)
            except Exception as e:
                logger.error(f"Error initializing Exa: {e}")
                self.exa = None
        else:
            if not EXA_AVAILABLE:
                logger.warning("Exa AI features are not available. Please install exa-py.")
            elif not EXA_API_KEY:
                logger.warning("Exa API key not found. Exa AI features will be disabled.")
    
    async def search_and_get_contents(self, query, num_results=5, category=None, include_domains=None, exclude_domains=None, 
                                    start_published_date=None, end_published_date=None, highlights=False, summary=False):
        """Search for content and get full text with advanced options"""
        if not self.exa:
            return "❌ Exa AI features are not configured. Please add your EXA_API_KEY to config.py"
        
        try:
            # Build search parameters correctly according to Exa API
            search_params = {
                "query": query,
                "type": "neural",  # Use neural search for better results
                "num_results": min(num_results, 10)  # Limit to 10 for performance
            }
            
            # Add optional parameters
            if category:
                search_params["category"] = category
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            if start_published_date:
                search_params["start_published_date"] = start_published_date
            if end_published_date:
                search_params["end_published_date"] = end_published_date
            
            # First, perform the search
            search_result = self.exa.search(**search_params)
            
            if not search_result.results:
                return "❌ No results found for your query."
            
            # Then get the contents for the results
            urls = [item.url for item in search_result.results]
            
            # Build contents parameters
            contents_params = {
                "urls": urls,
                "text": True
            }
            
            # Add highlights and summary if requested
            if highlights:
                contents_params["highlights"] = {
                    "num_sentences": 2,
                    "highlights_per_url": 1
                }
            
            if summary:
                contents_params["summary"] = {
                    "query": f"Summarize: {query}"
                }
            
            # Get the contents
            contents_result = self.exa.get_contents(**contents_params)
            
            # Create a cleaner, more concise response
            response = f"🔍 Search Results for: {query}\n\n"
            
            for i, item in enumerate(contents_result.results[:3], 1):  # Limit to 3 results for faster response
                title = getattr(item, 'title', 'No title')
                url = getattr(item, 'url', 'No URL')
                text = getattr(item, 'text', 'No content')
                author = getattr(item, 'author', 'Unknown author')
                published_date = getattr(item, 'published_date', 'Unknown date')
                
                # Format published date
                if published_date and published_date != 'Unknown date':
                    try:
                        # Extract just the date part if it's a full datetime
                        if 'T' in str(published_date):
                            published_date = str(published_date).split('T')[0]
                    except:
                        pass
                
                response += f"{i}. 📰 {title}\n"
                response += f"   👤 {author} | 📅 {published_date}\n"
                response += f"   🔗 {url}\n"
                
                # Add summary if available (prioritize over raw text for cleaner response)
                if hasattr(item, 'summary') and item.summary:
                    # Clean up summary text
                    summary_text = " ".join(str(item.summary).split())
                    if len(summary_text) > 150:
                        summary_text = summary_text[:150] + "..."
                    response += f"   📋 {summary_text}\n"
                elif text and text != 'No content':
                    # Clean up text and use as fallback
                    clean_text = " ".join(str(text).split())
                    if len(clean_text) > 150:
                        clean_text = clean_text[:150] + "..."
                    response += f"   📄 {clean_text}\n"
                
                response += "\n"
            
            return response
        except Exception as e:
            logger.error(f"Error searching with Exa: {e}")
            return f"❌ Error searching content: {str(e)}"
    
    async def get_answer(self, question, category=None):
        """Get an answer to a question using Exa with advanced options"""
        if not self.exa:
            return "❌ Exa AI features are not configured. Please add your EXA_API_KEY to config.py"
        
        try:
            # Build search parameters correctly
            search_params = {
                "query": question,
                "text": True,
                "num_results": 3  # Limit for faster response
            }
            
            if category:
                search_params["category"] = category
            
            result = self.exa.search_and_contents(**search_params)
            
            if not result.results:
                return "❌ Could not find an answer to your question."
            
            # Extract the most relevant answer from the first result
            answer = ""
            if result.results and len(result.results) > 0:
                first_result = result.results[0]
                if hasattr(first_result, 'text') and first_result.text:
                    # Take first paragraph as answer
                    text_parts = str(first_result.text).split('\n\n')
                    answer = text_parts[0] if text_parts else first_result.text
                    
            if not answer:
                return "❌ Could not find an answer to your question."
            
            # Clean up the answer to make it more readable
            # Fix the concatenation error by ensuring we're working with strings
            if answer is None:
                answer = ""
            answer = " ".join(str(answer).split())
            if len(answer) > 300:
                answer = answer[:300] + "..."
            
            response = f"❓ Question: {question}\n\n"
            response += f"💡 Answer: {answer}\n\n"
            response += f"🔗 Source: {getattr(result.results[0], 'url', 'Unknown source')}"
            
            return response
        except Exception as e:
            logger.error(f"Error getting answer from Exa: {e}")
            return f"❌ Error getting answer: {str(e)}"
    
    async def find_similar_content(self, url, num_results=3, exclude_domains=None, subpages=False):
        """Find similar content to a given URL with advanced options"""
        if not self.exa:
            return "❌ Exa AI features are not configured. Please add your EXA_API_KEY to config.py"
        
        try:
            # Build search parameters correctly
            search_params = {
                "url": url,
                "num_results": min(num_results, 5)  # Limit for performance
            }
            
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            
            # Make the API call
            result = self.exa.find_similar(**search_params)
            
            if not result.results:
                return "❌ No similar content found."
            
            response = f"🔗 Similar content to: {url}\n\n"
            
            for i, item in enumerate(result.results[:3], 1):  # Limit to 3 results
                title = getattr(item, 'title', 'No title')
                url = getattr(item, 'url', 'No URL')
                author = getattr(item, 'author', 'Unknown author')
                published_date = getattr(item, 'published_date', 'Unknown date')
                
                # Format published date
                if published_date and published_date != 'Unknown date':
                    try:
                        # Extract just the date part if it's a full datetime
                        if 'T' in str(published_date):
                            published_date = str(published_date).split('T')[0]
                    except:
                        pass
                
                response += f"{i}. 📰 {title}\n"
                response += f"   👤 {author} | 📅 {published_date}\n"
                response += f"   🔗 {url}\n\n"
            
            return response
        except Exception as e:
            logger.error(f"Error finding similar content with Exa: {e}")
            return f"❌ Error finding similar content: {str(e)}"
    
    async def chat_completion(self, messages, include_context=False):
        """Get a chat completion from Exa with context"""
        if not self.exa:
            return "❌ Exa AI features are not configured. Please add your EXA_API_KEY to config.py"
        
        try:
            try:
                from openai import OpenAI  # type: ignore
                openai_available = True
            except ImportError:
                openai_available = False
                return "❌ OpenAI library not installed. Please install openai library."
            
            if openai_available and EXA_AVAILABLE:
                client = OpenAI(
                    base_url="https://api.exa.ai",
                    api_key=EXA_API_KEY,
                )
                
                extra_body = {
                    "text": True
                }
                
                if include_context:
                    extra_body["context"] = True
                
                completion = client.chat.completions.create(
                    model="exa",
                    messages=messages,
                    extra_body=extra_body
                )
                
                response = completion.choices[0].message.content
                return response
            else:
                return "❌ OpenAI library not available."
        except Exception as e:
            logger.error(f"Error getting chat completion from Exa: {e}")
            return f"❌ Error getting chat completion: {str(e)}"