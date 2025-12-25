"""
Twitter/X API client wrapper.
Handles authentication and tweet searching.
"""

import tweepy
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config import settings


class TwitterClient:
    """
    Wrapper for Twitter/X API using Tweepy.
    Handles authentication and search operations.
    """
    
    def __init__(self):
        """Initialize Twitter API client with credentials from settings."""
        if not settings.is_twitter_configured():
            raise ValueError("Twitter API credentials not configured in .env file")
        
        # Try OAuth 2.0 first (newer, uses CLIENT_ID/CLIENT_SECRET)
        # If that fails, fall back to OAuth 1.0a (API_KEY/API_SECRET/ACCESS_TOKEN)
        try:
            # OAuth 2.0 - Client Credentials
            self.client = tweepy.Client(
                bearer_token=settings.twitter_api_key if hasattr(settings, 'twitter_bearer_token') else None,
                consumer_key=settings.twitter_api_key,
                consumer_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                wait_on_rate_limit=True
            )
        except Exception as e:
            print(f"Warning: Twitter client initialization issue: {e}")
            raise
    
    def search_tweets(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets using Twitter API v2.
        
        Args:
            query: Search query string
            max_results: Maximum number of tweets to return (10-100)
            
        Returns:
            List of tweet dictionaries with parsed data
        """
        try:
            # Search recent tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit is 100
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username', 'name'],
                expansions=['author_id']
            )
            
            if not response.data:
                return []
            
            # Create user lookup dict
            users = {}
            if response.includes and 'users' in response.includes:
                users = {user.id: user for user in response.includes['users']}
            
            # Parse tweets
            tweets = []
            for tweet in response.data:
                author = users.get(tweet.author_id)
                
                tweet_data = {
                    'tweet_id': str(tweet.id),
                    'content': tweet.text,
                    'author': author.name if author else 'Unknown',
                    'author_username': author.username if author else 'unknown',
                    'created_at': tweet.created_at,
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count'],
                    'replies': tweet.public_metrics['reply_count'],
                    'engagement_score': (
                        tweet.public_metrics['like_count'] +
                        tweet.public_metrics['retweet_count'] * 2 +
                        tweet.public_metrics['reply_count']
                    )
                }
                tweets.append(tweet_data)
            
            return tweets
            
        except tweepy.TweepyException as e:
            raise RuntimeError(f"Twitter API error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error searching tweets: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if API is properly configured."""
        return settings.is_twitter_configured()
