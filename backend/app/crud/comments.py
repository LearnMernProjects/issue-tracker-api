"""
CRUD operations for comments.
"""
from sqlalchemy.orm import Session
from app.models import Comment, Issue
from app.schemas import CommentCreate


def create_comment(db: Session, issue_id: int, comment: CommentCreate, author_id: int) -> Comment:
    """
    Create a new comment on an issue.
    Validates that the issue exists.
    """
    # Verify issue exists
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError(f"Issue {issue_id} not found")
    
    db_comment = Comment(
        issue_id=issue_id,
        author_id=author_id,
        body=comment.body
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comment_by_id(db: Session, comment_id: int) -> Comment | None:
    """Get a comment by ID."""
    return db.query(Comment).filter(Comment.id == comment_id).first()


def get_comments_by_issue_id(
    db: Session,
    issue_id: int,
    skip: int = 0,
    limit: int = 100
) -> list[Comment]:
    """
    Get all comments for a specific issue with pagination.
    """
    return (
        db.query(Comment)
        .filter(Comment.issue_id == issue_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_comment(db: Session, comment_id: int) -> bool:
    """
    Delete a comment by ID.
    Returns True if comment was deleted, False if not found.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return False
    db.delete(comment)
    db.commit()
    return True
