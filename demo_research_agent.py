"""
Demo script for Research Agent with Reddit.
Shows ReAct reasoning and Reddit search in action.
"""

from src.agents.intent_agent import IntentAgent
from src.agents.research_agent import ResearchAgent
from src.database import DatabaseManager
from src.utils import RedditClient
from src.workflow.state import create_initial_state

print("🔬 Research Agent (ReAct + Reddit) Demo\n")
print("=" * 60)

# Initialize components
db = DatabaseManager()
reddit_client = RedditClient()
intent_agent = IntentAgent(db_manager=db)
research_agent = ResearchAgent(db_manager=db, reddit_client=reddit_client)

# Test query
query = "What's today special for christians?"
print(f"\n📝 User Query: \"{query}\"\n")

# Step 1: Extract Intent
print("STEP 1: Intent Understanding")
print("-" * 60)
workflow = db.create_workflow(query)
workflow_id = workflow.id
state = create_initial_state(query, workflow_id)

state = intent_agent.process(state)
print(f"✅ Intent extracted:")
print(f"   Topic: {state['topic']}")
print(f"   Scope: {state['scope']}")
print(f"   Tone: {state['tone']}\n")

# Step 2: Research with ReAct
print("STEP 2: Research (ReAct + Reddit)")
print("-" * 60)
state = research_agent.process(state)

if "error" in state:
    print(f"❌ Error: {state['error']}")
else:
    posts = state.get("raw_tweets", [])  # Keeping name for compatibility
    print(f"\n✅ Research Complete!")
    print(f"   Total posts found: {len(posts)}")
    
    if posts:
        print(f"\n📌 Top 5 Posts by Engagement:\n")
        for i, post in enumerate(posts[:5], 1):
            print(f"{i}. r/{post['subreddit']} - u/{post['author']}")
            print(f"   {post['title']}")
            print(f"   ⬆️ {post['score']} | 💬 {post['num_comments']}")
            print(f"   Engagement Score: {post['engagement_score']}")
            print(f"   🔗 {post['permalink']}\n")

print("=" * 60)
print("✅ Demo Complete!")
print(f"\nWorkflow #{workflow_id} saved to database")
print("Check the 'research_results' table for all posts")
