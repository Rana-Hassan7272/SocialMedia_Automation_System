"""
Demo script for Intent Understanding Agent.
Shows how the agent extracts structured intent from user queries.
"""

from src.agents.intent_agent import IntentAgent
from src.database import DatabaseManager
from src.workflow.state import create_initial_state

print("🧠 Intent Understanding Agent Demo\n")
print("=" * 60)

# Initialize
db = DatabaseManager()
agent = IntentAgent(db_manager=db)

# Test queries
test_queries = [
    "What's happening in crypto today?",
    "Get latest AI regulation news in Europe",
    "Tell me about political updates this week",
    "Show me trending technology news",
    "What's new in machine learning?"
]

print("\n📝 Testing Intent Extraction:\n")

for i, query in enumerate(test_queries, 1):
    print(f"{i}. Query: \"{query}\"")
    
    # Create workflow and get ID immediately
    workflow = db.create_workflow(query)
    workflow_id = workflow.id  # Capture ID while still in session
    state = create_initial_state(query, workflow_id)
    
    # Process with agent
    try:
        result = agent.process(state)
        
        if "error" in result:
            print(f"   ❌ Error: {result['error']}\n")
        else:
            print(f"   📌 Topic: {result['topic']}")
            print(f"   📅 Scope: {result['scope']}")
            print(f"   🎨 Tone: {result['tone']}")
            print(f"   ✅ Saved to database (workflow #{workflow_id})\n")
    
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}\n")

print("=" * 60)
print("✅ Demo Complete!")
print("\nThe agent successfully:")
print("  1. Understood natural language queries")
print("  2. Extracted structured intent (topic, scope, tone)")
print("  3. Saved results to database")
