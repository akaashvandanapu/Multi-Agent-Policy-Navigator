"""
Ollama Web Search Tools
Direct tool wrappers for Ollama Web Search API
These tools call the Ollama API directly, providing web search capabilities
"""

import os
import httpx
import asyncio
from typing import Optional
from crewai.tools import tool
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

API_KEY = os.getenv('OLLAMA_API_KEY')

if not API_KEY:
    raise ValueError('OLLAMA_API_KEY environment variable is required')


async def make_api_request(url: str, payload: dict, max_retries: int = 3) -> dict:
    """Make API request with retry logic and error handling."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers={'Authorization': f'Bearer {API_KEY}'},
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                raise Exception(f"Request timed out after {max_retries} attempts")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                if attempt == max_retries - 1:
                    raise Exception("Rate limit exceeded. Please try again later.")
                await asyncio.sleep(5 * (attempt + 1))  # Longer wait for rate limits
            elif e.response.status_code >= 500:  # Server error
                if attempt == max_retries - 1:
                    raise Exception(f"Server error: {e.response.status_code}")
                await asyncio.sleep(2 ** attempt)
            else:
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Request failed: {str(e)}")
            await asyncio.sleep(2 ** attempt)

    raise Exception("All retry attempts failed")


@tool("Ollama Web Search Tool")
def web_search(query: str, max_results: int = 10) -> str:
    """Search the web using Ollama's web search API.
    
    This tool performs real-time web searches to find current information about
    market prices, MSP, weather conditions, and other agricultural data.
    Use this tool when you need up-to-date information that's not in the local database.
    
    Args:
        query: The search query string. Be specific about what you're looking for.
               Examples: "current MSP for rice India 2024", "latest market price rice Andhra Pradesh",
               "weather forecast Andhra Pradesh agriculture"
        max_results: Maximum number of results to return (default: 10, max: 20)
    
    Returns:
        Formatted search results with titles, URLs, and content excerpts.
        Results are sorted by relevance and include source URLs for verification.
    """
    try:
        # Validate and clamp max_results
        max_results = max(1, min(max_results, 20))
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data = loop.run_until_complete(make_api_request(
                'https://ollama.com/api/web_search',
                {'query': query, 'max_results': max_results}
            ))
        finally:
            loop.close()
        
        # Parse and format the results
        if 'results' in data and data['results']:
            # Format results for better readability
            formatted_results = []
            for i, result in enumerate(data['results'][:max_results], 1):
                formatted_results.append({
                    'rank': i,
                    'title': result.get('title', 'No title'),
                    'url': result.get('url', 'No URL'),
                    'content': result.get('content', 'No content')[:500] + '...' if len(result.get('content', '')) > 500 else result.get('content', 'No content')
                })
            
            output = f"Search Results for: '{query}'\n\n"
            output += "\n\n".join([
                f"{result['rank']}. **{result['title']}**\n   URL: {result['url']}\n   Content: {result['content']}"
                for result in formatted_results
            ])
            return output
        else:
            return f"Search completed for: '{query}'\n\nNo results found or unexpected response format."
    
    except Exception as e:
        return f"Error performing web search: {str(e)}"


@tool("Ollama Web Fetch Tool")
def web_fetch(url: str) -> str:
    """Fetch content from a web page using Ollama's web fetch API.
    
    This tool retrieves the full content of a webpage when you have a specific URL.
    Use this tool after web_search to get detailed information from specific sources.
    
    Args:
        url: The URL of the webpage to fetch. Must start with http:// or https://
    
    Returns:
        Formatted page content with title, content, and links found on the page.
    """
    try:
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return "Error: URL must start with http:// or https://"
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data = loop.run_until_complete(make_api_request(
                'https://ollama.com/api/web_fetch',
                {'url': url}
            ))
        finally:
            loop.close()
        
        # Format the response
        title = data.get('title', 'No title available')
        content = data.get('content', 'No content available')
        links = data.get('links', [])
        
        formatted_response = f"**Page Title:** {title}\n\n**URL:** {url}\n\n**Content:**\n{content[:2000]}{'...' if len(content) > 2000 else ''}"
        
        if links:
            formatted_response += f"\n\n**Links Found:** {len(links)}\n" + "\n".join(f"- {link}" for link in links[:10])
            if len(links) > 10:
                formatted_response += f"\n... and {len(links) - 10} more links"
        
        return formatted_response
    
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

