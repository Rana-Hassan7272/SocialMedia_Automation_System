"""
Workflow state management for LangGraph.
Defines the state that flows through the agent workflow.
"""

from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum


class WorkflowStep(str, Enum):
    """Workflow step enumeration."""
    START = "start"
    INTENT_UNDERSTANDING = "intent_understanding"
    RESEARCH = "research"
    FILTER = "filter"
    SUMMARIZE = "summarize"
    DRAFT = "draft"
    HUMAN_REVIEW = "human_review"
    PUBLISH = "publish"
    END = "end"


class WorkflowState(TypedDict, total=False):
    """
    State that flows through the LangGraph workflow.
    Each agent reads from and writes to this state.
    """
    
    # Workflow metadata
    workflow_id: int
    current_step: WorkflowStep
    
    # User input
    user_query: str
    
    # Intent understanding
    topic: Optional[str]
    scope: Optional[str]
    tone: Optional[str]
    
    # Research results
    raw_tweets: Optional[List[Dict[str, Any]]]
    
    # Filtered and ranked tweets
    filtered_tweets: Optional[List[Dict[str, Any]]]
    
    # Summarized insights
    summary: Optional[str]
    key_trends: Optional[str]
    
    # Draft content
    draft_content: Optional[str]
    draft_version: int
    
    # Human feedback
    feedback_type: Optional[str]  # "approve", "reject", "modify"
    feedback_comments: Optional[str]
    
    # Publishing
    published: bool
    tweet_url: Optional[str]
    
    # Error handling
    error: Optional[str]


def create_initial_state(user_query: str, workflow_id: int) -> WorkflowState:
    """
    Create initial workflow state.
    
    Args:
        user_query: User's input query
        workflow_id: Database workflow ID
        
    Returns:
        Initial WorkflowState
    """
    return WorkflowState(
        workflow_id=workflow_id,
        current_step=WorkflowStep.START,
        user_query=user_query,
        draft_version=0,
        published=False
    )
