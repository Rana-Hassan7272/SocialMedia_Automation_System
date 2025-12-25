# 🤖 Social Media Automation System

An intelligent multi-agent system that researches topics from **Reddit** and automatically generates engaging **Twitter/X posts** with human oversight.

## 🌟 Features

- **Intent Understanding**: Automatically parses user queries to extract topic, scope, and tone
- **Intelligent Research**: ReAct-style agent that searches **Reddit** for relevant content and discussions
- **Content Filtering**: Removes low-quality content and ranks by engagement
- **Insight Generation**: Summarizes Reddit posts into meaningful insights
- **Twitter/X Post Creation**: Generates engaging, viral-worthy tweets
- **Human-in-the-Loop**: Review and approve posts before publishing
- **Publishing to Twitter/X**: Automatically posts to Twitter/X after approval
- **Complete Logging**: SQLite database tracks entire workflow for analytics

## 🏗️ Architecture

This system uses **LangGraph** to orchestrate multiple specialized agents:

1. **Intent Understanding Agent** - Parses user queries
2. **Research Agent (ReAct)** - Searches Reddit intelligently  
3. **Filtering Agent** - Cleans and ranks content
4. **Summarization Agent** - Extracts key insights
5. **Twitter/X Drafting Agent** - Creates engaging tweets
6. **Publishing Agent** - Posts to Twitter/X (with approval)

## 📋 Prerequisites

- Python 3.10+
- Groq API account (for LLM)
- Twitter/X Developer account (for publishing only)
- Internet connection (for Reddit API - no auth needed)

## 🚀 Setup Instructions

### 1. Clone and Navigate

```bash
cd social_media_automation
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

#### 🔑 Get Groq API Key
1. Go to [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign up or log in
3. Click "Create API Key"
4. Copy and paste into `.env` as `GROQ_API_KEY`

#### 🔑 Get Twitter/X API Keys
1. Go to [https://developer.twitter.com/en/portal/dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Sign in with your Twitter/X account
3. Create a new Project and App
4. Go to "Keys and Tokens" tab
5. Generate:
   - API Key and Secret
   - Access Token and Secret
6. Copy all 4 values to `.env`

**Note**: You may need to apply for Elevated access for full API features.

### 5. Initialize Database

```bash
python -c "from src.database import DatabaseManager; db = DatabaseManager(); db.initialize_database()"
```

You should see: `✅ Database initialized at: sqlite:///data/social_automation.db`

## 📁 Project Structure

```
social_media_automation/
├── src/
│   ├── agents/              # Agent implementations
│   ├── database/            # Database models and operations
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   └── db_manager.py    # Database CRUD operations
│   ├── config/              # Configuration management
│   │   └── settings.py      # Environment variable handling
│   ├── workflow/            # LangGraph workflow orchestration
│   └── utils/               # Utility functions
├── tests/                   # Test files
├── data/                    # SQLite database storage
├── .env                     # Your API keys (not in git)
├── .env.example             # Template for environment variables
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🗄️ Database Schema

The system uses SQLite with the following tables:

- **workflows** - Track complete workflow executions
- **intents** - Store parsed user intents
- **research_results** - Store tweets from research
- **filtered_content** - Store filtered and ranked tweets
- **insights** - Store summarized insights
- **drafts** - Store Twitter/X post drafts (with versions)
- **feedback** - Store user feedback on drafts
- **published_posts** - Store published tweets

## 🎯 Usage

(Usage instructions will be added as we build the agents and workflow)

## 🧪 Testing

Run tests with:

```bash
pytest tests/ -v
```

## 📝 Development Status

- [x] Phase 1: Project Setup & Infrastructure
- [ ] Phase 2: Core Agent Framework
- [ ] Phase 3: Intent Understanding Agent
- [ ] Phase 4: Research Agent (ReAct)
- [ ] Phase 5: Content Processing Agents
- [ ] Phase 6: Twitter/X Content Generation
- [ ] Phase 7: Human-in-the-Loop System
- [ ] Phase 8: Publishing & Integration (Twitter/X)
- [ ] Phase 9: Logging & Analytics
- [ ] Phase 10: Testing & Deployment

## 🔧 Configuration

Key settings in `.env`:

- `GROQ_MODEL` - LLM model to use (default: llama-3.3-70b-versatile)
- `MAX_TWEETS_PER_QUERY` - Max tweets to retrieve (default: 50)
- `MIN_ENGAGEMENT_SCORE` - Minimum engagement for filtering (default: 10)
- `TOP_TWEETS_COUNT` - Number of top tweets for summarization (default: 8)

## 📄 License

This project is for educational and personal use.

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

---

**Built with**: LangGraph, Groq, SQLAlchemy, Tweepy, and LinkedIn API
# SocailMedia_Automation_System
