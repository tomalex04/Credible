"""
bias_analyzer.py - Module for bias analysis, categorization, and summarization

This module provides functions for:
1. Analyzing bias in news sources
2. Categorizing articles by bias category
3. Creating embeddings for each category
4. Summarizing information from unbiased sources
"""

import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Import from ranker to use the shared model cache and device detection
from ranker import DEVICE, _MODEL_CACHE

# Load environment variables
load_dotenv()

# Set up the Gemini API with the API key from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please add it to your .env file.")

# Initialize the Gemini client
genai.configure(api_key=GEMINI_API_KEY)


def analyze_bias(query, outlet_names, model_name):
    """
    Analyzes bias in news sources and categorizes them.
    
    Args:
        query (str): The original user query
        outlet_names (list): List of unique outlet names to categorize
        model_name (str): The name of the Gemini model to use
        
    Returns:
        dict: Dictionary containing bias analysis results and categorized articles
    """
    # Only print status messages if debug mode is enabled
    print(f"Analyzing potential bias in {len(outlet_names)} unique news outlets...")
    
    try:
        # Define system prompt for bias analysis
        bias_analysis_prompt = """
        You are an expert media bias analyzer. Your task is to categorize news sources into bias categories based on their reporting styles, focus, and potential biases.
        
        Analyze the provided list of news outlets in the context of the user's query. Identify any number of distinct bias categories that best describe the potential biases in these sources, plus EXACTLY one "unbiased" category (not "neutral" or any other name). The categories should reflect the relevant dimensions of bias for this specific query and set of outlets.
        
        For example, depending on the query and outlets, your categories might be:
        - Query about climate change: "industry-funded", "environmental-activist", "unbiased"
        - Query about international conflict: "pro-western", "state-controlled", "anti-western", "regional-perspective", "unbiased"
        - Query about economic policy: "pro-business", "labor-oriented", "progressive", "conservative", "unbiased"
        
        Consider these factors:
        - Historical reporting patterns and perspectives
        - Ownership and financial interests
        - Terminology and framing used in headlines
        - Fact-based vs. opinion-heavy reporting
        - Regional or national interests that may influence coverage
        
        CRITICAL REQUIREMENT: One category MUST be exactly named "unbiased" (not "neutral", "balanced", "centrist", or any other variation).
        
        Return your response in the exact JSON format shown below:
        {
          "categories": {
            "bias category 1": [list of outlet names in this category],
            "bias category 2": [list of outlet names in this category],
            "bias category 3": [list of outlet names in this category],
            "bias category 4": [list of outlet names in this category],
            "unbiased": [list of outlet names that are generally neutral]
          },
          "descriptions": {
            "bias category 1": "A concise description of what this category represents",
            "bias category 2": "A concise description of what this category represents",
            "bias category 3": "A concise description of what this category represents",
            "bias category 4": "A concise description of what this category represents",
            "unbiased": "A concise description of what this category represents"
          },
          "reasoning": "A brief explanation of your overall categorization approach"
        }
        
        The number of bias categories can vary based on the query and news sources - create as many distinct categories as needed to accurately represent the different perspectives. You are not limited to just 1 or 2 bias categories - use as many as necessary.
        
        Replace "bias category 1", "bias category 2", etc. with meaningful names that describe the bias types you've identified.
        Be comprehensive and put every outlet in exactly one category.
        IMPORTANT: You MUST name one category exactly "unbiased" (lowercase) without any variation.
        """
        
        # Use the original query directly
        corrected_query = query
        
        # Prepare input for Gemini
        input_text = f"Query: {corrected_query}\n\nNews Sources:\n" + "\n".join(outlet_names)
        #print(input_text)
        # Initialize Gemini client and generate analysis
        model = genai.GenerativeModel(model_name)
        
        generation_config = genai.GenerationConfig(
            temperature=0.1,  # Lower temperature for more deterministic results
        )
        
        response = model.generate_content(
            f"{bias_analysis_prompt}\n\n{input_text}",
            generation_config=generation_config
        )
        
        # Parse the JSON response
        response_text = response.text
        json_match = re.search(r'{[\s\S]*}', response_text)
        
        if json_match:
            parsed_response = json.loads(json_match.group(0))
            
            # Handle the new JSON structure with categories and descriptions
            bias_analysis = {}
            category_descriptions = {}
            
            # Extract categories and descriptions from the new format
            if 'categories' in parsed_response:
                # New format
                categories = parsed_response.get('categories', {})
                category_descriptions = parsed_response.get('descriptions', {})
                reasoning = parsed_response.get('reasoning', 'No reasoning provided')
                
                # Make sure one category is exactly named "unbiased"
                # If there's a similar category (like "neutral"), rename it to "unbiased"
                has_unbiased = "unbiased" in categories
                if not has_unbiased:
                    similar_category = None
                    for cat in list(categories.keys()):
                        if cat.lower() in ["neutral", "center", "balanced", "objective", "impartial"]:
                            similar_category = cat
                            break
                    
                    # Rename the similar category to "unbiased" if found
                    if similar_category:
                        categories["unbiased"] = categories.pop(similar_category)
                        if similar_category in category_descriptions:
                            category_descriptions["unbiased"] = category_descriptions.pop(similar_category)
                
                # Copy categories to the top level for backward compatibility
                for category, outlets in categories.items():
                    bias_analysis[category] = outlets
            else:
                # Old format for backward compatibility
                for key, value in parsed_response.items():
                    if key != "reasoning":
                        bias_analysis[key] = value
                reasoning = parsed_response.get('reasoning', 'No reasoning provided')
            
            # Add reasoning
            bias_analysis["reasoning"] = reasoning
            
            # Add descriptions to the analysis result
            bias_analysis["descriptions"] = category_descriptions
            
            # Print bias categories
            print("\nBias Analysis Results:")
            # Print information about each category
            for key, values in bias_analysis.items():
                if key not in ["reasoning", "descriptions"]:
                    print(f"{key}: {len(values)} sources")
            
            print(f"\nReasoning: {bias_analysis.get('reasoning', 'No reasoning provided')}")
            
            return bias_analysis
        else:
            print("⚠️ Could not parse bias analysis response from Gemini.")
            # Return an empty analysis with at least unbiased category if parsing fails
            return {
                "unbiased": [],
                "reasoning": "Failed to analyze bias"
            }
    
    except Exception as e:
        print(f"⚠️ Error in bias analysis module: {e}")
        # Return an empty analysis with at least unbiased category if an error occurs
        return {
            "unbiased": [],
            "reasoning": f"Error in analysis: {str(e)}"
        }


def categorize_and_rank_by_bias(query, normalized_articles, bias_analysis, ranker, min_threshold):
    """
    Categorizes articles by bias category and creates embeddings for each category.
    
    Args:
        query (str): The original user query
        normalized_articles (list): List of normalized article dictionaries
        bias_analysis (dict): The bias analysis results
        ranker: The ArticleRanker instance
        min_threshold (float): Minimum similarity threshold
        
    Returns:
        dict: Dictionary containing ranked articles by category
    """
    # Get number of articles per category from environment variable
    top_n_per_category = int(os.getenv('TOP_N_PER_CATEGORY', 5))
    
    # Extract the category names from the bias analysis
    categories = []
    for key in bias_analysis.keys():
        if key not in ["reasoning", "descriptions"]:
            categories.append(key)
    
    # Initialize dictionaries for categorized articles
    categorized_articles = {}
    for category in categories:
        categorized_articles[category] = []
    
    # Categorize articles based on their source
    for article in normalized_articles:
        # Extract source name (handling both object and string formats)
        if isinstance(article['source'], dict):
            source_name = article['source'].get('name', '')
        else:
            source_name = article['source']
        
        # Check each category to see if this source belongs to it
        for category in categories:
            if source_name in bias_analysis.get(category, []):
                categorized_articles[category].append(article)
                break
    
    # Create separate embeddings for each category
    category_rankings = {}
    
    for category, articles in categorized_articles.items():
        if not articles:
            category_rankings[category] = []
            continue
            
        print(f"Creating embeddings for {len(articles)} articles in '{category}' category...")
        
        # Prepare article texts for this category - ONLY USE TITLES
        category_texts = [article['title'] for article in articles]
        
        try:
            # Create embeddings for this category
            query_embedding, category_embeddings = ranker.create_embeddings(query, category_texts)
            
            # Calculate similarities
            similarities = ranker.calculate_similarities(query_embedding, category_embeddings)
            
            # Get top articles for this category
            top_indices = ranker.get_top_articles(
                similarities, 
                articles, 
                min(top_n_per_category, len(articles)), 
                min_threshold
            )
            
            # Format results for this category
            category_rankings[category] = ranker.format_results(top_indices, similarities, articles)
            
            # No need to print articles here since they will be printed in main.py
        
        except Exception as e:
            print(f"⚠️ Error ranking articles for '{category}' category: {e}")
            category_rankings[category] = []
    
    return category_rankings


def generate_summary(query, normalized_articles, category_rankings, model_name):
    """
    Generates a summary using articles from all categories, clearly identifying each category's sources.
    
    Args:
        query (str): The original user query
        normalized_articles (list): List of normalized article dictionaries
        category_rankings (dict): The ranked articles by category
        model_name (str): The name of the Gemini model to use
        
    Returns:
        str: The generated summary
    """
    # Extract the reasoning from category_rankings if available
    reasoning = category_rankings.get("reasoning", "No reasoning provided") if isinstance(category_rankings, dict) else "No reasoning provided"
    
    # Check if we have any articles for summarization
    if not category_rankings or all(not articles for category, articles in category_rankings.items() 
                                if category not in ["descriptions", "reasoning"]):
        print("No articles available for summarization.")
        return "No articles available for summarization."
    
    # Define system prompt for summarization
    summarization_prompt = """
    You are an expert news summarizer focused on factual reporting. Your task is to create a concise, factual summary based on multiple news sources from different bias categories.
    
    The articles provided will be clearly labeled with their bias category. You will receive articles from different perspectives:
    Articles from the "unbiased" category are generally considered neutral and factual
    Articles from other categories may represent specific perspectives or biases
    
    Guidelines:
    1. Focus primarily on verifiable facts that appear across multiple sources
    2. Highlight areas of consensus across sources from different categories
    3. Note significant differences in how different categories report on the same events
    4. Maintain neutral language in your summary despite potential bias in the sources
    5. Include relevant dates, figures, and key details
    6. Prioritize information that directly answers the user's query
    7. Acknowledge different perspectives when they exist
    
    IMPORTANT FORMAT INSTRUCTION: Do not use any symbols such as hash (#), asterisk (*), hyphen (-), underscore (_), or any other special characters in your output. Use plain text without any special formatting symbols.
    
    Structure your response in these sections:
    1. SUMMARY A 3 to 5 sentence factual answer to the query that balances all perspectives
    2. KEY FACTS 4 to 6 numbered points with the most important verified information (use numbers only, no symbols)
    3. DIFFERENT PERSPECTIVES Brief explanation of how different sources frame the issue
    4. SOURCES BY CATEGORY 
       Group sources under their respective categories (UNBIASED SOURCES, CATEGORY 1 SOURCES, etc.)
       Under each category heading, list UP TO 5 URLs of sources from that category
       Number sources starting from 1 within EACH category (each category has its own 1 to 5 numbering)
       Include only the source name, date, and URL for each source
       Format: 1. source.com (date) URL https://source.com/article
    
    IMPORTANT 
    Show each category as a separate heading with the category name in ALL CAPS
    List all sources from the same category together under their category heading
    Each category should have its OWN numbering from 1 to 5 (do NOT number continuously across categories)
    Include URLs for each source, clearly labeled
    Show up to 5 sources PER CATEGORY (not 5 total)
    DO NOT use any special characters or symbols such as hash (#), asterisk (*), hyphen (-), underscore (_)
    
    Be accurate, concise, and provide a balanced view that acknowledges different perspectives.
    """
    
    # We'll limit to a maximum of 30 articles total (to avoid overloading Gemini)
    # but we'll make sure each category is represented
    article_info = []
    article_number = 1
    max_articles_total = 30
    
    # Count the number of non-empty categories
    valid_categories = [cat for cat in category_rankings.keys() 
                       if cat not in ["descriptions", "reasoning"] and category_rankings[cat]]
    
    # Calculate how many articles to take from each category to maintain balance
    # Ensure we try to get at least 5 per category when possible
    articles_per_category = min(10, max(5, max_articles_total // len(valid_categories))) if valid_categories else 0
    
    # Process articles from each category
    for category, articles in category_rankings.items():
        # Skip non-category keys
        if category in ["descriptions", "reasoning"]:
            continue
            
        # Skip empty categories
        if not articles:
            continue
            
        # Get limited articles for this category
        top_articles = articles[:min(articles_per_category, len(articles))]
        
        # Add category header
        article_info.append(f"\n===== ARTICLES FROM {category.upper()} CATEGORY =====\n\n")
        
        # Extract article information for this category
        for article in top_articles:
            # Find the full article data from normalized_articles
            for full_article in normalized_articles:
                if full_article['url'] == article['url']:
                    # Extract source name (handling both object and string formats)
                    if isinstance(full_article['source'], dict):
                        source_name = full_article['source'].get('name', '')
                    else:
                        source_name = full_article['source']
                    
                    # Use the appropriate date field
                    published_date = full_article.get('publishedAt', full_article.get('published_at', ''))
                    
                    # Get description content, ensuring we have at least some text
                    description = full_article.get('description', '')
                    if not description and 'content' in full_article:
                        description = full_article['content']
                    if not description:
                        description = "No content available. Using title only."
                    
                    article_info.append(
                        f"ARTICLE {article_number} ({category.upper()}):\n"
                        f"Title: {full_article['title']}\n"
                        f"Source: {source_name}\n"
                        f"URL: {full_article['url']}\n"
                        f"Date: {published_date}\n"
                        f"Content: {description}\n\n"
                    )
                    article_number += 1
                    break
            else:
                # If we didn't find the full article, use what we have from the ranked article
                article_info.append(
                    f"ARTICLE {article_number} ({category.upper()}):\n"
                    f"Title: {article['title']}\n"
                    f"Source: {article['source']}\n"
                    f"URL: {article['url']}\n"
                    f"Date: {article['published_at']}\n"
                    f"Content: No detailed content available.\n\n"
                )
                article_number += 1
    
    # Prepare input for Gemini
    input_text = f"""USER QUERY: {query}

IMPORTANT INSTRUCTIONS:
- Group sources by their categories with clear headings (e.g., UNBIASED SOURCES, CATEGORY 1 SOURCES)
- List UP TO 5 URLs under EACH category heading
- Each category should have its OWN numbering from 1-5 (restart at 1 for each category)
- Show up to 5 sources PER CATEGORY (not 5 total)
- Format each source as: #1. source.com (date) - URL: https://source.com/article

{''.join(article_info)}"""
    
    try:
        # Initialize Gemini client and generate summary
        model = genai.GenerativeModel(model_name)
        
        generation_config = genai.GenerationConfig(
            temperature=0.2,  # Moderate temperature for factual but natural summary
        )
        
        # Get additional instructions to format the output with clear source categorization
        post_processing_instructions = """
Please ensure your final output follows these formatting guidelines:
1. SUMMARY section should be at the top
2. KEY FACTS section should follow the summary
3. DIFFERENT PERSPECTIVES section should be after key facts
4. SOURCES BY CATEGORY section should:
   - Group sources by their categories (e.g., UNBIASED SOURCES, CATEGORY 1 SOURCES, etc.)
   - List each category as a separate heading in ALL CAPS
   - Show UP TO 5 URLs clearly under each category heading
   - Each category should have its OWN numbering from 1-5 (restart at 1 for each category)
   - Show the MOST RELEVANT sources from each category
"""

        # Prepare the prompt with formatting instructions
        prompt_with_formatting = f"{summarization_prompt}\n\n{post_processing_instructions}\n\n{input_text}"
        
        response = model.generate_content(
            prompt_with_formatting,
            generation_config=generation_config
        )
        
        # Format the response with consistent styling similar to the input query display in UI
        summary_text = response.text
        
        # Create formatted summary with consistent styling
        formatted_summary = f"""
MULTI-PERSPECTIVE FACTUAL SUMMARY:

{summary_text}

ANALYSIS REASONING:

{reasoning}

"""
        
        # Return the formatted summary
        return formatted_summary
        
    except Exception as e:
        error_msg = f"⚠️ Error generating summary: {e}"
        print(error_msg)
        return error_msg
