"""
CRUD operations for labels.
"""
from sqlalchemy.orm import Session
from app.models import Label
from app.schemas import LabelCreate


def create_label(db: Session, label: LabelCreate) -> Label:
    """Create a new label if it doesn't exist."""
    existing_label = db.query(Label).filter(Label.name == label.name).first()
    if existing_label:
        return existing_label
    
    db_label = Label(name=label.name)
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label


def get_or_create_label(db: Session, name: str) -> Label:
    """Get or create a label by name."""
    existing_label = db.query(Label).filter(Label.name == name).first()
    if existing_label:
        return existing_label
    
    db_label = Label(name=name)
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label


def get_label_by_id(db: Session, label_id: int) -> Label | None:
    """Get label by ID."""
    return db.query(Label).filter(Label.id == label_id).first()


def get_label_by_name(db: Session, name: str) -> Label | None:
    """Get label by name."""
    return db.query(Label).filter(Label.name == name).first()


def get_all_labels(db: Session, skip: int = 0, limit: int = 100):
    """Get all labels with pagination."""
    return db.query(Label).offset(skip).limit(limit).all()


def get_labels_by_names(db: Session, names: list[str]) -> list[Label]:
    """Get labels by their names."""
    return db.query(Label).filter(Label.name.in_(names)).all()
