"""
Test Intent Understanding Agent.
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.agents.intent_agent import IntentAgent
from src.database import DatabaseManager
from src.workflow.state import create_initial_state


@pytest.fixture
def mock_db():
    """Create mock database manager."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def intent_agent(mock_db):
    """Create intent agent with mock database."""
    return IntentAgent(db_manager=mock_db)


def test_system_prompt(intent_agent):
    """Test system prompt is properly defined."""
    prompt = intent_agent.get_system_prompt()
    
    assert "topic" in prompt.lower()
    assert "scope" in prompt.lower()
    assert "tone" in prompt.lower()
    assert "json" in prompt.lower()


@patch('src.agents.base_agent.ChatGroq')
def test_process_extracts_intent(mock_groq, intent_agent):
    """Test intent extraction from user query."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = json.dumps({
        "topic": "cryptocurrency",
        "scope": "today",
        "tone": "informative"
    })
    mock_groq.return_value.invoke.return_value = mock_response
    
    # Create state
    state = create_initial_state("What's happening in crypto today?", 1)
    
    # Process
    result = intent_agent.process(state)
    
    # Verify
    assert result["topic"] == "cryptocurrency"
    assert result["scope"] == "today"
    assert result["tone"] == "informative"
    assert "error" not in result


@patch('src.agents.base_agent.ChatGroq')
def test_process_saves_to_database(mock_groq, mock_db):
    """Test that intent is saved to database."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = json.dumps({
        "topic": "AI regulation",
        "scope": "latest in Europe",
        "tone": "informative"
    })
    mock_groq.return_value.invoke.return_value = mock_response
    
    # Create agent with real mock db
    agent = IntentAgent(db_manager=mock_db)
    
    # Create state
    state = create_initial_state("Get latest AI regulation news in Europe", 1)
    
    # Process
    agent.process(state)
    
    # Verify database was called
    mock_db.create_intent.assert_called_once_with(
        workflow_id=1,
        topic="AI regulation",
        scope="latest in Europe",
        tone="informative",
        raw_intent=mock_response.content
    )


@patch('src.agents.base_agent.ChatGroq')
def test_process_handles_invalid_json(mock_groq, intent_agent):
    """Test error handling for invalid JSON response."""
    # Mock invalid response
    mock_response = Mock()
    mock_response.content = "Not valid JSON"
    mock_groq.return_value.invoke.return_value = mock_response
    
    state = create_initial_state("Test query", 1)
    result = intent_agent.process(state)
    
    assert "error" in result
    assert "parse" in result["error"].lower()


def test_process_with_empty_query(intent_agent):
    """Test handling of empty query."""
    state = {"workflow_id": 1, "user_query": ""}
    result = intent_agent.process(state)
    
    assert "error" in result
    assert "no user query" in result["error"].lower()


@patch('src.agents.base_agent.ChatGroq')
def test_multiple_queries(mock_groq, intent_agent):
    """Test processing multiple different queries."""
    test_cases = [
        {
            "query": "Latest tech news",
            "response": {"topic": "technology", "scope": "latest", "tone": "informative"}
        },
        {
            "query": "Political updates this week",
            "response": {"topic": "politics", "scope": "this week", "tone": "informative"}
        },
        {
            "query": "What's trending in AI?",
            "response": {"topic": "AI", "scope": "trending", "tone": "informative"}
        }
    ]
    
    for test_case in test_cases:
        # Mock response
        mock_response = Mock()
        mock_response.content = json.dumps(test_case["response"])
        mock_groq.return_value.invoke.return_value = mock_response
        
        state = create_initial_state(test_case["query"], 1)
        result = intent_agent.process(state)
        
        assert result["topic"] == test_case["response"]["topic"]
        assert result["scope"] == test_case["response"]["scope"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
