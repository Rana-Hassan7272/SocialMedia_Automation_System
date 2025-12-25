"""
Demo script for Drafting Agent.
Shows the full pipeline: Intent → Research → Filter → Summarize → Draft
"""

from src.agents.intent_agent import IntentAgent
from src.agents.research_agent import ResearchAgent
from src.agents.filtering_agent import FilteringAgent
from src.agents.summarization_agent import SummarizationAgent
from src.agents.drafting_agent import DraftingAgent
from src.database import DatabaseManager
from src.utils import RedditClient
from src.workflow.state import create_initial_state

print("✍️  Twitter/X Drafting Agent Demo\n")
print("=" * 60)

# Initialize components
db = DatabaseManager()
reddit_client = RedditClient()
intent_agent = IntentAgent(db_manager=db)
research_agent = ResearchAgent(db_manager=db, reddit_client=reddit_client)
filtering_agent = FilteringAgent(db_manager=db, top_k=5)
summarization_agent = SummarizationAgent(db_manager=db)
drafting_agent = DraftingAgent(db_manager=db)

# Test query
query = "What's happening in AI today?"
print(f"\n📝 User Query: \"{query}\"\n")

# Step 1: Extract Intent
print("STEP 1: Intent Understanding")
print("-" * 60)
workflow = db.create_workflow(query)
workflow_id = workflow.id
state = create_initial_state(query, workflow_id)

state = intent_agent.process(state)
print(f"✅ Topic: {state['topic']}, Scope: {state['scope']}, Tone: {state['tone']}\n")

# Step 2: Research
print("STEP 2: Research (ReAct + Reddit)")
print("-" * 60)
state = research_agent.process(state)
print(f"✅ Found {len(state.get('raw_tweets', []))} posts\n")

# Step 3: Filter
print("STEP 3: Filtering & Ranking")
print("-" * 60)
state = filtering_agent.process(state)
print(f"✅ Filtered to {len(state.get('filtered_tweets', []))} posts\n")

# Step 4: Summarize
print("STEP 4: Summarization & Insights")
print("-" * 60)
state = summarization_agent.process(state)
print(f"✅ Generated insights\n")

# Step 5: Draft
print("STEP 5: Twitter/X Post Drafting")
print("-" * 60)
state = drafting_agent.process(state)

if "error" in state:
    print(f"❌ Error: {state['error']}")
else:
    draft = state.get('draft_content', '')
    print(f"\n✅ Draft Complete!\n")
    print("📱 TWITTER/X POST:")
    print("─" * 60)
    print(draft)
    print("─" * 60)
    print(f"Character count: {len(draft)}/280")
    
    # Show option for revision
    print("\n💡 To create a revision, you can call:")
    print("   drafting_agent.create_revision(state, 'your feedback here')")

print("\n" + "=" * 60)
print("✅ Demo Complete!")
print(f"\nWorkflow #{workflow_id} - Full pipeline executed")
print("Next: Human review and publishing!")
