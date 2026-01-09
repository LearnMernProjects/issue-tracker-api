"""
Tests for user endpoints.
"""
import pytest


class TestUserCreate:
    """Tests for user creation."""
    
    def test_create_user(self, client):
        response = client.post("/users/", json={
            "name": "John Doe",
            "email": "john@example.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["id"] is not None
        assert "created_at" in data
    
    def test_create_duplicate_email(self, client):
        client.post("/users/", json={
            "name": "John Doe",
            "email": "john@example.com"
        })
        response = client.post("/users/", json={
            "name": "Jane Doe",
            "email": "john@example.com"
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_user_invalid_email(self, client):
        response = client.post("/users/", json={
            "name": "John Doe",
            "email": "invalid-email"
        })
        assert response.status_code == 422
    
    def test_create_user_empty_name(self, client):
        response = client.post("/users/", json={
            "name": "",
            "email": "john@example.com"
        })
        assert response.status_code == 422


class TestUserGet:
    """Tests for user retrieval."""
    
    def test_get_user(self, client, sample_user):
        response = client.get(f"/users/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["email"] == "test@example.com"
    
    def test_get_nonexistent_user(self, client):
        response = client.get("/users/999")
        assert response.status_code == 404
    
    def test_list_users(self, client):
        client.post("/users/", json={"name": "User 1", "email": "user1@example.com"})
        client.post("/users/", json={"name": "User 2", "email": "user2@example.com"})
        
        response = client.get("/users/?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_list_users_pagination(self, client):
        for i in range(5):
            client.post("/users/", json={
                "name": f"User {i}",
                "email": f"user{i}@example.com"
            })
        
        response = client.get("/users/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
