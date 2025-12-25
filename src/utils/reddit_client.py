"""
Reddit API client wrapper.
Uses Reddit's public JSON API (no authentication required).
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class RedditClient:
    """
    Wrapper for Reddit's public JSON API.
    No authentication required.
    """
    
    def __init__(self):
        """Initialize Reddit client."""
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'SocialMediaAutomation/1.0'
        }
    
    def search_posts(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 20,
        time_filter: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Search for Reddit posts.
        
        Args:
            query: Search query
            subreddits: List of subreddit names (without r/)
            limit: Max posts to return
            time_filter: "hour", "day", "week", "month", "year", "all"
            
        Returns:
            List of post dictionaries
        """
        all_posts = []
        
        if subreddits:
            # Get top posts from each subreddit
            # Since we're already targeting topic-specific subreddits,
            # just get top posts without strict filtering
            for subreddit in subreddits:
                posts = self.get_top_posts(subreddit, limit=limit // len(subreddits) + 5, time_filter=time_filter)
                all_posts.extend(posts)
        else:
            # Search across all of Reddit
            url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': limit,
                't': time_filter,
                'sort': 'top'
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for child in data.get('data', {}).get('children', []):
                    post_data = child.get('data', {})
                    all_posts.append(self._parse_post(post_data))
                    
            except Exception as e:
                print(f"   ⚠️  Reddit search error: {str(e)}")
        
        return all_posts
    
    def get_top_posts(
        self,
        subreddit_name: str,
        limit: int = 20,
        time_filter: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get top posts from a subreddit.
        
        Args:
            subreddit_name: Subreddit name (without r/)
            limit: Max posts to return
            time_filter: "hour", "day", "week", "month", "year", "all"
            
        Returns:
            List of post dictionaries
        """
        url = f"{self.base_url}/r/{subreddit_name}/top.json"
        params = {
            'limit': min(limit, 100),
            't': time_filter
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for child in data.get('data', {}).get('children', []):
                post_data = child.get('data', {})
                posts.append(self._parse_post(post_data))
            
            return posts
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print(f"   ⚠️  Subreddit r/{subreddit_name} not found")
            else:
                print(f"   ⚠️  HTTP {e.response.status_code} for r/{subreddit_name}")
            return []
        except Exception as e:
            print(f"   ⚠️  Error fetching r/{subreddit_name}: {str(e)}")
            return []
    
    def _parse_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Reddit post data.
        
        Args:
            post_data: Post data from Reddit JSON
            
        Returns:
            Parsed post dictionary
        """
        # Calculate engagement score
        score = post_data.get('score', 0)
        num_comments = post_data.get('num_comments', 0)
        engagement_score = score + (num_comments * 2)
        
        # Get post content
        title = post_data.get('title', '')
        selftext = post_data.get('selftext', '')
        content = title
        if selftext:
            content += f"\n\n{selftext[:500]}"
        
        return {
            'post_id': post_data.get('id', ''),
            'title': title,
            'content': content,
            'author': post_data.get('author', 'deleted'),
            'subreddit': post_data.get('subreddit', 'unknown'),
            'url': post_data.get('url', ''),
            'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
            'score': score,
            'num_comments': num_comments,
            'engagement_score': engagement_score,
            'created_at': datetime.fromtimestamp(post_data.get('created_utc', 0)),
            'is_self': post_data.get('is_self', False)
        }
    
    def get_relevant_subreddits(self, topic: str) -> List[str]:
        """
        Suggest relevant subreddits for a topic.
        
        Args:
            topic: Topic to find subreddits for
            
        Returns:
            List of subreddit names
        """
        # Mapping of topics to relevant subreddits
        subreddit_map = {
            'ai': ['artificial', 'MachineLearning', 'OpenAI', 'ChatGPT', 'singularity'],
            'crypto': ['CryptoCurrency', 'Bitcoin', 'ethereum', 'CryptoMarkets'],
            'technology': ['technology', 'tech', 'gadgets', 'Futurology'],
            'politics': ['politics', 'worldnews', 'news'],
            'business': ['business', 'Economics', 'stocks', 'investing'],
            'science': ['science', 'EverythingScience', 'askscience'],
            'programming': ['programming', 'coding', 'learnprogramming', 'webdev'],
            'gaming': ['gaming', 'Games', 'pcgaming'],
            'sports': ['sports', 'nfl', 'nba', 'soccer'],
        }
        
        # Try to match topic to known categories
        topic_lower = topic.lower()
        for key, subreddits in subreddit_map.items():
            if key in topic_lower or topic_lower in key:
                return subreddits[:3]  # Return top 3
        
        # Default: use the topic as subreddit name + news + worldnews
        return ['news', 'worldnews']
