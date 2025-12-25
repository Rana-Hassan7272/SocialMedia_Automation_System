"""
Summarization Agent.
Generates insights and summaries from filtered research results.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..database import DatabaseManager
from ..workflow.state import WorkflowStep


class SummarizationAgent(BaseAgent):
    """
    Agent that summarizes filtered posts into actionable insights.
    Extracts key trends, patterns, and expert opinions.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize summarization agent.
        
        Args:
            db_manager: Database manager
        """
        super().__init__(temperature=0.5)  # Balanced for creative summarization
        self.db_manager = db_manager
    
    def get_system_prompt(self) -> str:
        """Get system prompt for summarization."""
        return """You are an expert content analyst and summarizer.

Given a topic and a list of Reddit posts, create a comprehensive summary with:
1. **Summary**: 2-3 sentence overview of the main discussion
2. **Key Trends**: 3-5 bullet points of emerging trends or patterns
3. **Expert Opinions**: Notable perspectives or insights from the posts

Guidelines:
- Be concise and informative
- Focus on actionable insights
- Highlight what's newsworthy or interesting
- Use clear, engaging language

Return your analysis in this JSON format:
{
    "summary": "2-3 sentence overview",
    "key_trends": [
        "Trend 1",
        "Trend 2",
        "Trend 3"
    ],
    "expert_opinions": [
        "Opinion 1",
        "Opinion 2"
    ]
}

Return ONLY the JSON object, nothing else."""
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process workflow state to generate insights.
        
        Args:
            state: Workflow state with filtered_tweets
            
        Returns:
            Updated state with summary and insights
        """
        topic = state.get("topic", "")
        filtered_posts = state.get("filtered_tweets", [])
        workflow_id = state.get("workflow_id")
        
        if not filtered_posts:
            state["error"] = "No filtered posts to summarize"
            return state
        
        print(f"\n📝 Summarizing {len(filtered_posts)} posts about: {topic}")
        
        # Prepare posts for summarization
        posts_text = []
        for i, post in enumerate(filtered_posts, 1):
            posts_text.append(f"{i}. [{post['subreddit']}] {post['title']}")
            if post.get('content') and post['content'] != post['title']:
                # Add first 200 chars of content
                content_preview = post['content'].replace(post['title'], '').strip()[:200]
                if content_preview:
                    posts_text.append(f"   {content_preview}...")
        
        posts_summary = "\n".join(posts_text)
        prompt = f"Topic: {topic}\n\nPosts:\n{posts_summary}\n\nGenerate insights:"
        
        try:
            print("   💭 Analyzing posts and generating insights...")
            response = self.invoke_llm(prompt)
            
            # Extract JSON from markdown if needed
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            import json
            insights = json.loads(response)
            
            # Update state
            state["summary"] = insights.get("summary", "")
            state["key_trends"] = insights.get("key_trends", [])
            state["expert_opinions"] = insights.get("expert_opinions", [])
            state["current_step"] = WorkflowStep.SUMMARIZE
            
            print(f"   ✅ Generated summary and {len(state['key_trends'])} key trends")
            
            # Save to database
            if workflow_id and self.db_manager:
                try:
                    self.db_manager.create_insight(
                        workflow_id=workflow_id,
                        summary=state["summary"],
                        key_trends="\n".join(state["key_trends"]),
                        expert_opinions="\n".join(state["expert_opinions"])
                    )
                    print("   ✅ Saved insights to database")
                except Exception as e:
                    print(f"   ⚠️  Error saving insights: {str(e)}")
            
            return state
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"   ⚠️  Summarization failed: {str(e)}")
            state["error"] = f"Failed to generate insights: {str(e)}"
            return state
