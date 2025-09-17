#!/home/tom/miniconda3/envs/fake_news_detection/bin/python
"""
main.py - Server for the Fake News Detection system

This script creates a Flask server that exposes API endpoints to:
1. Take user input (news query) from the UI
2. Process the request through the fake news detection pipeline
3. Return the results to the UI for display
"""

import os
import json
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import required functions from modules
from gdelt_api import (
    fetch_articles_from_gdelt,
    filter_by_whitelisted_domains,
    normalize_gdelt_articles
)
from ranker import ArticleRanker
from gdelt_query_builder import generate_query, GEMINI_MODEL
import bias_analyzer
from google_search import google_search

# Global variable for embedding model caching across requests
print("Preloading embedding model for faster request processing...")
# Preload the embedding model at server startup
global_ranker = ArticleRanker()


# The function has been removed since bias category descriptions are provided directly by the Gemini model
# and stored in the bias_analysis["descriptions"] dictionary


def format_results(query, ranked_articles):
    """
    Format the ranked results in a structured way for the UI.
    
    Args:
        query (str): The original query
        ranked_articles (list): List of ranked article dictionaries
        
    Returns:
        dict: Dictionary with formatted results
    """
    result = {}
    
    if not ranked_articles:
        result = {
            "status": "no_results",
            "message": "⚠️ No news found. Possibly Fake.",
            "details": "No reliable sources could verify this information.",
            "articles": []
        }
    else:
        # Get display configuration from environment variables
        show_scores = os.getenv('SHOW_SIMILARITY_SCORES', 'true').lower() == 'true'
        show_date = os.getenv('SHOW_PUBLISH_DATE', 'true').lower() == 'true'
        show_url = os.getenv('SHOW_URL', 'true').lower() == 'true'
        
        formatted_articles = []
        for article in ranked_articles:
            formatted_article = {
                "rank": article['rank'],
                "title": article['title'],
                "source": article['source']
            }
            
            if show_scores:
                formatted_article["similarity_score"] = round(article['similarity_score'], 4)
                
            if show_url:
                formatted_article["url"] = article['url']
                
            if show_date:
                formatted_article["published_at"] = article['published_at']
                
            formatted_articles.append(formatted_article)
        
        result = {
            "status": "success",
            "message": f"✅ Found {len(ranked_articles)} relevant articles for: '{query}'",
            "articles": formatted_articles,
            "footer": "If the news matches these reliable sources, it's likely true. If it contradicts them or no sources are found, it might be fake."
        }
    
    return result


def remove_duplicates(articles):
    """
    Remove duplicate articles based on URL.
    
    Args:
        articles (list): List of article dictionaries
        
    Returns:
        list: List with duplicate articles removed
    """
    unique_urls = set()
    unique_articles = []
    
    for article in articles:
        if article['url'] not in unique_urls:
            unique_urls.add(article['url'])
            unique_articles.append(article)
    
    return unique_articles


# This function has been removed since Gemini is a cloud API service
# that does not require local caching - models are instantiated as needed


def main():
    """Main function to run the fake news detection pipeline as a server."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__, static_folder='static')
    CORS(app)  # Enable CORS for all routes
    
    @app.route('/static/')
    def index():
        """Serve the main page."""
        return app.send_static_file('front.html')

    
    @app.route('/api/detect', methods=['POST'])
    def detect_fake_news():
        """API endpoint to check if news is potentially fake."""
        # Start timing the request processing
        start_time = time.time()
        
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Please provide a news statement to verify."
            })
        
        # =====================================================
        # 1. Input Handling
        # =====================================================
        # Generate three variations of the query using Gemini
        query_variations = generate_query(query)
        
        # Check if the query was flagged as inappropriate
        if query_variations == ["INAPPROPRIATE_QUERY"]:
            return jsonify({
                "status": "error",
                "message": "I cannot provide information on this topic as it appears to contain sensitive or inappropriate content."
            })
        
        # =====================================================
        # 2. Data Fetching
        # =====================================================
        # Fetch articles from GDELT API for each query variation
        all_articles = []
        
        # First, fetch Google search results using the original query
        # print(f"Fetching Google search results for: {query}")
        # google_results = google_search(query, num_results=25)
        # if google_results:
        #     all_articles.extend(google_results)
        #     print(f"Added {len(google_results)} Google search results to articles")
        
        # Then fetch GDELT results for each query variation
        for query_var in query_variations:
            articles = fetch_articles_from_gdelt(query_var)
            if articles:
                all_articles.extend(articles)
        
        # After the loop, check if any articles were found
        if not all_articles:
            return jsonify({
                "status": "no_results",
                "message": "No articles found on this topic.",
                "details": "No reliable sources could be found covering this information.",
                "articles": []
            })
        
        # Store unique articles in a set to ensure uniqueness
        unique_articles = remove_duplicates(all_articles)
        
        # Apply domain whitelist filtering if enabled in .env
        use_whitelist_only = os.getenv('USE_WHITELIST_ONLY', 'false').lower() == 'true'
        if use_whitelist_only:
            print(f"Filtering articles to only include whitelisted domains...")
            unique_articles = filter_by_whitelisted_domains(unique_articles)
            print(f"After whitelist filtering: {len(unique_articles)} articles remain")
        
        # Normalize the articles to a standard format
        normalized_articles = normalize_gdelt_articles(unique_articles)
        
        if not normalized_articles:
            return jsonify(format_results(query, []))
        
        # =====================================================
        # 3. Embedding & Ranking
        # =====================================================
        # Initialize the ranker with model from environment variable
        model_name = os.getenv('SIMILARITY_MODEL', 'intfloat/multilingual-e5-base')
        
        # Use global ranker if it matches the requested model, otherwise create a new instance
        if global_ranker.model_name == model_name:
            ranker = global_ranker
        else:
            ranker = ArticleRanker(model_name)
        
        # Get TOP_K_ARTICLES from .env file
        TOP_K_ARTICLES = int(os.getenv('TOP_K_ARTICLES', 250))
        min_threshold = float(os.getenv('MIN_SIMILARITY_THRESHOLD', 0.1))
        
        # Prepare article texts for embedding
        article_texts = [f"{article['title']} {article['description'] or ''}" for article in normalized_articles]
        
        # Create embeddings and calculate similarities
        query_embedding, article_embeddings = ranker.create_embeddings(query, article_texts)
        similarities = ranker.calculate_similarities(query_embedding, article_embeddings)
        
        # Get top articles based on similarity
        top_indices = ranker.get_top_articles(similarities, normalized_articles, TOP_K_ARTICLES, min_threshold)
        top_articles = ranker.format_results(top_indices, similarities, normalized_articles)
        
        # =====================================================
        # 4. Bias Categorization
        # =====================================================
        # Extract outlet names from the TOP_K_ARTICLES
        # In top_articles, the source is already extracted as a string
        outlet_names = [article['source'] for article in top_articles]
        unique_outlets = list(set(outlet_names))
        print(f"Analyzing {len(unique_outlets)} unique news outlets for bias...")
        
        # Analyze bias using Gemini - send just the outlet names, not the whole articles
        bias_analysis = bias_analyzer.analyze_bias(query, unique_outlets, GEMINI_MODEL)
        
        # =====================================================
        # 5. Category Embeddings
        # =====================================================
        print("\n" + "=" * 80)
        print("EMBEDDING VECTORS BY BIAS CATEGORY")
        print("=" * 80)
        
        # Create embedding vectors for each bias category
        # 1. Group articles based on their outlet's bias category
        # 2. Create an embedding vector for each category using ONLY article titles
        # 3. Rank articles within each category by similarity to query
        category_rankings = bias_analyzer.categorize_and_rank_by_bias(
            query, normalized_articles, bias_analysis, ranker, min_threshold
        )
        
        # =====================================================
        # 6. Top N Selection per Category
        # =====================================================
        # Get TOP_N_PER_CATEGORY from .env file (default: 5)
        TOP_N_PER_CATEGORY = int(os.getenv('TOP_N_PER_CATEGORY', 5))
        
        # Get total counts of articles per category before filtering
        category_article_counts = {
            category: len(articles) 
            for category, articles in category_rankings.items() 
            if category not in ["descriptions", "reasoning"]
        }
        
        # For each bias category, select the top N articles
        # These are the most relevant articles within each bias perspective
        filtered_category_rankings = {}
        for category, articles in category_rankings.items():
            # Skip non-category keys like "descriptions" or "reasoning"
            if category in ["descriptions", "reasoning"]:
                continue
                
            filtered_category_rankings[category] = articles[:TOP_N_PER_CATEGORY]
            
            # Only print if there are articles in this category
            if len(filtered_category_rankings[category]) > 0:
                print(f"\n===== Top {len(filtered_category_rankings[category])} articles from {category} category =====")
                
                # Print detailed information about each selected article
                for i, article in enumerate(filtered_category_rankings[category], 1):
                    print(f"Article #{i}:")
                    print(f"  Title: {article['title']}")
                    print(f"  Source: {article['source']}")
                    print(f"  Similarity Score: {article['similarity_score']:.4f}")
                    print(f"  Rank: {article['rank']}")
                    print(f"  URL: {article['url']}")
                    print(f"  Published: {article['published_at']}")
                    print("-" * 50)
        
        # =====================================================
        # 7. Summarization
        # =====================================================
        # Generate summary from articles in all categories
        print("\nGenerating factual summary using top articles from all categories...")
        
        # Pass the original bias_analysis to include the reasoning in the summary
        # We need to add the reasoning to filtered_category_rankings since that's what gets passed to generate_summary
        filtered_category_rankings["reasoning"] = bias_analysis.get("reasoning", "No reasoning provided")
        
        # Call the bias_analyzer's generate_summary function with articles from all categories
        summary = bias_analyzer.generate_summary(
            query, 
            normalized_articles, 
            filtered_category_rankings, 
            GEMINI_MODEL
        )
        
        # Print the summary to terminal (already includes its own formatting)
        print(summary)
        
        # Prepare response with ONLY the combined summary (reasoning already appended at end)
        # Removed separate 'reasoning' key to avoid it showing at the top in the UI
        result = {
            "summary": summary
        }
        
        return jsonify(result)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """API endpoint to check if the server is running."""
        return jsonify({
            "status": "ok", 
            "message": "Fake News Detection API is running"
        })
    
    # Get port from environment variable or use default 5000
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"Starting Fake News Detection API server on port {port}...")
    # Start the Flask server
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == "__main__":
    main()
