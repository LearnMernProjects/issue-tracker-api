"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class IssueStatusEnum(str, Enum):
    """Issue status enum for schemas."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    REOPENED = "reopened"


# ============== USER SCHEMAS ==============

class UserBase(BaseModel):
    """Base user schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== LABEL SCHEMAS ==============

class LabelBase(BaseModel):
    """Base label schema."""
    name: str = Field(..., min_length=1, max_length=100)


class LabelCreate(LabelBase):
    """Schema for creating a label."""
    pass


class LabelResponse(LabelBase):
    """Schema for label response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== COMMENT SCHEMAS ==============

class CommentBase(BaseModel):
    """Base comment schema."""
    body: str = Field(..., min_length=1)

    @validator('body')
    def body_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment body cannot be empty')
        return v.strip()


class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    pass


class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: int
    issue_id: int
    author_id: int
    author: UserResponse
    created_at: datetime

    class Config:
        from_attributes = True


# ============== ISSUE SCHEMAS ==============

class IssueBase(BaseModel):
    """Base issue schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    status: IssueStatusEnum = IssueStatusEnum.OPEN
    assignee_id: Optional[int] = None


class IssueCreate(IssueBase):
    """Schema for creating an issue."""
    creator_id: int


class IssueUpdate(BaseModel):
    """Schema for updating an issue with optimistic locking."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    status: Optional[IssueStatusEnum] = None
    assignee_id: Optional[int] = None
    version: int = Field(..., description="Current version for optimistic locking")


class IssueResponse(IssueBase):
    """Schema for issue response."""
    id: int
    creator_id: int
    version: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    creator: UserResponse
    assignee: Optional[UserResponse] = None
    comments: List[CommentResponse] = []
    labels: List[LabelResponse] = []

    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    """Schema for list of issues with pagination."""
    items: List[IssueResponse]
    total: int
    skip: int
    limit: int


# ============== LABEL UPDATE SCHEMAS ==============

class IssueLabelsUpdate(BaseModel):
    """Schema for updating issue labels."""
    label_names: List[str] = Field(..., min_items=0, max_items=100)

    @validator('label_names')
    def validate_label_names(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate label names')
        for name in v:
            if not name or not name.strip():
                raise ValueError('Label name cannot be empty')
        return [name.strip() for name in v]


# ============== BULK OPERATIONS SCHEMAS ==============

class BulkStatusUpdateItem(BaseModel):
    """Schema for single item in bulk status update."""
    issue_id: int
    status: IssueStatusEnum
    version: int


class BulkStatusUpdateRequest(BaseModel):
    """Schema for bulk status update request."""
    updates: List[BulkStatusUpdateItem] = Field(..., min_items=1, max_items=1000)


class BulkStatusUpdateResult(BaseModel):
    """Schema for bulk status update result."""
    issue_id: int
    success: bool
    error: Optional[str] = None


class BulkStatusUpdateResponse(BaseModel):
    """Schema for bulk status update response."""
    results: List[BulkStatusUpdateResult]
    success_count: int
    failure_count: int


# ============== CSV IMPORT SCHEMAS ==============

class CSVImportResult(BaseModel):
    """Schema for CSV import result."""
    total_rows: int
    success_count: int
    failure_count: int
    failure_reasons: List[str] = []


# ============== REPORTS SCHEMAS ==============

class TopAssigneeReport(BaseModel):
    """Schema for top assignee report."""
    assignee_name: str
    assignee_email: str
    issue_count: int
    open_issues: int
    closed_issues: int


class TopAssigneesResponse(BaseModel):
    """Schema for top assignees response."""
    top_assignees: List[TopAssigneeReport]


class LatencyReport(BaseModel):
    """Schema for latency report (time to resolution)."""
    status: str
    average_latency_hours: float
    median_latency_hours: float
    max_latency_hours: float
    sample_size: int


class LatencyReportsResponse(BaseModel):
    """Schema for latency reports response."""
    reports: List[LatencyReport]
