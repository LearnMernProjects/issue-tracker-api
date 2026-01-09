"""
SQLAlchemy ORM models for Issue Tracker.
Implements optimistic locking, relationships, and indexes.
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum, Index, UniqueConstraint, func, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class IssueStatus(str, enum.Enum):
    """Enum for issue statuses."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    REOPENED = "reopened"


class User(Base):
    """User model for issue authors and assignees."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issues_created = relationship(
        "Issue",
        back_populates="creator",
        foreign_keys="Issue.creator_id"
    )
    issues_assigned = relationship(
        "Issue",
        back_populates="assignee",
        foreign_keys="Issue.assignee_id"
    )
    comments = relationship("Comment", back_populates="author")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Label(Base):
    """Label model for categorizing issues."""
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issues = relationship(
        "Issue",
        secondary="issue_labels",
        back_populates="labels"
    )

    def __repr__(self):
        return f"<Label(id={self.id}, name={self.name})>"


# Association table for many-to-many relationship
issue_labels = Table(
    "issue_labels",
    Base.metadata,
    Column("issue_id", Integer, ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Issue(Base):
    """Issue model with optimistic locking support."""
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Optimistic locking version field
    version = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship(
        "User",
        back_populates="issues_created",
        foreign_keys=[creator_id]
    )
    assignee = relationship(
        "User",
        back_populates="issues_assigned",
        foreign_keys=[assignee_id]
    )
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")
    labels = relationship(
        "Label",
        secondary=issue_labels,
        back_populates="issues"
    )

    # Indexes
    __table_args__ = ()

    def __repr__(self):
        return f"<Issue(id={self.id}, title={self.title}, status={self.status})>"


class Comment(Base):
    """Comment model for issue discussions."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")

    # Indexes
    __table_args__ = ()

    def __repr__(self):
        return f"<Comment(id={self.id}, issue_id={self.issue_id})>"
