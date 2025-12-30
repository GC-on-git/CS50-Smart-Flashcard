"""
Tests for deck endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_token(client):
    """Create a user and return auth token."""
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    login_response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )
    return login_response.json()["access_token"]

def test_create_deck(client, auth_token):
    """Test creating a deck."""
    response = client.post(
        "/decks",
        json={
            "title": "Test Deck",
            "description": "A test deck"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Deck"
    assert data["description"] == "A test deck"
    assert "id" in data

def test_list_decks(client, auth_token):
    """Test listing decks."""
    client.post(
        "/decks",
        json={"title": "Test Deck", "description": "A test deck"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    response = client.get(
        "/decks",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Deck"

def test_get_deck(client, auth_token):
    """Test getting a specific deck."""
    create_response = client.post(
        "/decks",
        json={"title": "Test Deck", "description": "A test deck"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    deck_id = create_response.json()["id"]
    
    response = client.get(
        f"/decks/{deck_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Deck"
    assert data["id"] == deck_id

def test_update_deck(client, auth_token):
    """Test updating a deck."""
    create_response = client.post(
        "/decks",
        json={"title": "Test Deck", "description": "A test deck"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    deck_id = create_response.json()["id"]
    
    response = client.put(
        f"/decks/{deck_id}",
        json={"title": "Updated Deck", "description": "Updated description"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Deck"
    assert data["description"] == "Updated description"

def test_delete_deck(client, auth_token):
    """Test deleting a deck."""
    create_response = client.post(
        "/decks",
        json={"title": "Test Deck", "description": "A test deck"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    deck_id = create_response.json()["id"]
    
    response = client.delete(
        f"/decks/{deck_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204
    
    get_response = client.get(
        f"/decks/{deck_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 404

def test_search_decks(client, auth_token):
    """Test searching decks."""
    client.post(
        "/decks",
        json={"title": "Python Basics", "description": "Python fundamentals"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    client.post(
        "/decks",
        json={"title": "JavaScript Advanced", "description": "Advanced JS"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    response = client.get(
        "/decks?query=Python",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Python" in data[0]["title"]

def test_create_deck_unauthorized(client):
    """Test creating deck without authentication."""
    response = client.post(
        "/decks",
        json={"title": "Test Deck", "description": "A test deck"}
    )
    assert response.status_code == 401

