"""
gdelt_api.py - Module for interacting with the GDELT API

This module provides functions for fetching articles from GDELT
and filtering by trusted domains.
"""

import os
import requests
import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Import the whitelist from the separate module
from whitelisted_domains import WHITELISTED_DOMAINS


def fetch_articles_from_gdelt(query):
    """
    Fetch news articles from GDELT API.
    
    Args:
        query (str): The news query to search for (can be structured GDELT query)
        
    Returns:
        list: List of article dictionaries, or empty list if no results or error
    """
    try:
        # Construct the API URL with the query
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
        # Parse the query to separate main query from other parameters
        params = {
            'format': 'json',
            'maxrecords': int(os.getenv('MAX_ARTICLES_PER_QUERY', 250))
        }
        
        # If the query has multiple parameters (separated by &)
        if '&' in query:
            parts = query.split('&')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    params[key] = value
                elif part.startswith('query='):
                    params['query'] = part[6:]  # Remove 'query='
                else:
                    # If it's just a query without the query= prefix
                    if 'query' not in params:
                        params['query'] = part
        else:
            # It's just a simple query
            if query.startswith('query='):
                params['query'] = query[6:]  # Remove 'query='
            else:
                params['query'] = query
        
        # Convert params to query string
        query_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        url = f"{base_url}?{query_string}"
        
        print(f"DEBUG - Requesting URL: {url}")
        
        # Make the request
        response = requests.get(url, timeout=30)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # GDELT API returns articles in the 'articles' field
            if 'articles' in data:
                return data['articles']
        
        return []
        
    except Exception as e:
        print(f"⚠️ Error fetching articles from GDELT: {e}")
        return []


def is_whitelisted_domain(url):
    """
    Check if the URL belongs to a whitelisted domain.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the domain is whitelisted, False otherwise
    """
    try:
        domain = urlparse(url).netloc
        
        # Handle subdomains by checking if any whitelisted domain is a suffix
        return any(domain.endswith(trusted_domain) for trusted_domain in WHITELISTED_DOMAINS)
    except:
        return False


def format_timestamp(timestamp_str):
    """
    Format a GDELT timestamp string to a more user-friendly format.
    
    Args:
        timestamp_str (str): Timestamp string in GDELT format (e.g., "20250829T173000Z")
        
    Returns:
        str: Formatted timestamp (e.g., "Aug 29, 2025 17:30")
    """
    if not timestamp_str:
        return ""
        
    try:
        # Handle common GDELT timestamp format
        if "T" in timestamp_str and len(timestamp_str) >= 15:
            # Parse YYYYMMDDTHHMMSSZ format
            year = timestamp_str[0:4]
            month = timestamp_str[4:6]
            day = timestamp_str[6:8]
            hour = timestamp_str[9:11]
            minute = timestamp_str[11:13]
            
            # Convert month number to month name
            month_name = datetime.datetime.strptime(month, "%m").strftime("%b")
            
            return f"{month_name} {int(day)}, {year} {hour}:{minute}"
        else:
            # Return original if not in expected format
            return timestamp_str
    except Exception as e:
        print(f"Error formatting timestamp {timestamp_str}: {e}")
        return timestamp_str


def filter_by_whitelisted_domains(articles):
    """
    Filter articles to only include those from trusted domains.
    
    Args:
        articles (list): List of article dictionaries
        
    Returns:
        list: Filtered list of article dictionaries
    """
    if not articles:
        return []
    
    trusted_articles = []
    total_articles = len(articles)
    
    for article in articles:
        if 'url' in article and is_whitelisted_domain(article['url']):
            trusted_articles.append(article)
    
    filtered_count = total_articles - len(trusted_articles)
    print(f"Domain filtering: {filtered_count} non-whitelisted articles removed, {len(trusted_articles)} whitelisted articles kept")
    
    return trusted_articles


def normalize_gdelt_articles(articles):
    """
    Normalize GDELT article format to match the expected format in the rest of the application.
    
    Args:
        articles (list): List of GDELT article dictionaries
        
    Returns:
        list: List of normalized article dictionaries
    """
    normalized_articles = []
    
    for article in articles:
        # Extract domain from URL for source name if not available
        source_name = article.get('sourcename', '')
        if not source_name and 'url' in article:
            domain = urlparse(article['url']).netloc
            source_name = domain.replace('www.', '')
        
        # Format the timestamp for better readability
        raw_timestamp = article.get('seendate', '')
        formatted_timestamp = format_timestamp(raw_timestamp)
        
        normalized_articles.append({
            'title': article.get('title', ''),
            'description': article.get('seentext', ''),
            'url': article.get('url', ''),
            'publishedAt': formatted_timestamp,
            'source': {'name': source_name}
        })
    
    return normalized_articles
