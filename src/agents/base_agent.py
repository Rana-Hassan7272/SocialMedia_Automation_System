"""
Base agent class for all workflow agents.
Provides common functionality and Groq LLM integration.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the workflow.
    Provides Groq LLM integration and common utilities.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize base agent with Groq LLM.
        
        Args:
            model: Groq model name (defaults to settings)
            temperature: LLM temperature (0.0 to 1.0)
            max_tokens: Max tokens to generate
        """
        self.model_name = model or settings.groq_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Must be implemented by subclasses.
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow state.
        Must be implemented by subclasses.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    def invoke_llm(
        self,
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Invoke the Groq LLM with a message.
        
        Args:
            user_message: User message to send
            system_prompt: Optional system prompt (defaults to get_system_prompt())
            
        Returns:
            LLM response text
        """
        system = system_prompt or self.get_system_prompt()
        
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user_message)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            raise RuntimeError(f"LLM invocation failed: {str(e)}")
    
    def __repr__(self) -> str:
        """String representation of agent."""
        return f"{self.__class__.__name__}(model={self.model_name})"
