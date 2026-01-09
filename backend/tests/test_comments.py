"""
Tests for comments endpoints.
"""
import pytest


class TestCommentCreate:
    """Tests for comment creation."""
    
    def test_create_comment(self, client, sample_issue, sample_user):
        response = client.post(
            f"/issues/{sample_issue.id}/comments",
            json={"body": "This is a comment"},
            params={"author_id": sample_user.id}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["body"] == "This is a comment"
        assert data["issue_id"] == sample_issue.id
        assert data["author"]["id"] == sample_user.id
    
    def test_create_comment_empty_body(self, client, sample_issue, sample_user):
        response = client.post(
            f"/issues/{sample_issue.id}/comments",
            json={"body": ""},
            params={"author_id": sample_user.id}
        )
        assert response.status_code == 422
    
    def test_create_comment_nonexistent_issue(self, client, sample_user):
        response = client.post(
            "/issues/999/comments",
            json={"body": "This is a comment"},
            params={"author_id": sample_user.id}
        )
        assert response.status_code == 404
    
    def test_create_comment_nonexistent_author(self, client, sample_issue):
        response = client.post(
            f"/issues/{sample_issue.id}/comments",
            json={"body": "This is a comment"},
            params={"author_id": 999}
        )
        assert response.status_code == 404


class TestCommentGet:
    """Tests for comment retrieval."""
    
    def test_get_issue_comments(self, client, sample_issue, sample_user):
        # Create comments
        client.post(
            f"/issues/{sample_issue.id}/comments",
            json={"body": "Comment 1"},
            params={"author_id": sample_user.id}
        )
        client.post(
            f"/issues/{sample_issue.id}/comments",
            json={"body": "Comment 2"},
            params={"author_id": sample_user.id}
        )
        
        response = client.get(f"/issues/{sample_issue.id}/comments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["body"] == "Comment 1"
        assert data[1]["body"] == "Comment 2"
    
    def test_get_comments_nonexistent_issue(self, client):
        response = client.get("/issues/999/comments")
        assert response.status_code == 404
