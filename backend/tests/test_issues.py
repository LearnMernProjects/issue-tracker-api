"""
Tests for issue endpoints and optimistic locking.
"""
import pytest


class TestIssueCreate:
    """Tests for issue creation."""
    
    def test_create_issue(self, client, sample_user):
        response = client.post("/issues/", json={
            "title": "Test Issue",
            "description": "Test description",
            "creator_id": sample_user.id
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Issue"
        assert data["status"] == "open"
        assert data["version"] == 1
    
    def test_create_issue_with_assignee(self, client, sample_user, sample_assignee):
        response = client.post("/issues/", json={
            "title": "Test Issue",
            "description": "Test description",
            "creator_id": sample_user.id,
            "assignee_id": sample_assignee.id
        })
        assert response.status_code == 201
        data = response.json()
        assert data["assignee"]["id"] == sample_assignee.id
    
    def test_create_issue_invalid_creator(self, client):
        response = client.post("/issues/", json={
            "title": "Test Issue",
            "creator_id": 999
        })
        assert response.status_code == 404
    
    def test_create_issue_invalid_assignee(self, client, sample_user):
        response = client.post("/issues/", json={
            "title": "Test Issue",
            "creator_id": sample_user.id,
            "assignee_id": 999
        })
        assert response.status_code == 404


class TestIssueGet:
    """Tests for issue retrieval."""
    
    def test_get_issue(self, client, sample_issue):
        response = client.get(f"/issues/{sample_issue.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_issue.id
        assert data["title"] == "Sample Issue"
        assert "comments" in data
        assert "labels" in data
    
    def test_get_nonexistent_issue(self, client):
        response = client.get("/issues/999")
        assert response.status_code == 404
    
    def test_list_issues(self, client, sample_user):
        client.post("/issues/", json={
            "title": "Issue 1",
            "creator_id": sample_user.id
        })
        client.post("/issues/", json={
            "title": "Issue 2",
            "creator_id": sample_user.id
        })
        
        response = client.get("/issues/?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
    
    def test_list_issues_filter_by_status(self, client, sample_user):
        response = client.post("/issues/", json={
            "title": "Open Issue",
            "creator_id": sample_user.id,
            "status": "open"
        })
        issue_id = response.json()["id"]
        
        response = client.get("/issues/?status=open")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == issue_id
    
    def test_list_issues_invalid_status(self, client):
        response = client.get("/issues/?status=invalid")
        assert response.status_code == 400


class TestIssueUpdate:
    """Tests for issue updates with optimistic locking."""
    
    def test_update_issue_success(self, client, sample_issue):
        response = client.patch(f"/issues/{sample_issue.id}", json={
            "title": "Updated Title",
            "version": sample_issue.version
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["version"] == 2  # Version incremented
    
    def test_update_issue_version_mismatch(self, client, sample_issue):
        response = client.patch(f"/issues/{sample_issue.id}", json={
            "title": "Updated Title",
            "version": sample_issue.version + 10  # Wrong version
        })
        assert response.status_code == 409  # Conflict
        assert "Version mismatch" in response.json()["detail"]
    
    def test_update_issue_status(self, client, sample_issue):
        response = client.patch(f"/issues/{sample_issue.id}", json={
            "status": "in_progress",
            "version": sample_issue.version
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
    
    def test_update_issue_close_sets_resolved_at(self, client, sample_issue):
        response = client.patch(f"/issues/{sample_issue.id}", json={
            "status": "closed",
            "version": sample_issue.version
        })
        assert response.status_code == 200
        data = response.json()
        assert data["resolved_at"] is not None
    
    def test_update_nonexistent_issue(self, client):
        response = client.patch("/issues/999", json={
            "title": "Updated",
            "version": 1
        })
        assert response.status_code == 404


class TestIssueDelete:
    """Tests for issue deletion."""
    
    def test_delete_issue(self, client, sample_issue):
        response = client.delete(f"/issues/{sample_issue.id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        response = client.get(f"/issues/{sample_issue.id}")
        assert response.status_code == 404
    
    def test_delete_nonexistent_issue(self, client):
        response = client.delete("/issues/999")
        assert response.status_code == 404
