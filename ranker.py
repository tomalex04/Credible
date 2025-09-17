"""
ranker.py - Module for ranking news articles based on relevance to query

This module uses SentenceTransformers to create embeddings and rank articles
based on their semantic similarity to the user query.
"""

import os
import torch
from sentence_transformers import SentenceTransformer

# Global model cache dictionary to store loaded models
_MODEL_CACHE = {}

# Check if CUDA is available
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {DEVICE}")

class ArticleRanker:
    """A class to rank articles based on their relevance to a query using embeddings."""
    
    def __init__(self, model_name=None):
        """
        Initialize the ranker with a SentenceTransformer model.
        
        Args:
            model_name (str): Name of the SentenceTransformer model to use
        """
        # Get model name or use default
        self.model_name = model_name or 'intfloat/multilingual-e5-base'
        
        try:
            # Check if model is already in cache
            if self.model_name in _MODEL_CACHE:
                self.model = _MODEL_CACHE[self.model_name]
                print(f"Using cached model: {self.model_name} on {DEVICE}")
            else:
                # Load model and add to cache, automatically using the appropriate device
                self.model = SentenceTransformer(self.model_name, device=str(DEVICE))
                _MODEL_CACHE[self.model_name] = self.model
                print(f"Loaded model: {self.model_name} on {DEVICE}")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            print("Make sure you have installed sentence-transformers:")
            print("pip install sentence-transformers")
            raise
    
    def create_embeddings(self, query, article_texts):
        """
        Create embeddings for the query and article texts.
        
        Args:
            query (str): The user's query/news statement
            article_texts (list): List of article text strings
            
        Returns:
            tuple: (query_embedding, article_embeddings)
        """
        # Use convert_to_tensor=True to get tensors that will be on the right device (CUDA or CPU)
        query_embedding = self.model.encode(query, convert_to_tensor=True, device=DEVICE)
        article_embeddings = self.model.encode(article_texts, convert_to_tensor=True, device=DEVICE)
        return query_embedding, article_embeddings
    
    def calculate_similarities(self, query_embedding, article_embeddings):
        """
        Calculate cosine similarity between query and article embeddings.
        
        Args:
            query_embedding: Tensor of query embedding
            article_embeddings: Tensor of article embeddings
            
        Returns:
            list: List of similarity scores
        """
        similarities = torch.nn.functional.cosine_similarity(
            query_embedding.unsqueeze(0), article_embeddings
        )
        return similarities.tolist()
    
    def get_top_articles(self, similarities, articles, top_n, min_threshold):
        """
        Get the top N articles based on similarity scores.
        
        Args:
            similarities (list): List of similarity scores
            articles (list): List of article dictionaries
            top_n (int): Number of top results to return
            min_threshold (float): Minimum similarity threshold
            
        Returns:
            list: List of indices of top articles
        """
        # Create a list of (index, similarity) tuples and sort by similarity (descending)
        indexed_similarities = list(enumerate(similarities))
        indexed_similarities.sort(key=lambda x: x[1], reverse=True)
        
        top_indices = []
        
        # Filter results by threshold
        for idx, score in indexed_similarities:
            if score >= min_threshold and len(top_indices) < top_n:
                top_indices.append(idx)
        
        return top_indices
    
    def format_results(self, top_indices, similarities, articles):
        """
        Format the results with rank and similarity score.
        
        Args:
            top_indices (list): List of indices of top articles
            similarities (list): List of similarity scores
            articles (list): List of article dictionaries
            
        Returns:
            list: List of dictionaries with ranked articles and their similarity scores
        """
        result = []
        
        for i, idx in enumerate(top_indices, 1):
            similarity_score = similarities[idx]
            article = articles[idx]
            
            # Extract source name (handling both object and string formats)
            if isinstance(article['source'], dict):
                source_name = article['source'].get('name', '')
            else:
                source_name = article['source']
            
            # Use publishedAt if available, otherwise use published_at
            published_at = article.get('publishedAt', article.get('published_at', ''))
            
            result.append({
                'rank': i,
                'title': article['title'],
                'source': source_name,
                'url': article['url'],
                'similarity_score': similarity_score,
                'published_at': published_at
            })
        
        return result
