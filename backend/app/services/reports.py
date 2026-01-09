"""
Report queries and services.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from app.models import Issue, IssueStatus, User


def get_top_assignees(db: Session, limit: int = 10) -> list[dict]:
    """
    Get top assignees by number of assigned issues.
    
    Returns list of dicts with:
    - assignee_name
    - assignee_email
    - issue_count
    - open_issues
    - closed_issues
    """
    results = db.query(
        User.name.label('assignee_name'),
        User.email.label('assignee_email'),
        func.count(Issue.id).label('issue_count'),
        func.sum(
            case((Issue.status == IssueStatus.OPEN, 1), else_=0)
        ).label('open_issues'),
        func.sum(
            case((Issue.status == IssueStatus.CLOSED, 1), else_=0)
        ).label('closed_issues')
    ).join(
        Issue, Issue.assignee_id == User.id
    ).group_by(
        User.id, User.name, User.email
    ).order_by(
        func.count(Issue.id).desc()
    ).limit(limit).all()
    
    return [
        {
            'assignee_name': r.assignee_name,
            'assignee_email': r.assignee_email,
            'issue_count': r.issue_count or 0,
            'open_issues': r.open_issues or 0,
            'closed_issues': r.closed_issues or 0
        }
        for r in results
    ]


def get_resolution_latency(db: Session) -> list[dict]:
    """
    Get issue resolution latency statistics by status.
    
    Only includes closed issues (where resolved_at is set).
    Calculates latency in hours.
    
    Returns list of dicts with:
    - status: Issue status
    - average_latency_hours
    - median_latency_hours
    - max_latency_hours
    - sample_size
    """
    from sqlalchemy import and_, func as sqla_func
    from datetime import datetime
    
    # Subquery to calculate latencies in hours
    latency_subquery = db.query(
        Issue.status,
        (extract('epoch', Issue.resolved_at - Issue.created_at) / 3600).label('latency_hours')
    ).filter(
        Issue.resolved_at.isnot(None),
        Issue.status == IssueStatus.CLOSED
    ).subquery()
    
    results = db.query(
        latency_subquery.c.status,
        func.avg(latency_subquery.c.latency_hours).label('avg_latency'),
        func.max(latency_subquery.c.latency_hours).label('max_latency'),
        func.count(latency_subquery.c.latency_hours).label('sample_size')
    ).group_by(
        latency_subquery.c.status
    ).all()
    
    output = []
    for r in results:
        # For median, we need a separate query per status
        median_result = db.query(
            func.percentile_cont(0.5).within_group(
                Issue.resolved_at - Issue.created_at
            ).label('median_interval')
        ).filter(
            Issue.status == r.status,
            Issue.resolved_at.isnot(None)
        ).first()
        
        median_hours = 0
        if median_result and median_result.median_interval:
            # Convert timedelta to hours
            median_hours = median_result.median_interval.total_seconds() / 3600
        
        output.append({
            'status': r.status.value if r.status else 'unknown',
            'average_latency_hours': float(r.avg_latency or 0),
            'median_latency_hours': float(median_hours),
            'max_latency_hours': float(r.max_latency or 0),
            'sample_size': r.sample_size or 0
        })
    
    return output
