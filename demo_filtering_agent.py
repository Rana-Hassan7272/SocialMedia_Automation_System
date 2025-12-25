"""
Demo script for Filtering Agent.
Shows relevance scoring and ranking in action.
"""

from src.agents.intent_agent import IntentAgent
from src.agents.research_agent import ResearchAgent
from src.agents.filtering_agent import FilteringAgent
from src.database import DatabaseManager
from src.utils import RedditClient
from src.workflow.state import create_initial_state

print("🔍 Filtering Agent Demo\n")
print("=" * 60)

# Initialize components
db = DatabaseManager()
reddit_client = RedditClient()
intent_agent = IntentAgent(db_manager=db)
research_agent = ResearchAgent(db_manager=db, reddit_client=reddit_client)
filtering_agent = FilteringAgent(db_manager=db, top_k=5)

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
print(f"✅ Topic: {state['topic']}, Scope: {state['scope']}\n")

# Step 2: Research
print("STEP 2: Research (ReAct + Reddit)")
print("-" * 60)
state = research_agent.process(state)
print(f"✅ Found {len(state.get('raw_tweets', []))} posts\n")

# Step 3: Filter
print("STEP 3: Filtering & Ranking")
print("-" * 60)
state = filtering_agent.process(state)

filtered = state.get("filtered_tweets", [])
print(f"\n✅ Filtering Complete!")
print(f"   Filtered to top {len(filtered)} posts\n")

if filtered:
    print("📌 Top Filtered Posts:\n")
    for i, post in enumerate(filtered, 1):
        print(f"{i}. r/{post['subreddit']} - {post['title'][:80]}")
        print(f"   Relevance: {post['relevance_score']:.2f} | Combined: {post['combined_score']:.2f}")
        print(f"   Engagement: ⬆️ {post['score']} | 💬 {post['num_comments']}\n")

print("=" * 60)
print("✅ Demo Complete!")
print(f"\nWorkflow #{workflow_id} - Check 'filtered_content' table")
