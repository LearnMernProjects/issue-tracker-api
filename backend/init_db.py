#!/usr/bin/env python
"""
Database initialization script.
Creates all tables and optionally adds sample data.
"""
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, DATABASE_URL
from app.models import User, Issue, Label, IssueStatus
from datetime import datetime


def init_database():
    """Initialize database and create all tables."""
    print(f"Initializing database: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
    
    return engine


def add_sample_data(engine):
    """Add sample data for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        user_count = db.query(User).count()
        if user_count > 0:
            print("✓ Sample data already exists, skipping...")
            return
        
        # Create users
        user1 = User(name="Alice Johnson", email="alice@example.com")
        user2 = User(name="Bob Smith", email="bob@example.com")
        user3 = User(name="Carol Williams", email="carol@example.com")
        
        db.add_all([user1, user2, user3])
        db.commit()
        print(f"✓ Created 3 sample users")
        
        # Create labels
        label1 = Label(name="bug")
        label2 = Label(name="feature")
        label3 = Label(name="enhancement")
        label4 = Label(name="documentation")
        
        db.add_all([label1, label2, label3, label4])
        db.commit()
        print(f"✓ Created 4 sample labels")
        
        # Create issues
        issue1 = Issue(
            title="Login button not working",
            description="The login button on the homepage is not responsive to clicks",
            status=IssueStatus.OPEN,
            creator_id=user1.id,
            assignee_id=user2.id
        )
        issue1.labels = [label1]
        
        issue2 = Issue(
            title="Add dark mode",
            description="Implement dark mode for better user experience at night",
            status=IssueStatus.IN_PROGRESS,
            creator_id=user2.id,
            assignee_id=user3.id
        )
        issue2.labels = [label2, label3]
        
        issue3 = Issue(
            title="Update API documentation",
            description="Add examples and clarify authentication flow",
            status=IssueStatus.OPEN,
            creator_id=user3.id,
            assignee_id=user1.id
        )
        issue3.labels = [label4]
        
        db.add_all([issue1, issue2, issue3])
        db.commit()
        print(f"✓ Created 3 sample issues with labels")
        
        print("\n✓ Sample data initialized successfully!")
        print("\nSample data:")
        print(f"  Users: alice@example.com, bob@example.com, carol@example.com")
        print(f"  Issues: 3 issues with various statuses and labels")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error adding sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Issue Tracker database")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Add sample data for testing"
    )
    
    args = parser.parse_args()
    
    try:
        engine = init_database()
        
        if args.sample:
            add_sample_data(engine)
        else:
            print("\nTo add sample data, run with --sample flag:")
            print("  python init_db.py --sample")
        
        print("\n✓ Database initialization complete!")
        print(f"API available at: http://localhost:8000")
        print(f"Documentation: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        sys.exit(1)
