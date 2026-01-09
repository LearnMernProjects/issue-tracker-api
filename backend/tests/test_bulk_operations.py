"""
Tests for labels and bulk operations.
"""
import pytest


class TestLabels:
    """Tests for label operations."""
    
    def test_create_label(self, client):
        response = client.post("/labels/", json={"name": "bug"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "bug"
    
    def test_create_duplicate_label(self, client):
        client.post("/labels/", json={"name": "bug"})
        response = client.post("/labels/", json={"name": "bug"})
        # Should return existing label, not error
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "bug"
    
    def test_update_issue_labels(self, client, sample_issue):
        response = client.put(
            f"/issues/{sample_issue.id}/labels",
            json={"label_names": ["bug", "critical"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) == 2
        label_names = [l["name"] for l in data["labels"]]
        assert "bug" in label_names
        assert "critical" in label_names
    
    def test_update_issue_labels_creates_new(self, client, sample_issue):
        response = client.put(
            f"/issues/{sample_issue.id}/labels",
            json={"label_names": ["new-label"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) == 1
        assert data["labels"][0]["name"] == "new-label"
    
    def test_update_issue_labels_replaces(self, client, sample_issue):
        # Add initial labels
        client.put(
            f"/issues/{sample_issue.id}/labels",
            json={"label_names": ["bug"]}
        )
        
        # Replace with different labels
        response = client.put(
            f"/issues/{sample_issue.id}/labels",
            json={"label_names": ["feature", "enhancement"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) == 2
        label_names = [l["name"] for l in data["labels"]]
        assert "bug" not in label_names
        assert "feature" in label_names
    
    def test_clear_issue_labels(self, client, sample_issue):
        # Add labels first
        client.put(
            f"/issues/{sample_issue.id}/labels",
            json={"label_names": ["bug"]}
        )
        
        # Clear labels
        response = client.put(
            f"/issues/{sample_issue.id}/labels",
            json={"label_names": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) == 0


class TestBulkOperations:
    """Tests for bulk status updates."""
    
    def test_bulk_status_update_success(self, client, sample_user):
        # Create multiple issues
        issue1_response = client.post("/issues/", json={
            "title": "Issue 1",
            "creator_id": sample_user.id
        })
        issue1_id = issue1_response.json()["id"]
        issue1_version = issue1_response.json()["version"]
        
        issue2_response = client.post("/issues/", json={
            "title": "Issue 2",
            "creator_id": sample_user.id
        })
        issue2_id = issue2_response.json()["id"]
        issue2_version = issue2_response.json()["version"]
        
        # Bulk update
        response = client.post("/issues/bulk-status", json={
            "updates": [
                {"issue_id": issue1_id, "status": "in_progress", "version": issue1_version},
                {"issue_id": issue2_id, "status": "closed", "version": issue2_version}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2
        assert data["failure_count"] == 0
        
        # Verify updates
        response = client.get(f"/issues/{issue1_id}")
        assert response.json()["status"] == "in_progress"
    
    def test_bulk_status_update_version_mismatch_fails(self, client, sample_user):
        # Create issue
        issue_response = client.post("/issues/", json={
            "title": "Test Issue",
            "creator_id": sample_user.id
        })
        issue_id = issue_response.json()["id"]
        
        # Try bulk update with wrong version
        response = client.post("/issues/bulk-status", json={
            "updates": [
                {"issue_id": issue_id, "status": "in_progress", "version": 999}
            ]
        })
        assert response.status_code == 400
    
    def test_bulk_status_update_invalid_issue(self, client):
        response = client.post("/issues/bulk-status", json={
            "updates": [
                {"issue_id": 999, "status": "in_progress", "version": 1}
            ]
        })
        assert response.status_code == 400
