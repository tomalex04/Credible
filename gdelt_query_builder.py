"""
gdelt_query_builder.py - Module for building GDELT queries using Gemini API

This module uses Google's Gemini API to transform natural language queries
into structured GDELT query format.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up the Gemini API with the API key from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please add it to your .env file.")

# Initialize the Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# Get the model name from environment variables or use default
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# Define the system prompt for Gemini
SYSTEM_PROMPT = """
You are a query builder for the GDELT 2.0 DOC API.
Your task is to take the user's natural language request and produce TEN different variations of the query for the GDELT API. Use simple English words to create variations.

IMPORTANT: First, check if the query contains inappropriate content such as:
- Pornography or sexually explicit content


If the query contains ANY of the above, respond EXACTLY with the string: 
"INAPPROPRIATE_QUERY_DETECTED"

Otherwise, proceed with the following rules:

Rules:
1. IMPORTANT: Always keep the query variations in the SAME LANGUAGE as the user's original query.
2. Correct spelling mistakes in the user input before processing.
3. Remove all words with length less than or equal to 2 characters ONLY if they don't affect meaning.
4. ONLY use AND operators between terms. DO NOT use OR or NOT operators.
5. Create TWO TYPES of variations:
   a. For the first 5 variations: Create journalistic style queries with verbs and complete phrases (e.g., "announced sanctions", "threatens military action")
   b. For the last 5 variations: Focus ONLY on organizations, entities, and relevant nouns WITHOUT any verbs or phrases of speech (e.g., "European Union" AND "Russia" AND "sanctions")
6. CRITICAL: All terms in the main query part (between AND operators) MUST have a minimum length of 5 characters. This rule does NOT apply to sourcecountry, sourceregion, and timestamp parameters.
   - Replace short terms (< 5 chars) with equivalent longer terms (e.g., "UK" → "United Kingdom", "US" → "United States", "EU" → "Europe")
   - For common short words with no longer alternative, add context words to make them more specific
7. Contextual understanding:
   - ALWAYS analyze the query for implied countries, regions, people, or events that suggest a location
   - For people (e.g., "Biden", "Putin", "Modi"), infer their associated country
   - For events (e.g., "Olympics in Paris", "Earthquake in Japan"), extract the location
   - For organizations (e.g., "EU Parliament", "Kremlin"), map to their appropriate region
7. Country and region parameters:
   - Always include sourcecountry and/or sourceregion when you can infer them from context
   - If user mentions a country, include it as: sourcecountry=<ISO code>
   - If user mentions a region, include it as: sourceregion=<region code>
   - For Europe use: sourceregion=EU (not a country code)
   - For implicit locations (e.g., "Eiffel Tower" → France), add the appropriate country code
8. Time range detection:
   - Analyze for any time-related terms ("yesterday", "last week", "June 2025")
   - Include startdatetime and enddatetime for any time reference (format YYYYMMDDHHMMSS)
   - For relative times like "last week" or "recent", calculate actual date ranges
9. Main query construction:
   - Always format as: query=<search terms>
   - For exact phrases use double quotes: query="climate change"
   - Connect concepts with AND ONLY: query="climate change" AND "global warming"
   - Each query should be well-formed with proper placement of operators and quotes
10. Language preservation:
   - If the user's query is in English, all variations must be in English
   - If the user's query is in Spanish, all variations must be in Spanish
   - If the user's query is in French, all variations must be in French
   - Always maintain the original language of the user's query in all variations
11. Output format:
   - Return EXACTLY ten query variations, separated by ||| (three pipe symbols)
   - For the first 5 variations, focus on journalistic style with complete phrases
   - For the last 5 variations, focus ONLY on organizations, entities, locations, and relevant nouns WITHOUT any verbs or phrases of speech
   - Example for entity-only variations: query="United Nations" AND "climate change" AND "Paris"
   - Each query should be a complete, valid GDELT query string
   - Format each query correctly with query= at the beginning and & between parameters
   - Do not explain your choices, just return the ten queries

Examples:
- Input: "Did a tsunami really happen in Japan yesterday?"
  Output: query="tsunami" AND "Japan"&sourcecountry=JP&startdatetime=20250903000000&enddatetime=20250903235959 ||| query="natural disaster" AND "Japan"&sourcecountry=JP&startdatetime=20250903000000&enddatetime=20250903235959 ||| query="earthquake" AND "tsunami" AND "Japan"&sourcecountry=JP&startdatetime=20250903000000&enddatetime=20250903235959

- Input: "Is it true that there was an explosion near the Eiffel Tower?"
  Output: query="explosion" AND "Eiffel Tower"&sourcecountry=FR&sourceregion=EU ||| query="incident" AND "Eiffel Tower" AND "Paris"&sourcecountry=FR&sourceregion=EU ||| query="security" AND "Eiffel Tower" AND "explosion"&sourcecountry=FR&sourceregion=EU

- Input: "Did Biden announce new sanctions against Russia last week?"
  Output: query="Biden" AND "sanctions" AND "Russia"&sourcecountry=US&startdatetime=20250828000000&enddatetime=20250903235959 ||| query="United States" AND "sanctions" AND "Russia"&sourcecountry=US&startdatetime=20250828000000&enddatetime=20250903235959 ||| query="Biden" AND "economic measures" AND "Russia"&sourcecountry=US&startdatetime=20250828000000&enddatetime=20250903235959
  
- Input: "¿Hubo una manifestación en Madrid ayer?"
  Output: query="manifestación" AND "Madrid"&sourcecountry=ES&startdatetime=20250903000000&enddatetime=20250903235959 ||| query="protesta" AND "Madrid"&sourcecountry=ES&startdatetime=20250903000000&enddatetime=20250903235959 ||| query="manifestación" AND "España" AND "Madrid"&sourcecountry=ES&startdatetime=20250903000000&enddatetime=20250903235959

- Input: "Was a new law on AI passed in UK?"
  Output: query="legislation" AND "artificial intelligence" AND "United Kingdom"&sourcecountry=GB ||| query="regulation" AND "artificial intelligence" AND "United Kingdom"&sourcecountry=GB ||| query="parliament" AND "artificial intelligence" AND "United Kingdom"&sourcecountry=GB
"""


def generate_query(user_input: str) -> list:
    """
    Generate ten structured GDELT queries from natural language input using Gemini API.
    
    Args:
        user_input (str): The user's natural language query
        
    Returns:
        list: List of ten structured GDELT query variations or a list with a single
              inappropriate content message if the query contains sensitive topics
    """
    try:
        # Create the chat with system prompt and user input
        combined_prompt = f"{SYSTEM_PROMPT}\n\nUser request: {user_input}"
        
        # Generate content with the specified model
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Set generation config to disable thinking
        generation_config = genai.GenerationConfig(
            temperature=0.3,  # Slightly higher temperature for more variation
        )
        
        response = model.generate_content(
            combined_prompt,
            generation_config=generation_config
        )
        
        # Extract the response text
        response_text = response.text.strip()
        
        # Check if the model detected inappropriate content
        if response_text == "INAPPROPRIATE_QUERY_DETECTED":
            print(f"⚠️ Inappropriate query detected: '{user_input}'")
            # Return a special marker that will be detected in main.py
            return ["INAPPROPRIATE_QUERY"]
        
        # Split the response by the separator
        query_variations = response_text.split('|||')
        
        # Clean and format each query variation
        formatted_queries = []
        for i, query in enumerate(query_variations):
            query = query.strip()
            
            # Ensure query format is correct - add "query=" if needed
            if not (query.startswith('query=') or 
                    'sourcecountry=' in query or 
                    'sourceregion=' in query or
                    'startdatetime=' in query):
                # Add query= prefix if not dealing with just filter parameters
                query = f'query={query}'
            
            formatted_queries.append(query)
        
        # If we don't have exactly 10 queries, duplicate or trim as needed
        while len(formatted_queries) < 10:
            formatted_queries.append(formatted_queries[0])
        
        if len(formatted_queries) > 10:
            formatted_queries = formatted_queries[:10]
        
        # Log the transformation only once
        print(f"Original input: '{user_input}'")
        for i, query in enumerate(formatted_queries):
            print(f"Query variation {i+1}: '{query}'")
        
        return formatted_queries
        
    except Exception as e:
        if "429" in str(e):
            print(f"⚠️ Rate limit exceeded for Gemini API. Using original query. Details: {e}")
        elif "404" in str(e) and "models" in str(e):
            print(f"⚠️ Model not found. Please check available models. Details: {e}")
        elif "400" in str(e) and "API key" in str(e):
            print(f"⚠️ Invalid API key. Please check your GEMINI_API_KEY in .env file. Details: {e}")
        else:
            print(f"⚠️ Error generating structured query: {e}")
        
        # Format the original query with quotes for GDELT for all ten variations
        fallback_query = f'query="{user_input}"'
        return [fallback_query] * 10


if __name__ == "__main__":
    # Example usage
    test_queries = [
        "Latest news about climate change in Europe",
        "Political developments in Ukraine last week",
        "Economic impact of recent floods in Asia",
        "Noticias sobre cambio climático en España"  # Spanish query
    ]
    
    print("\nGDELT Query Builder - Example Usage\n")
    for query in test_queries:
        print(f"\nTesting query: {query}")
        query_variations = generate_query(query)
        for i, variation in enumerate(query_variations):
            print(f"Variation {i+1}: {variation}")
        print("-" * 80)
