"""
Research Agent with ReAct reasoning.
Searches Reddit for relevant content using think-act-observe loop.
"""

import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..database import DatabaseManager
from ..utils import RedditClient
from ..workflow.state import WorkflowStep


class ResearchAgent(BaseAgent):
    """
    ReAct-style agent that searches Reddit for relevant posts.
    Uses reasoning loop: Think → Act → Observe → Repeat
    """
    
    def __init__(self, db_manager: DatabaseManager, reddit_client: RedditClient):
        """
        Initialize research agent.
        
        Args:
            db_manager: Database manager for storing results
            reddit_client: Reddit API client
        """
        super().__init__(temperature=0.4)  # Balanced for reasoning
        self.db_manager = db_manager
        self.reddit_client = reddit_client
    
    def get_system_prompt(self) -> str:
        """Get system prompt for ReAct reasoning."""
        return """You are a research planning agent. Your job is to identify the best Reddit search strategy.

Given a topic and scope, determine:
1. Relevant subreddits to search
2. Search queries to use
3. Time filter (hour/day/week)

Return ONLY valid JSON with this format:
{
    "subreddits": ["subreddit1", "subreddit2"],
    "search_query": "optimized search query",
    "time_filter": "day",
    "reasoning": "brief explanation"
}

Examples:
- Topic: "AI", Scope: "today"
  Output: {"subreddits": ["artificial", "MachineLearning", "OpenAI"], "search_query": "AI latest", "time_filter": "day", "reasoning": "Focus on AI-focused communities for recent discussions"}

- Topic: "cryptocurrency", Scope: "this week"
  Output: {"subreddits": ["CryptoCurrency", "Bitcoin"], "search_query": "crypto news", "time_filter": "week", "reasoning": "Top crypto subreddits for weekly trends"}

Return ONLY the JSON, nothing else."""
    
    def _generate_research_strategy(self, topic: str, scope: str) -> Dict[str, Any]:
        """
        Generate research strategy using LLM.
        
        Args:
            topic: Research topic
            scope: Research scope
            
        Returns:
            Dictionary with subreddits, query, and time filter
        """
        prompt = f"Topic: {topic}\nScope: {scope}\n\nGenerate research strategy:"
        
        try:
            response = self.invoke_llm(prompt)
            strategy = json.loads(response)
            
            # Validate and set defaults
            if "subreddits" not in strategy or not strategy["subreddits"]:
                strategy["subreddits"] = self.reddit_client.get_relevant_subreddits(topic)
            if "search_query" not in strategy:
                strategy["search_query"] = topic
            if "time_filter" not in strategy:
                strategy["time_filter"] = "day"
            
            return strategy
            
        except (json.JSONDecodeError, KeyError):
            # Fallback strategy
            return {
                "subreddits": self.reddit_client.get_relevant_subreddits(topic),
                "search_query": topic,
                "time_filter": "day"
            }
    
    def _search_reddit(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search Reddit using strategy.
        
        Args:
            strategy: Research strategy dict
            
        Returns:
            List of post dictionaries
        """
        try:
            posts = self.reddit_client.search_posts(
                query=strategy["search_query"],
                subreddits=strategy["subreddits"],
                limit=30,
                time_filter=strategy["time_filter"]
            )
            return posts
        except Exception as e:
            print(f"   ⚠️  Reddit search failed: {str(e)}")
            return []
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process workflow state using ReAct reasoning.
        
        Args:
            state: Workflow state with topic and scope
            
        Returns:
            Updated state with raw_tweets (keeping name for compatibility)
        """
        topic = state.get("topic", "")
        scope = state.get("scope", "latest")
        workflow_id = state.get("workflow_id")
        
        if not topic:
            state["error"] = "No topic provided for research"
            return state
        
        print(f"\n🔍 Researching: {topic} ({scope})")
        
        # Step 1: THINK - Generate research strategy
        print("   💭 Thinking: Generating research strategy...")
        strategy = self._generate_research_strategy(topic, scope)
        print(f"   📝 Subreddits: {strategy['subreddits']}")
        print(f"   📝 Query: {strategy['search_query']}")
        print(f"   📝 Time filter: {strategy['time_filter']}")
        
        # Step 2: ACT - Search Reddit
        print(f"   🔎 Searching Reddit...")
        posts = self._search_reddit(strategy)
        print(f"   ✅ Found {len(posts)} posts")
        
        # Step 3: OBSERVE - Sort by engagement
        sorted_posts = sorted(
            posts,
            key=lambda p: p['engagement_score'],
            reverse=True
        )
        
        print(f"   📊 Total posts: {len(sorted_posts)}")
        
        # Save to database (reusing research_results table structure)
        if workflow_id and self.db_manager:
            for post in sorted_posts:
                try:
                    self.db_manager.create_research_result(
                        workflow_id=workflow_id,
                        tweet_id=post['post_id'],  # Using post_id as tweet_id
                        author=post['author'],
                        author_username=post['subreddit'],  # Subreddit as username
                        content=post['content'],
                        engagement_score=post['engagement_score'],
                        likes=post['score'],
                        retweets=0,  # Reddit doesn't have retweets
                        replies=post['num_comments'],
                        tweet_created_at=post['created_at']
                    )
                except Exception:
                    # Skip duplicates or errors
                    pass
        
        # Update state (keeping "raw_tweets" name for compatibility with later agents)
        state["raw_tweets"] = sorted_posts
        state["current_step"] = WorkflowStep.RESEARCH
        
        return state
