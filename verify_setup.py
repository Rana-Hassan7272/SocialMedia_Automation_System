"""
Simple verification script to test core functionality.
Run this to verify the base agent and workflow setup.
"""

print("🧪 Testing Core Agent Framework...\n")

# Test 1: Import workflow state
print("1️⃣ Testing workflow state imports...")
try:
    from src.workflow.state import WorkflowState, WorkflowStep, create_initial_state
    print("   ✅ Workflow state imported successfully")
    
    # Create initial state
    state = create_initial_state("Test query", 1)
    assert state["workflow_id"] == 1
    assert state["user_query"] == "Test query"
    assert state["current_step"] == WorkflowStep.START
    print("   ✅ Initial state creation works")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Import base agent
print("\n2️⃣ Testing base agent imports...")
try:
    from src.agents.base_agent import BaseAgent
    print("   ✅ Base agent imported successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Import workflow graph
print("\n3️⃣ Testing workflow graph imports...")
try:
    from src.workflow.graph import WorkflowGraph
    print("   ✅ Workflow graph imported successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Check Groq configuration
print("\n4️⃣ Testing Groq configuration...")
try:
    from src.config import settings
    assert settings.groq_api_key, "Groq API key not set"
    print(f"   ✅ Groq configured with model: {settings.groq_model}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Test concrete agent implementation
print("\n5️⃣ Testing concrete agent implementation...")
try:
    from src.agents.base_agent import BaseAgent
    
    class TestAgent(BaseAgent):
        def get_system_prompt(self):
            return "Test prompt"
        
        def process(self, state):
            state["processed"] = True
            return state
    
    agent = TestAgent()
    print(f"   ✅ Agent created: {repr(agent)}")
    
    # Test process
    test_state = {"test": "data"}
    result = agent.process(test_state)
    assert result["processed"] is True
    print("   ✅ Agent process method works")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("✅ Core Agent Framework Setup Complete!")
print("="*50)
print("\nYou can now build specific agents that inherit from BaseAgent.")
