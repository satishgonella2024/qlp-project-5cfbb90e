import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_book():
    book = {
        "title": "Test Book",
        "author": "Test Author",
        "description": "Test Description",
        "rating": 4
    }
    response = client.post("/books", json=book)
    assert response.status_code == 201
    assert response.json()["title"] == book["title"]

def test_get_books():
    response = client.get("/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_book():
    response = client.get("/books/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_update_book():
    book = {
        "title": "Updated Book",
        "author": "Updated Author",
        "description": "Updated Description",
        "rating": 5
    }
    response = client.put("/books/1", json=book)
    assert response.status_code == 200
    assert response.json()["title"] == book["title"]

def test_delete_book():
    response = client.delete("/books/1")
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted successfully"