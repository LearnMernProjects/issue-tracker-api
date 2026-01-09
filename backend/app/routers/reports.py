"""
API routes for reports and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import reports
from app.schemas import TopAssigneesResponse, TopAssigneeReport, LatencyReportsResponse, LatencyReport

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/top-assignees", response_model=TopAssigneesResponse)
def get_top_assignees(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top assignees by number of assigned issues.
    
    Returns assignees sorted by issue count in descending order.
    Includes breakdown of open vs closed issues.
    
    - **limit**: Number of top assignees to return (default: 10, max: 100)
    """
    if limit <= 0 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100"
        )
    
    top_assignees = reports.get_top_assignees(db, limit=limit)
    return TopAssigneesResponse(
        top_assignees=[TopAssigneeReport(**item) for item in top_assignees]
    )


@router.get("/latency", response_model=LatencyReportsResponse)
def get_latency_reports(db: Session = Depends(get_db)):
    """
    Get issue resolution latency statistics.
    
    Shows average, median, and max time to resolution for closed issues.
    Helps identify bottlenecks and performance trends.
    """
    try:
        latency_data = reports.get_resolution_latency(db)
        return LatencyReportsResponse(
            reports=[LatencyReport(**item) for item in latency_data]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate latency reports: {str(e)}"
        )
