"""
API routes for issues with full CRUD, bulk operations, and labels.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app import crud
from app.models import IssueStatus
from app.schemas import (
    IssueCreate, IssueResponse, IssueUpdate, IssueListResponse,
    CommentCreate, CommentResponse,
    IssueLabelsUpdate,
    BulkStatusUpdateRequest, BulkStatusUpdateResponse
)

router = APIRouter(prefix="/issues", tags=["issues"])


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(issue: IssueCreate, db: Session = Depends(get_db)):
    """
    Create a new issue.
    
    - **title**: Issue title (required)
    - **description**: Detailed description (optional)
    - **status**: Issue status (default: "open")
    - **creator_id**: ID of the user creating the issue
    - **assignee_id**: ID of the assigned user (optional)
    """
    creator = crud.users.get_user_by_id(db, issue.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with id {issue.creator_id} not found"
        )
    
    if issue.assignee_id:
        assignee = crud.users.get_user_by_id(db, issue.assignee_id)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignee with id {issue.assignee_id} not found"
            )
    
    return crud.issues.create_issue(db, issue)


@router.get("/", response_model=IssueListResponse)
def list_issues(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = None,
    assignee_id: int | None = None,
    creator_id: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Get all issues with filtering and pagination.
    
    - **skip**: Number of issues to skip (default: 0)
    - **limit**: Number of issues to return (default: 100, max: 1000)
    - **status**: Filter by status (open, in_progress, closed, reopened)
    - **assignee_id**: Filter by assignee ID
    - **creator_id**: Filter by creator ID
    """
    status_enum = None
    if status:
        try:
            status_enum = IssueStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid values are: open, in_progress, closed, reopened"
            )
    
    issues, total = crud.issues.get_all_issues(
        db,
        skip=skip,
        limit=limit,
        status=status_enum,
        assignee_id=assignee_id,
        creator_id=creator_id
    )
    
    return IssueListResponse(
        items=issues,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    """Get issue by ID with comments and labels."""
    issue = crud.issues.get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    return issue


@router.patch("/{issue_id}", response_model=IssueResponse)
def update_issue(issue_id: int, update_data: IssueUpdate, db: Session = Depends(get_db)):
    """
    Update an issue with optimistic locking.
    
    **IMPORTANT**: Client must send the current version. If version mismatch,
    the update will be rejected with 409 Conflict.
    
    - **title**: New title (optional)
    - **description**: New description (optional)
    - **status**: New status (optional)
    - **assignee_id**: New assignee ID (optional)
    - **version**: Current version (required for optimistic locking)
    """
    # Verify assignee exists if provided
    if update_data.assignee_id:
        assignee = crud.users.get_user_by_id(db, update_data.assignee_id)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignee with id {update_data.assignee_id} not found"
            )
    
    issue, error = crud.issues.update_issue_with_locking(db, issue_id, update_data)
    
    if error:
        if "not found" in error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        else:  # Version mismatch
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error
            )
    
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    """Delete an issue and its comments."""
    success = crud.issues.delete_issue(db, issue_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )


# ============== COMMENTS ENDPOINTS ==============

@router.post("/{issue_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(issue_id: int, comment: CommentCreate, author_id: int = Query(...), db: Session = Depends(get_db)):
    """
    Add a comment to an issue.
    
    - **issue_id**: Issue ID (in path)
    - **author_id**: ID of the comment author (query param)
    - **body**: Comment body (required, non-empty)
    """
    issue = crud.issues.get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    
    author = crud.users.get_user_by_id(db, author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id {author_id} not found"
        )
    
    try:
        return crud.comments.create_comment(db, issue_id, comment, author_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create comment"
        )


@router.get("/{issue_id}/comments", response_model=list[CommentResponse])
def get_issue_comments(
    issue_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all comments for an issue."""
    issue = crud.issues.get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    
    return crud.comments.get_comments_by_issue_id(db, issue_id, skip=skip, limit=limit)


# ============== LABELS ENDPOINTS ==============

@router.put("/{issue_id}/labels", response_model=IssueResponse)
def update_issue_labels(issue_id: int, labels_update: IssueLabelsUpdate, db: Session = Depends(get_db)):
    """
    Replace issue labels atomically.
    
    - **label_names**: List of label names to assign to the issue
    
    Rules:
    - Labels are replaced completely (not merged)
    - Labels that don't exist are created automatically
    - Operation is atomic (all-or-nothing)
    """
    issue = crud.issues.get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    
    try:
        # Start transaction
        # Clear existing labels
        issue.labels.clear()
        
        # Get or create labels
        for label_name in labels_update.label_names:
            label = crud.labels.get_or_create_label(db, label_name)
            issue.labels.append(label)
        
        db.commit()
        db.refresh(issue)
        return issue
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update labels: {str(e)}"
        )


# ============== BULK OPERATIONS ==============

@router.post("/bulk-status", response_model=BulkStatusUpdateResponse)
def bulk_update_status(request: BulkStatusUpdateRequest, db: Session = Depends(get_db)):
    """
    Update status for multiple issues atomically.
    
    Rules:
    - If any issue fails validation, entire operation is rolled back
    - Each update must include the current version for optimistic locking
    - Returns detailed results for each issue
    """
    results = []
    
    try:
        for update_item in request.updates:
            issue, error = crud.issues.update_issue_with_locking(
                db,
                update_item.issue_id,
                IssueUpdate(
                    status=update_item.status,
                    version=update_item.version
                )
            )
            
            if error:
                results.append({
                    "issue_id": update_item.issue_id,
                    "success": False,
                    "error": error
                })
            else:
                results.append({
                    "issue_id": update_item.issue_id,
                    "success": True,
                    "error": None
                })
        
        # Check if any failed
        failure_count = sum(1 for r in results if not r["success"])
        if failure_count > 0:
            # Rollback entire transaction
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bulk update failed: {failure_count} issue(s) failed validation"
            )
        
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk update failed: {str(e)}"
        )
    
    success_count = sum(1 for r in results if r["success"])
    failure_count = sum(1 for r in results if not r["success"])
    
    return BulkStatusUpdateResponse(
        results=results,
        success_count=success_count,
        failure_count=failure_count
    )
