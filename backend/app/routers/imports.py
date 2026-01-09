"""
API routes for CSV imports.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.csv_import import import_issues_from_csv, CSVImportError
from app.schemas import CSVImportResult

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/issues", response_model=CSVImportResult)
async def import_issues_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import issues from CSV file.
    
    Expected CSV format (with headers):
    ```
    title,description,status,creator_id,assignee_id
    My Issue,This is a test issue,open,1,2
    Another Issue,,in_progress,1,
    ```
    
    Rules:
    - Processes all rows even if some fail
    - Returns detailed failure reasons
    - Does NOT roll back on partial failures (continues processing)
    - All successful rows are committed
    
    Required fields:
    - title: Issue title
    - creator_id: ID of user creating the issue
    
    Optional fields:
    - description: Issue description
    - status: Issue status (open, in_progress, closed, reopened). Default: open
    - assignee_id: ID of assigned user
    
    Returns:
    - total_rows: Total data rows processed (excluding header)
    - success_count: Successfully imported
    - failure_count: Failed imports
    - failure_reasons: List of error messages for each failure
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file (.csv extension)"
        )
    
    try:
        contents = await file.read()
        import io
        file_obj = io.BytesIO(contents)
        
        result = import_issues_from_csv(db, file_obj)
        return CSVImportResult(**result)
        
    except CSVImportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import CSV: {str(e)}"
        )
