import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get SerpAPI key from environment variables
API_KEY = os.getenv('SERPAPI_KEY')
if not API_KEY:
    raise ValueError("SERPAPI_KEY environment variable not set. Please add it to your .env file.")

def google_search(query, num_results=25):
    """
    Search Google for articles related to the query using SerpAPI.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        
    Returns:
        list: List of article dictionaries with title, snippet, and URL
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",   # search engine
        "q": query,           # search query
        "api_key": API_KEY,   # your key
        "num": num_results    # number of results
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        results = response.json()

        output = []
        for item in results.get("organic_results", []):
            # Format the results to match GDELT article format for consistency
            article = {
                "title": item.get("title", "No title"),
                "snippet": item.get("snippet", "No description available"),
                "url": item.get("link", ""),
                "source": {
                    "name": item.get("source", "Google Search")
                },
                "publishedAt": "",  # No date information in the API response
                "origin": "google_search"  # Add origin to track source
            }
            output.append(article)
            
        print(f"Found {len(output)} results from Google Search")
        return output
        
    except Exception as e:
        print(f"Error with Google Search API: {e}")
        return []

# Example usage
if __name__ == "__main__":
    query = "GM stopped operations in India"
    search_results = google_search(query)
    for r in search_results:
        print(f"{r['title']}\n{r['snippet']}\n{r['link']}\n")
