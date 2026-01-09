"""
CRUD operations for issues with optimistic locking support.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models import Issue, IssueStatus
from app.schemas import IssueCreate, IssueUpdate


def create_issue(db: Session, issue: IssueCreate) -> Issue:
    """
    Create a new issue.
    Version is initialized to 1 for optimistic locking.
    """
    db_issue = Issue(
        title=issue.title,
        description=issue.description,
        status=issue.status,
        creator_id=issue.creator_id,
        assignee_id=issue.assignee_id,
        version=1
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue


def get_issue_by_id(db: Session, issue_id: int) -> Issue | None:
    """Get issue by ID with all relationships loaded."""
    return db.query(Issue).filter(Issue.id == issue_id).first()


def get_all_issues(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: IssueStatus | None = None,
    assignee_id: int | None = None,
    creator_id: int | None = None
) -> tuple[list[Issue], int]:
    """
    Get issues with optional filtering and pagination.
    Returns tuple of (issues, total_count)
    """
    query = db.query(Issue)
    
    if status:
        query = query.filter(Issue.status == status)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)
    if creator_id:
        query = query.filter(Issue.creator_id == creator_id)
    
    total = query.count()
    issues = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()
    
    return issues, total


def update_issue_with_locking(
    db: Session,
    issue_id: int,
    update_data: IssueUpdate
) -> tuple[Issue | None, str | None]:
    """
    Update an issue with optimistic locking.
    
    Returns:
        tuple: (updated_issue, error_message)
        If version mismatch, returns (None, error_message)
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    if not issue:
        return None, f"Issue with id {issue_id} not found"
    
    # Check optimistic locking version
    if issue.version != update_data.version:
        return None, f"Version mismatch. Current version is {issue.version}, expected {update_data.version}"
    
    # Update fields
    if update_data.title is not None:
        issue.title = update_data.title
    if update_data.description is not None:
        issue.description = update_data.description
    if update_data.status is not None:
        issue.status = update_data.status
        # Set resolved_at if status is closed
        if update_data.status == IssueStatus.CLOSED and not issue.resolved_at:
            issue.resolved_at = datetime.utcnow()
    if update_data.assignee_id is not None or (hasattr(update_data, 'assignee_id') and update_data.assignee_id is None):
        issue.assignee_id = update_data.assignee_id
    
    # Increment version for optimistic locking
    issue.version += 1
    issue.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(issue)
    return issue, None


def delete_issue(db: Session, issue_id: int) -> bool:
    """Delete an issue and cascade delete its comments."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        return False
    
    db.delete(issue)
    db.commit()
    return True
