"""
Tests for CSV import functionality.
"""
import pytest
import io


class TestCSVImport:
    """Tests for CSV import endpoint."""
    
    def test_import_csv_success(self, client, sample_user):
        csv_content = b"""title,description,creator_id
Test Issue 1,Description 1,1
Test Issue 2,Description 2,1
"""
        response = client.post(
            "/imports/issues",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["success_count"] == 2
        assert data["failure_count"] == 0
    
    def test_import_csv_with_failures(self, client, sample_user):
        csv_content = b"""title,description,creator_id
Test Issue,Description,1
,No Title,1
Invalid Creator,,999
"""
        response = client.post(
            "/imports/issues",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 3
        assert data["success_count"] == 1
        assert data["failure_count"] == 2
        assert len(data["failure_reasons"]) > 0
    
    def test_import_csv_with_status(self, client, sample_user):
        csv_content = b"""title,creator_id,status
Open Issue,1,open
In Progress Issue,1,in_progress
Closed Issue,1,closed
"""
        response = client.post(
            "/imports/issues",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
    
    def test_import_csv_with_assignee(self, client, sample_user, sample_assignee):
        csv_content = b"""title,creator_id,assignee_id
Test Issue,1,2
"""
        response = client.post(
            "/imports/issues",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
    
    def test_import_csv_invalid_file_type(self, client):
        response = client.post(
            "/imports/issues",
            files={"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")}
        )
        assert response.status_code == 400
    
    def test_import_csv_missing_required_field(self, client):
        csv_content = b"""description,status
This has no title,open
"""
        response = client.post(
            "/imports/issues",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert response.status_code == 400
