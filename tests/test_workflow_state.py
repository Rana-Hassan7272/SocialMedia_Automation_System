"""
Test workflow state management.
"""

import pytest
from src.workflow.state import (
    WorkflowState,
    WorkflowStep,
    create_initial_state
)


def test_create_initial_state():
    """Test creating initial workflow state."""
    query = "Get latest AI news"
    workflow_id = 123
    
    state = create_initial_state(query, workflow_id)
    
    assert state["workflow_id"] == workflow_id
    assert state["user_query"] == query
    assert state["current_step"] == WorkflowStep.START
    assert state["draft_version"] == 0
    assert state["published"] is False


def test_workflow_steps_enum():
    """Test workflow step enumeration."""
    assert WorkflowStep.START == "start"
    assert WorkflowStep.INTENT_UNDERSTANDING == "intent_understanding"
    assert WorkflowStep.RESEARCH == "research"
    assert WorkflowStep.FILTER == "filter"
    assert WorkflowStep.SUMMARIZE == "summarize"
    assert WorkflowStep.DRAFT == "draft"
    assert WorkflowStep.HUMAN_REVIEW == "human_review"
    assert WorkflowStep.PUBLISH == "publish"
    assert WorkflowStep.END == "end"


def test_state_type():
    """Test WorkflowState is a TypedDict."""
    state = create_initial_state("test", 1)
    
    # Should be a dict
    assert isinstance(state, dict)
    
    # Should have required keys
    assert "workflow_id" in state
    assert "user_query" in state
    assert "current_step" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
