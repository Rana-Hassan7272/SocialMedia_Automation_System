"""
Intent Understanding Agent.
Parses user queries to extract topic, scope, and tone.
"""

import json
from typing import Dict, Any
from .base_agent import BaseAgent
from ..database import DatabaseManager
from ..workflow.state import WorkflowStep


class IntentAgent(BaseAgent):
    """
    Agent that understands user intent from natural language queries.
    Extracts: topic, scope, and tone.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize intent agent.
        
        Args:
            db_manager: Database manager for storing results
        """
        super().__init__(temperature=0.3)  # Lower temp for more focused extraction
        self.db_manager = db_manager
    
    def get_system_prompt(self) -> str:
        """Get system prompt for intent understanding."""
        return """You are an intent understanding specialist. Your job is to analyze user queries and extract structured information.

Extract the following from the user's query:
1. **Topic**: The main subject (e.g., "AI", "cryptocurrency", "politics", "technology")
2. **Scope**: Time/region constraint (e.g., "latest", "today", "this week", "in Europe", "global")
3. **Tone**: Desired tone if mentioned (e.g., "informative", "opinionated", "neutral") - use "informative" as default

Return ONLY valid JSON in this exact format:
{
    "topic": "extracted topic",
    "scope": "extracted scope", 
    "tone": "extracted tone"
}

Examples:
- Query: "What's happening in crypto today?"
  Output: {"topic": "cryptocurrency", "scope": "today", "tone": "informative"}

- Query: "Get latest AI regulation news in Europe"
  Output: {"topic": "AI regulation", "scope": "latest in Europe", "tone": "informative"}

- Query: "Tell me about political updates this week"
  Output: {"topic": "politics", "scope": "this week", "tone": "informative"}

Return ONLY the JSON, nothing else."""
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user query to extract intent.
        
        Args:
            state: Workflow state with user_query
            
        Returns:
            Updated state with topic, scope, tone
        """
        user_query = state.get("user_query", "")
        workflow_id = state.get("workflow_id")
        
        if not user_query:
            state["error"] = "No user query provided"
            return state
        
        try:
            # Call LLM to extract intent
            response = self.invoke_llm(user_query)
            
            # Parse JSON response
            intent_data = json.loads(response)
            
            # Update state
            state["topic"] = intent_data.get("topic", "")
            state["scope"] = intent_data.get("scope", "latest")
            state["tone"] = intent_data.get("tone", "informative")
            state["current_step"] = WorkflowStep.INTENT_UNDERSTANDING
            
            # Save to database if workflow_id exists
            if workflow_id and self.db_manager:
                self.db_manager.create_intent(
                    workflow_id=workflow_id,
                    topic=state["topic"],
                    scope=state["scope"],
                    tone=state["tone"],
                    raw_intent=response
                )
            
            return state
            
        except json.JSONDecodeError as e:
            state["error"] = f"Failed to parse intent: {str(e)}"
            return state
        except Exception as e:
            state["error"] = f"Intent extraction failed: {str(e)}"
            return state
