"""
Database manager for Social Media Automation System.
Handles database initialization, connections, and CRUD operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    Base, Workflow, Intent, ResearchResult, FilteredContent,
    Insight, Draft, Feedback, PublishedPost,
    WorkflowStatus, DraftStatus, FeedbackType
)
from ..config import settings


class DatabaseManager:
    """Manages database operations for the social media automation system."""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL. If None, uses settings.
        """
        self.database_url = database_url or settings.get_database_url()
        self.engine = create_engine(
            self.database_url,
            echo=settings.log_level == "DEBUG"
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
    def initialize_database(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        print(f"✅ Database initialized at: {self.database_url}")
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️  All tables dropped")
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ========================================
    # Workflow Operations
    # ========================================
    
    def create_workflow(self, user_query: str) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            user_query: User's original query
            
        Returns:
            Created Workflow object
        """
        with self.get_session() as session:
            workflow = Workflow(
                user_query=user_query,
                status=WorkflowStatus.PENDING
            )
            session.add(workflow)
            session.flush()
            session.refresh(workflow)
            # Expunge from session so it can be used after session closes
            session.expunge(workflow)
            return workflow
    
    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID."""
        with self.get_session() as session:
            return session.get(Workflow, workflow_id)
    
    def update_workflow_status(
        self,
        workflow_id: int,
        status: WorkflowStatus,
        error_message: Optional[str] = None
    ) -> Workflow:
        """Update workflow status."""
        with self.get_session() as session:
            workflow = session.get(Workflow, workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow.status = status
            if error_message:
                workflow.error_message = error_message
            if status == WorkflowStatus.COMPLETED:
                workflow.completed_at = datetime.utcnow()
            
            session.flush()
            session.refresh(workflow)
            return workflow
    
    def get_all_workflows(self, limit: int = 100) -> List[Workflow]:
        """Get all workflows, most recent first."""
        with self.get_session() as session:
            stmt = select(Workflow).order_by(Workflow.created_at.desc()).limit(limit)
            return list(session.scalars(stmt).all())
    
    # ========================================
    # Intent Operations
    # ========================================
    
    def create_intent(
        self,
        workflow_id: int,
        topic: str,
        scope: str,
        raw_intent: str,
        tone: Optional[str] = None
    ) -> Intent:
        """Create a new intent."""
        with self.get_session() as session:
            intent = Intent(
                workflow_id=workflow_id,
                topic=topic,
                scope=scope,
                tone=tone,
                raw_intent=raw_intent
            )
            session.add(intent)
            session.flush()
            session.refresh(intent)
            return intent
    
    def get_intent_by_workflow(self, workflow_id: int) -> Optional[Intent]:
        """Get intent for a workflow."""
        with self.get_session() as session:
            stmt = select(Intent).where(Intent.workflow_id == workflow_id)
            return session.scalar(stmt)
    
    # ========================================
    # Research Result Operations
    # ========================================
    
    def create_research_result(
        self,
        workflow_id: int,
        tweet_id: str,
        author: str,
        author_username: str,
        content: str,
        engagement_score: int,
        likes: int,
        retweets: int,
        replies: int,
        tweet_created_at: datetime
    ) -> ResearchResult:
        """Create a new research result (tweet)."""
        with self.get_session() as session:
            result = ResearchResult(
                workflow_id=workflow_id,
                tweet_id=tweet_id,
                author=author,
                author_username=author_username,
                content=content,
                engagement_score=engagement_score,
                likes=likes,
                retweets=retweets,
                replies=replies,
                tweet_created_at=tweet_created_at
            )
            session.add(result)
            session.flush()
            session.refresh(result)
            return result
    
    def get_research_results_by_workflow(
        self,
        workflow_id: int
    ) -> List[ResearchResult]:
        """Get all research results for a workflow."""
        with self.get_session() as session:
            stmt = select(ResearchResult).where(
                ResearchResult.workflow_id == workflow_id
            ).order_by(ResearchResult.engagement_score.desc())
            return list(session.scalars(stmt).all())
    
    # ========================================
    # Filtered Content Operations
    # ========================================
    
    def create_filtered_content(
        self,
        workflow_id: int,
        research_result_id: int,
        rank: int,
        relevance_score: float
    ) -> FilteredContent:
        """Create filtered content entry."""
        with self.get_session() as session:
            filtered = FilteredContent(
                workflow_id=workflow_id,
                research_result_id=research_result_id,
                rank=rank,
                relevance_score=relevance_score
            )
            session.add(filtered)
            session.flush()
            session.refresh(filtered)
            return filtered
    
    def get_filtered_content_by_workflow(
        self,
        workflow_id: int
    ) -> List[FilteredContent]:
        """Get filtered content for a workflow, ordered by rank."""
        with self.get_session() as session:
            stmt = select(FilteredContent).where(
                FilteredContent.workflow_id == workflow_id
            ).order_by(FilteredContent.rank)
            return list(session.scalars(stmt).all())
    
    # ========================================
    # Insight Operations
    # ========================================
    
    def create_insight(
        self,
        workflow_id: int,
        summary: str,
        key_trends: Optional[str] = None,
        expert_opinions: Optional[str] = None
    ) -> Insight:
        """Create a new insight."""
        with self.get_session() as session:
            insight = Insight(
                workflow_id=workflow_id,
                summary=summary,
                key_trends=key_trends,
                expert_opinions=expert_opinions
            )
            session.add(insight)
            session.flush()
            session.refresh(insight)
            return insight
    
    def get_insights_by_workflow(self, workflow_id: int) -> List[Insight]:
        """Get all insights for a workflow."""
        with self.get_session() as session:
            stmt = select(Insight).where(
                Insight.workflow_id == workflow_id
            ).order_by(Insight.created_at.desc())
            return list(session.scalars(stmt).all())
    
    # ========================================
    # Draft Operations
    # ========================================
    
    def create_draft(
        self,
        workflow_id: int,
        content: str,
        version: int = 1,
        status: DraftStatus = DraftStatus.DRAFT
    ) -> Draft:
        """Create a new draft."""
        with self.get_session() as session:
            draft = Draft(
                workflow_id=workflow_id,
                version=version,
                content=content,
                status=status
            )
            session.add(draft)
            session.flush()
            session.refresh(draft)
            return draft
    
    def update_draft_status(
        self,
        draft_id: int,
        status: DraftStatus
    ) -> Draft:
        """Update draft status."""
        with self.get_session() as session:
            draft = session.get(Draft, draft_id)
            if not draft:
                raise ValueError(f"Draft {draft_id} not found")
            
            draft.status = status
            session.flush()
            session.refresh(draft)
            return draft
    
    def get_drafts_by_workflow(self, workflow_id: int) -> List[Draft]:
        """Get all drafts for a workflow, ordered by version."""
        with self.get_session() as session:
            stmt = select(Draft).where(
                Draft.workflow_id == workflow_id
            ).order_by(Draft.version.desc())
            return list(session.scalars(stmt).all())
    
    def get_latest_draft(self, workflow_id: int) -> Optional[Draft]:
        """Get the latest draft for a workflow."""
        drafts = self.get_drafts_by_workflow(workflow_id)
        return drafts[0] if drafts else None
    
    # ========================================
    # Feedback Operations
    # ========================================
    
    def create_feedback(
        self,
        draft_id: int,
        feedback_type: FeedbackType,
        comments: Optional[str] = None
    ) -> Feedback:
        """Create user feedback."""
        with self.get_session() as session:
            feedback = Feedback(
                draft_id=draft_id,
                feedback_type=feedback_type,
                comments=comments
            )
            session.add(feedback)
            session.flush()
            session.refresh(feedback)
            return feedback
    
    def get_feedback_by_draft(self, draft_id: int) -> List[Feedback]:
        """Get all feedback for a draft."""
        with self.get_session() as session:
            stmt = select(Feedback).where(
                Feedback.draft_id == draft_id
            ).order_by(Feedback.created_at.desc())
            return list(session.scalars(stmt).all())
    
    # ========================================
    # Published Post Operations
    # ========================================
    
    def create_published_post(
        self,
        workflow_id: int,
        draft_id: int,
        twitter_post_id: Optional[str] = None,
        twitter_post_url: Optional[str] = None
    ) -> PublishedPost:
        """Create a published post record."""
        with self.get_session() as session:
            post = PublishedPost(
                workflow_id=workflow_id,
                draft_id=draft_id,
                twitter_post_id=twitter_post_id,
                twitter_post_url=twitter_post_url
            )
            session.add(post)
            session.flush()
            session.refresh(post)
            return post
    
    def get_published_post_by_workflow(
        self,
        workflow_id: int
    ) -> Optional[PublishedPost]:
        """Get published post for a workflow."""
        with self.get_session() as session:
            stmt = select(PublishedPost).where(
                PublishedPost.workflow_id == workflow_id
            )
            return session.scalar(stmt)
    
    def get_all_published_posts(self, limit: int = 100) -> List[PublishedPost]:
        """Get all published posts, most recent first."""
        with self.get_session() as session:
            stmt = select(PublishedPost).order_by(
                PublishedPost.published_at.desc()
            ).limit(limit)
            return list(session.scalars(stmt).all())
