"""
Twitter/X Drafting Agent.
Creates engaging tweets from summarized insights.
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from ..database import DatabaseManager
from ..database.models import DraftStatus
from ..workflow.state import WorkflowStep


class DraftingAgent(BaseAgent):
    """
    Agent that creates engaging Twitter/X posts from insights.
    Handles character limits, hashtags, and viral formatting.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize drafting agent.
        
        Args:
            db_manager: Database manager
        """
        super().__init__(temperature=0.7)  # Higher temp for creativity
        self.db_manager = db_manager
        self.max_length = 280  # Twitter character limit
    
    def get_system_prompt(self) -> str:
        """Get system prompt for tweet drafting."""
        return """You are an expert social media content creator specializing in viral Twitter/X posts.

Given a topic, summary, and key trends, create an engaging tweet that:
- Uses most of the 280 character limit (aim for 220-280 characters)
- Captures attention in the first line
- Includes multiple insights or trends
- Uses 2-3 relevant hashtags
- Is informative and shareable
- Has a clear hook or insight
- Uses emojis strategically (1-2 max)

Guidelines:
- Start with a hook (question, stat, or bold statement)
- Pack in multiple insights - use the full character limit!
- Be concise but comprehensive
- Avoid corporate jargon
- Make it feel authentic and timely
- Include a call-to-action or thought-provoking question

Return ONLY the tweet text, nothing else. No quotes, no explanations, just the tweet."""
    
    def _create_draft(self, topic: str, summary: str, key_trends: list, tone: str = "informative") -> str:
        """
        Create tweet draft using LLM.
        
        Args:
            topic: Topic of the tweet
            summary: Summary from insights
            key_trends: List of key trends
            tone: Desired tone
            
        Returns:
            Tweet text
        """
        trends_text = "\n".join([f"- {trend}" for trend in key_trends[:3]])
        
        prompt = f"""Topic: {topic}
Tone: {tone}

Summary: {summary}

Key Trends:
{trends_text}

Create an engaging tweet that uses most of the 280 character limit (aim for 220-280 chars). Include multiple insights:"""
        
        try:
            tweet = self.invoke_llm(prompt).strip()
            
            # Remove quotes if LLM added them
            if tweet.startswith('"') and tweet.endswith('"'):
                tweet = tweet[1:-1]
            if tweet.startswith("'") and tweet.endswith("'"):
                tweet = tweet[1:-1]
            
            # Ensure it's within character limit
            if len(tweet) > self.max_length:
                print(f"   ⚠️  Tweet too long ({len(tweet)} chars), truncating...")
                tweet = tweet[:self.max_length-3] + "..."
            
            return tweet
            
        except Exception as e:
            print(f"   ⚠️  Draft creation failed: {str(e)}")
            # Fallback: create simple tweet from summary
            fallback = f"{summary[:250]} #{topic.replace(' ', '')}"
            return fallback[:self.max_length]
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process workflow state to create tweet draft.
        
        Args:
            state: Workflow state with summary and insights
            
        Returns:
            Updated state with draft_content
        """
        topic = state.get("topic", "")
        summary = state.get("summary", "")
        key_trends = state.get("key_trends", [])
        tone = state.get("tone", "informative")
        workflow_id = state.get("workflow_id")
        
        if not summary:
            state["error"] = "No summary available for drafting"
            return state
        
        print(f"\n✍️  Drafting Twitter/X post about: {topic}")
        print(f"   Tone: {tone}")
        
        # Create draft
        print("   💭 Generating engaging tweet...")
        draft_content = self._create_draft(topic, summary, key_trends, tone)
        
        print(f"   ✅ Draft created ({len(draft_content)} characters)")
        
        # Update state
        state["draft_content"] = draft_content
        state["draft_version"] = 1
        state["current_step"] = WorkflowStep.DRAFT
        
        # Save to database
        if workflow_id and self.db_manager:
            try:
                with self.db_manager.get_session() as session:
                    from ..database.models import Draft
                    draft = Draft(
                        workflow_id=workflow_id,
                        content=draft_content,
                        version=1,
                        status=DraftStatus.DRAFT
                    )
                    session.add(draft)
                    session.flush()
                    session.refresh(draft)
                    draft_id = draft.id
                    session.expunge(draft)
                
                state["draft_id"] = draft_id
                print("   ✅ Draft saved to database")
            except Exception as e:
                print(f"   ⚠️  Error saving draft: {str(e)}")
        
        return state
    
    def create_revision(self, state: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Create revised draft based on feedback.
        
        Args:
            state: Current workflow state
            feedback: User feedback
            
        Returns:
            Updated state with new draft
        """
        topic = state.get("topic", "")
        summary = state.get("summary", "")
        key_trends = state.get("key_trends", [])
        current_draft = state.get("draft_content", "")
        version = state.get("draft_version", 1) + 1
        workflow_id = state.get("workflow_id")
        
        print(f"\n✍️  Creating revision (v{version}) based on feedback...")
        
        # Create revision prompt
        revision_prompt = f"""Current tweet: {current_draft}

User feedback: {feedback}

Topic: {topic}
Summary: {summary}

Create an improved tweet (max 280 characters) addressing the feedback:"""
        
        try:
            revised_draft = self.invoke_llm(revision_prompt).strip()
            
            # Clean up
            if revised_draft.startswith('"') and revised_draft.endswith('"'):
                revised_draft = revised_draft[1:-1]
            
            if len(revised_draft) > self.max_length:
                revised_draft = revised_draft[:self.max_length-3] + "..."
            
            state["draft_content"] = revised_draft
            state["draft_version"] = version
            
            print(f"   ✅ Revision v{version} created ({len(revised_draft)} characters)")
            
            # Save to database
            if workflow_id and self.db_manager:
                try:
                    with self.db_manager.get_session() as session:
                        from ..database.models import Draft
                        draft = Draft(
                            workflow_id=workflow_id,
                            content=revised_draft,
                            version=version,
                            status=DraftStatus.DRAFT
                        )
                        session.add(draft)
                        session.flush()
                        session.refresh(draft)
                        draft_id = draft.id
                        session.expunge(draft)
                    
                    state["draft_id"] = draft_id
                except Exception as e:
                    print(f"   ⚠️  Error saving revision: {str(e)}")
            
            return state
            
        except Exception as e:
            print(f"   ⚠️  Revision failed: {str(e)}")
            state["error"] = f"Failed to create revision: {str(e)}"
            return state
