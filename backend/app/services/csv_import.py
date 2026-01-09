"""
CSV import service for bulk issue creation.
"""
import csv
import io
from typing import BinaryIO
from sqlalchemy.orm import Session
from app.models import IssueStatus
from app import crud


class CSVImportError(Exception):
    """Exception for CSV import errors."""
    pass


def import_issues_from_csv(db: Session, file: BinaryIO) -> dict:
    """
    Import issues from CSV file.
    
    Expected CSV format:
    title,description,status,creator_id,assignee_id
    
    Rules:
    - Process all rows even if some fail
    - Track failures and reasons
    - Return summary with success/failure counts
    
    Args:
        db: Database session
        file: File object containing CSV data
        
    Returns:
        dict with keys:
            - total_rows: Total rows processed
            - success_count: Successfully imported
            - failure_count: Failed imports
            - failure_reasons: List of error messages
    """
    total_rows = 0
    success_count = 0
    failure_count = 0
    failure_reasons = []
    
    try:
        # Read CSV file
        text_stream = io.TextIOWrapper(file, encoding='utf-8')
        reader = csv.DictReader(text_stream)
        
        if not reader.fieldnames:
            raise CSVImportError("CSV file is empty or invalid")
        
        required_fields = {'title', 'creator_id'}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            raise CSVImportError(
                f"CSV must contain required fields: {required_fields}"
            )
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            total_rows += 1
            
            try:
                # Validate and parse fields
                title = row.get('title', '').strip()
                if not title:
                    raise ValueError("Title is required and cannot be empty")
                
                description = row.get('description', '').strip() or None
                
                status_str = row.get('status', 'open').strip().lower()
                try:
                    status = IssueStatus(status_str)
                except ValueError:
                    raise ValueError(
                        f"Invalid status '{status_str}'. "
                        f"Must be one of: {', '.join(s.value for s in IssueStatus)}"
                    )
                
                creator_id_str = row.get('creator_id', '').strip()
                if not creator_id_str:
                    raise ValueError("creator_id is required")
                try:
                    creator_id = int(creator_id_str)
                except ValueError:
                    raise ValueError(f"creator_id must be an integer, got '{creator_id_str}'")
                
                assignee_id = None
                assignee_id_str = row.get('assignee_id', '').strip()
                if assignee_id_str:
                    try:
                        assignee_id = int(assignee_id_str)
                    except ValueError:
                        raise ValueError(
                            f"assignee_id must be an integer, got '{assignee_id_str}'"
                        )
                
                # Verify users exist
                creator = crud.users.get_user_by_id(db, creator_id)
                if not creator:
                    raise ValueError(f"Creator user with id {creator_id} not found")
                
                if assignee_id:
                    assignee = crud.users.get_user_by_id(db, assignee_id)
                    if not assignee:
                        raise ValueError(f"Assignee user with id {assignee_id} not found")
                
                # Create issue
                from app.schemas import IssueCreate
                issue_data = IssueCreate(
                    title=title,
                    description=description,
                    status=status,
                    creator_id=creator_id,
                    assignee_id=assignee_id
                )
                crud.issues.create_issue(db, issue_data)
                success_count += 1
                
            except ValueError as e:
                failure_count += 1
                failure_reasons.append(f"Row {row_num}: {str(e)}")
            except Exception as e:
                failure_count += 1
                failure_reasons.append(f"Row {row_num}: Unexpected error: {str(e)}")
        
        db.commit()
        
    except CSVImportError as e:
        raise
    except Exception as e:
        db.rollback()
        raise CSVImportError(f"Failed to read CSV file: {str(e)}")
    
    return {
        "total_rows": total_rows,
        "success_count": success_count,
        "failure_count": failure_count,
        "failure_reasons": failure_reasons
    }
