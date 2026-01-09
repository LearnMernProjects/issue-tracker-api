"""
API routes for labels.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud
from app.schemas import LabelCreate, LabelResponse

router = APIRouter(prefix="/labels", tags=["labels"])


@router.post("/", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(label: LabelCreate, db: Session = Depends(get_db)):
    """
    Create a new label.
    
    - **name**: Label name (must be unique)
    """
    return crud.labels.create_label(db, label)


@router.get("/{label_id}", response_model=LabelResponse)
def get_label(label_id: int, db: Session = Depends(get_db)):
    """Get label by ID."""
    label = crud.labels.get_label_by_id(db, label_id)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found"
        )
    return label


@router.get("/", response_model=list[LabelResponse])
def list_labels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all labels with pagination."""
    if skip < 0 or limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters"
        )
    return crud.labels.get_all_labels(db, skip=skip, limit=limit)
