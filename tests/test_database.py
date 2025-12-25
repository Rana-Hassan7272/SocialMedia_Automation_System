"""
Test database initialization and basic operations.
"""

import pytest
from datetime import datetime
from src.database import DatabaseManager
from src.database.models import WorkflowStatus, DraftStatus, FeedbackType


@pytest.fixture
def db_manager():
    """Create a test database manager with in-memory database."""
    db = DatabaseManager(database_url="sqlite:///:memory:")
    db.initialize_database()
    return db


def test_database_initialization(db_manager):
    """Test that database tables are created successfully."""
    # If we get here without errors, initialization worked
    assert db_manager.engine is not None
    assert db_manager.SessionLocal is not None


def test_create_workflow(db_manager):
    """Test creating a new workflow."""
    workflow = db_manager.create_workflow(
        user_query="Get latest AI news"
    )
    
    assert workflow.id is not None
    assert workflow.user_query == "Get latest AI news"
    assert workflow.status == WorkflowStatus.PENDING
    assert workflow.created_at is not None


def test_create_intent(db_manager):
    """Test creating an intent."""
    # First create a workflow
    workflow = db_manager.create_workflow("Get crypto news")
    
    # Create intent
    intent = db_manager.create_intent(
        workflow_id=workflow.id,
        topic="cryptocurrency",
        scope="latest",
        raw_intent="Latest cryptocurrency news and trends"
    )
    
    assert intent.id is not None
    assert intent.workflow_id == workflow.id
    assert intent.topic == "cryptocurrency"
    assert intent.scope == "latest"


def test_create_research_result(db_manager):
    """Test creating a research result (tweet)."""
    workflow = db_manager.create_workflow("AI regulation news")
    
    result = db_manager.create_research_result(
        workflow_id=workflow.id,
        tweet_id="123456789",
        author="Tech Expert",
        author_username="techexpert",
        content="New AI regulations announced in EU",
        engagement_score=150,
        likes=100,
        retweets=40,
        replies=10,
        tweet_created_at=datetime.utcnow()
    )
    
    assert result.id is not None
    assert result.tweet_id == "123456789"
    assert result.engagement_score == 150


def test_create_draft(db_manager):
    """Test creating a LinkedIn draft."""
    workflow = db_manager.create_workflow("Tech trends")
    
    draft = db_manager.create_draft(
        workflow_id=workflow.id,
        content="🚀 Exciting developments in AI...",
        version=1,
        status=DraftStatus.DRAFT
    )
    
    assert draft.id is not None
    assert draft.version == 1
    assert draft.status == DraftStatus.DRAFT


def test_create_feedback(db_manager):
    """Test creating user feedback."""
    workflow = db_manager.create_workflow("Test query")
    draft = db_manager.create_draft(
        workflow_id=workflow.id,
        content="Test content"
    )
    
    feedback = db_manager.create_feedback(
        draft_id=draft.id,
        feedback_type=FeedbackType.MODIFY,
        comments="Please make it more engaging"
    )
    
    assert feedback.id is not None
    assert feedback.feedback_type == FeedbackType.MODIFY
    assert feedback.comments == "Please make it more engaging"


def test_workflow_status_update(db_manager):
    """Test updating workflow status."""
    workflow = db_manager.create_workflow("Test")
    
    updated = db_manager.update_workflow_status(
        workflow_id=workflow.id,
        status=WorkflowStatus.COMPLETED
    )
    
    assert updated.status == WorkflowStatus.COMPLETED
    assert updated.completed_at is not None


def test_get_latest_draft(db_manager):
    """Test getting the latest draft version."""
    workflow = db_manager.create_workflow("Test")
    
    # Create multiple draft versions
    draft1 = db_manager.create_draft(workflow.id, "Version 1", version=1)
    draft2 = db_manager.create_draft(workflow.id, "Version 2", version=2)
    draft3 = db_manager.create_draft(workflow.id, "Version 3", version=3)
    
    latest = db_manager.get_latest_draft(workflow.id)
    
    assert latest.id == draft3.id
    assert latest.version == 3
    assert latest.content == "Version 3"


def test_get_filtered_content_by_workflow(db_manager):
    """Test retrieving filtered content ordered by rank."""
    workflow = db_manager.create_workflow("Test")
    
    # Create research results
    result1 = db_manager.create_research_result(
        workflow.id, "1", "Author1", "user1", "Content1",
        100, 50, 30, 20, datetime.utcnow()
    )
    result2 = db_manager.create_research_result(
        workflow.id, "2", "Author2", "user2", "Content2",
        200, 100, 60, 40, datetime.utcnow()
    )
    
    # Create filtered content
    db_manager.create_filtered_content(workflow.id, result2.id, 1, 0.95)
    db_manager.create_filtered_content(workflow.id, result1.id, 2, 0.85)
    
    filtered = db_manager.get_filtered_content_by_workflow(workflow.id)
    
    assert len(filtered) == 2
    assert filtered[0].rank == 1
    assert filtered[1].rank == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
