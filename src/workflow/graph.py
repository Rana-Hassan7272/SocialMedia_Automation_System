"""
LangGraph workflow orchestration.
Defines the complete agent workflow graph.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
from .state import WorkflowState, WorkflowStep
from ..agents import (
    IntentAgent, ResearchAgent, FilteringAgent,
    SummarizationAgent, DraftingAgent, PublishingAgent
)
from ..database import DatabaseManager
from ..utils import RedditClient, TwitterClient


class WorkflowGraph:
    """
    LangGraph-based workflow orchestration.
    Manages the complete pipeline from intent to publishing.
    """
    
    def __init__(self, db_manager: DatabaseManager, reddit_client: RedditClient, twitter_client: TwitterClient):
        """
        Initialize workflow graph with all agents.
        
        Args:
            db_manager: Database manager
            reddit_client: Reddit API client
            twitter_client: Twitter API client
        """
        self.db_manager = db_manager
        self.reddit_client = reddit_client
        self.twitter_client = twitter_client
        
        # Initialize all agents
        self.intent_agent = IntentAgent(db_manager=db_manager)
        self.research_agent = ResearchAgent(db_manager=db_manager, reddit_client=reddit_client)
        self.filtering_agent = FilteringAgent(db_manager=db_manager, top_k=5)
        self.summarization_agent = SummarizationAgent(db_manager=db_manager)
        self.drafting_agent = DraftingAgent(db_manager=db_manager)
        self.publishing_agent = PublishingAgent(db_manager=db_manager, twitter_client=twitter_client)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (each agent is a node)
        workflow.add_node("intent", self._intent_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("filter", self._filter_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("draft", self._draft_node)
        workflow.add_node("review", self._review_node)
        workflow.add_node("publish", self._publish_node)
        
        # Define edges (workflow transitions)
        workflow.set_entry_point("intent")
        workflow.add_edge("intent", "research")
        workflow.add_edge("research", "filter")
        workflow.add_edge("filter", "summarize")
        workflow.add_edge("summarize", "draft")
        workflow.add_edge("draft", "review")
        
        # Conditional edge from review
        workflow.add_conditional_edges(
            "review",
            self._should_publish,
            {
                "publish": "publish",
                "revise": "draft",
                "end": END
            }
        )
        
        workflow.add_edge("publish", END)
        
        return workflow.compile()
    
    # Node functions
    def _intent_node(self, state: WorkflowState) -> WorkflowState:
        """Intent understanding node."""
        print("🔹 Node: Intent Understanding")
        return self.intent_agent.process(state)
    
    def _research_node(self, state: WorkflowState) -> WorkflowState:
        """Research node."""
        print("🔹 Node: Research (Reddit)")
        return self.research_agent.process(state)
    
    def _filter_node(self, state: WorkflowState) -> WorkflowState:
        """Filtering node."""
        print("🔹 Node: Filtering & Ranking")
        return self.filtering_agent.process(state)
    
    def _summarize_node(self, state: WorkflowState) -> WorkflowState:
        """Summarization node."""
        print("🔹 Node: Summarization")
        return self.summarization_agent.process(state)
    
    def _draft_node(self, state: WorkflowState) -> WorkflowState:
        """Drafting node."""
        print("🔹 Node: Drafting")
        return self.drafting_agent.process(state)
    
    def _review_node(self, state: WorkflowState) -> WorkflowState:
        """Human review node."""
        print("🔹 Node: Human Review")
        return self.publishing_agent.request_human_review(state)
    
    def _publish_node(self, state: WorkflowState) -> WorkflowState:
        """Publishing node."""
        print("🔹 Node: Publishing")
        return self.publishing_agent.handle_approval(state)
    
    def _should_publish(self, state: WorkflowState) -> str:
        """
        Conditional logic for review decision.
        
        Returns:
            Next node: "publish", "revise", or "end"
        """
        # This would be set by human review
        if state.get("approved"):
            return "publish"
        elif state.get("revision_requested"):
            return "revise"
        else:
            return "end"
    
    def run(self, user_query: str) -> WorkflowState:
        """
        Execute the complete workflow.
        
        Args:
            user_query: User's input query
            
        Returns:
            Final workflow state
        """
        # Create workflow in database
        workflow = self.db_manager.create_workflow(user_query)
        
        # Create initial state
        from .state import create_initial_state
        initial_state = create_initial_state(user_query, workflow.id)
        
        # Run the graph
        print(f"\n🚀 Starting LangGraph Workflow")
        print(f"Query: {user_query}")
        print("=" * 60)
        
        final_state = self.graph.invoke(initial_state)
        
        print("=" * 60)
        print("✅ Workflow Complete!")
        
        return final_state
