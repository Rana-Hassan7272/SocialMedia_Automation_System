"""
Filtering Agent.
Filters and ranks research results by relevance and quality.
"""

import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..database import DatabaseManager
from ..workflow.state import WorkflowStep


class FilteringAgent(BaseAgent):
    """
    Agent that filters and ranks research results.
    Removes low-quality content and scores by relevance.
    """
    
    def __init__(self, db_manager: DatabaseManager, top_k: int = 8):
        """
        Initialize filtering agent.
        
        Args:
            db_manager: Database manager
            top_k: Number of top posts to keep
        """
        super().__init__(temperature=0.3)  # Lower temp for consistent scoring
        self.db_manager = db_manager
        self.top_k = top_k
    
    def get_system_prompt(self) -> str:
        """Get system prompt for relevance scoring."""
        return """You are a content quality and relevance evaluator.

Given a topic and a list of Reddit posts, score each post's relevance from 0.0 to 1.0.

Scoring criteria:
- **1.0**: Highly relevant, directly addresses the topic, high quality
- **0.7-0.9**: Relevant, good quality, useful information
- **0.4-0.6**: Somewhat relevant, moderate quality
- **0.0-0.3**: Off-topic, low quality, spam, or promotional

CRITICAL: You MUST return ONLY valid JSON. No explanations, no markdown, just pure JSON.

Format:
{
    "scores": [
        {"post_id": "abc123", "score": 0.9, "reason": "highly relevant"},
        {"post_id": "def456", "score": 0.5, "reason": "somewhat relevant"}
    ]
}

Return ONLY the JSON object, nothing else."""
    
    def _score_posts(self, topic: str, posts: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Score posts by relevance using LLM.
        
        Args:
            topic: Research topic
            posts: List of post dictionaries
            
        Returns:
            Dictionary mapping post_id to relevance score
        """
        if not posts:
            return {}
        
        # Prepare posts for LLM (limit content length)
        posts_summary = []
        for post in posts[:20]:  # Limit to 20 posts for LLM
            posts_summary.append({
                "post_id": post['post_id'],
                "title": post['title'][:200],
                "subreddit": post['subreddit']
            })
        
        prompt = f"Topic: {topic}\n\nPosts:\n{json.dumps(posts_summary, indent=2)}\n\nScore each post:"
        
        try:
            response = self.invoke_llm(prompt)
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            data = json.loads(response)
            
            # Create score mapping
            scores = {}
            for item in data.get("scores", []):
                post_id = item.get("post_id")
                score = item.get("score", 0.5)
                if post_id:
                    scores[post_id] = float(score)
            
            return scores
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"   ⚠️  Scoring failed, using engagement only: {str(e)}")
            # Fallback: return neutral scores
            return {post['post_id']: 0.5 for post in posts}
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process workflow state to filter and rank posts.
        
        Args:
            state: Workflow state with raw_tweets
            
        Returns:
            Updated state with filtered_tweets
        """
        topic = state.get("topic", "")
        raw_posts = state.get("raw_tweets", [])
        workflow_id = state.get("workflow_id")
        
        if not raw_posts:
            state["filtered_tweets"] = []
            return state
        
        print(f"\n🔍 Filtering {len(raw_posts)} posts for topic: {topic}")
        
        # Step 1: Score by relevance
        print("   💭 Scoring posts by relevance...")
        relevance_scores = self._score_posts(topic, raw_posts)
        
        # Step 2: Combine relevance + engagement
        print("   📊 Combining relevance and engagement scores...")
        scored_posts = []
        for post in raw_posts:
            post_id = post['post_id']
            relevance = relevance_scores.get(post_id, 0.5)
            
            # Normalize engagement score (0-1 range)
            max_engagement = max(p['engagement_score'] for p in raw_posts) or 1
            engagement_norm = post['engagement_score'] / max_engagement
            
            # Combined score: 60% relevance, 40% engagement
            combined_score = (relevance * 0.6) + (engagement_norm * 0.4)
            
            scored_posts.append({
                **post,
                'relevance_score': relevance,
                'combined_score': combined_score
            })
        
        # Step 3: Sort and select top K
        scored_posts.sort(key=lambda x: x['combined_score'], reverse=True)
        filtered_posts = scored_posts[:self.top_k]
        
        print(f"   ✅ Selected top {len(filtered_posts)} posts")
        
        # Step 4: Save to database
        if workflow_id and self.db_manager:
            # Get research result IDs first (avoid session issues)
            with self.db_manager.get_session() as session:
                from ..database.models import ResearchResult
                research_results = session.query(ResearchResult).filter(
                    ResearchResult.workflow_id == workflow_id
                ).all()
                
                # Create mapping of post_id to research_result_id
                post_id_to_result_id = {r.tweet_id: r.id for r in research_results}
            
            # Now save filtered content
            for rank, post in enumerate(filtered_posts, 1):
                try:
                    result_id = post_id_to_result_id.get(post['post_id'])
                    if result_id:
                        self.db_manager.create_filtered_content(
                            workflow_id=workflow_id,
                            research_result_id=result_id,
                            rank=rank,
                            relevance_score=post['relevance_score']
                        )
                except Exception as e:
                    print(f"   ⚠️  Error saving filtered content: {str(e)}")
        
        # Update state
        state["filtered_tweets"] = filtered_posts
        state["current_step"] = WorkflowStep.FILTER
        
        return state
