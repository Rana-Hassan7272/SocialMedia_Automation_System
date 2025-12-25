"""
Publishing Agent.
Handles human review and publishing to Twitter/X.
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..database import DatabaseManager
from ..database.models import DraftStatus, FeedbackType, WorkflowStatus
from ..utils import TwitterClient
from ..workflow.state import WorkflowStep


class PublishingAgent(BaseAgent):
    """
    Agent that handles human review and publishes to Twitter/X.
    Supports approve, reject, and request revision workflows.
    """
    
    def __init__(self, db_manager: DatabaseManager, twitter_client: TwitterClient):
        """
        Initialize publishing agent.
        
        Args:
            db_manager: Database manager
            twitter_client: Twitter API client
        """
        super().__init__(temperature=0.0)  # Not using LLM for publishing
        self.db_manager = db_manager
        self.twitter_client = twitter_client
    
    def get_system_prompt(self) -> str:
        """Not used for publishing agent."""
        return ""
    
    def request_human_review(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Present draft for human review.
        
        Args:
            state: Workflow state with draft
            
        Returns:
            State with review_requested flag
        """
        draft_content = state.get("draft_content", "")
        topic = state.get("topic", "")
        
        print(f"\n👤 HUMAN REVIEW REQUIRED")
        print("=" * 60)
        print(f"Topic: {topic}")
        print(f"\n📱 DRAFT TWEET:")
        print("-" * 60)
        print(draft_content)
        print("-" * 60)
        print(f"Character count: {len(draft_content)}/280\n")
        
        state["review_requested"] = True
        state["current_step"] = WorkflowStep.HUMAN_REVIEW
        
        return state
    
    def handle_approval(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle draft approval and publish to Twitter/X.
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state with publishing status
        """
        draft_content = state.get("draft_content", "")
        draft_id = state.get("draft_id")
        workflow_id = state.get("workflow_id")
        
        print(f"\n✅ Draft APPROVED - Publishing to Twitter/X...")
        
        try:
            # Publish to Twitter/X
            response = self.twitter_client.client.create_tweet(text=draft_content)
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            print(f"   ✅ Published successfully!")
            print(f"   🔗 {tweet_url}")
            
            # Update database
            if draft_id and self.db_manager:
                # Save feedback
                with self.db_manager.get_session() as session:
                    from ..database.models import Feedback, Draft
                    feedback = Feedback(
                        draft_id=draft_id,
                        feedback_type=FeedbackType.APPROVE,
                        comments="Approved for publishing"
                    )
                    session.add(feedback)
                    
                    # Update draft status
                    draft = session.get(Draft, draft_id)
                    if draft:
                        draft.status = DraftStatus.APPROVED
                
                # Save published post
                self.db_manager.create_published_post(
                    workflow_id=workflow_id,
                    draft_id=draft_id,
                    twitter_post_id=tweet_id,
                    twitter_post_url=tweet_url
                )
                
                # Update workflow status
                self.db_manager.update_workflow_status(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.COMPLETED
                )
            
            state["published"] = True
            state["tweet_id"] = tweet_id
            state["tweet_url"] = tweet_url
            state["current_step"] = WorkflowStep.PUBLISH
            
            return state
            
        except Exception as e:
            print(f"   ❌ Publishing failed: {str(e)}")
            state["error"] = f"Publishing failed: {str(e)}"
            
            # Update workflow with error
            if workflow_id and self.db_manager:
                self.db_manager.update_workflow_status(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.FAILED,
                    error_message=str(e)
                )
            
            return state
    
    def handle_rejection(self, state: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
        """
        Handle draft rejection.
        
        Args:
            state: Workflow state
            reason: Rejection reason
            
        Returns:
            Updated state
        """
        draft_id = state.get("draft_id")
        workflow_id = state.get("workflow_id")
        
        print(f"\n❌ Draft REJECTED")
        if reason:
            print(f"   Reason: {reason}")
        
        # Save feedback
        if draft_id and self.db_manager:
            with self.db_manager.get_session() as session:
                from ..database.models import Feedback, Draft
                feedback = Feedback(
                    draft_id=draft_id,
                    feedback_type=FeedbackType.REJECT,
                    comments=reason or "Rejected"
                )
                session.add(feedback)
                
                # Update draft status
                draft = session.get(Draft, draft_id)
                if draft:
                    draft.status = DraftStatus.REJECTED
            
            # Update workflow
            self.db_manager.update_workflow_status(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error_message=f"Draft rejected: {reason}"
            )
        
        state["rejected"] = True
        return state
    
    def handle_revision_request(self, state: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Handle request for draft revision.
        
        Args:
            state: Workflow state
            feedback: Revision feedback
            
        Returns:
            Updated state
        """
        draft_id = state.get("draft_id")
        
        print(f"\n🔄 Revision REQUESTED")
        print(f"   Feedback: {feedback}")
        
        # Save feedback
        if draft_id and self.db_manager:
            with self.db_manager.get_session() as session:
                from ..database.models import Feedback
                feedback_obj = Feedback(
                    draft_id=draft_id,
                    feedback_type=FeedbackType.REVISE,
                    comments=feedback
                )
                session.add(feedback_obj)
        
        state["revision_requested"] = True
        state["revision_feedback"] = feedback
        
        return state
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process publishing workflow (requests human review).
        
        Args:
            state: Workflow state
            
        Returns:
            Updated state
        """
        return self.request_human_review(state)
