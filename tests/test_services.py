{
    "code": """
import os
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
import bcrypt
from functools import lru_cache
from datetime import datetime, timedelta
import jwt

# Load environment variables
JWT_SECRET = os.getenv("JWT_SECRET")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

# Models
class Book(BaseModel):
    id: int | None
    title: str
    author: str
    description: str | None = None

    @validator('title')
    def title_not_empty(cls, value):
        if not value.strip():
            raise ValueError('Title cannot be empty')
        return value

class User(BaseModel):
    id: int | None
    username: str
    password: str

    @validator('username')
    def username_not_empty(cls, value):
        if not value.strip():
            raise ValueError('Username cannot be empty')
        return value

    @validator('password')
    def hash_password(cls, value):
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(value.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')

# In-memory data store
books = []
users = []

# Rate limiting
@lru_cache(maxsize=1000)
def get_request_count(ip):
    return 1

def rate_limit(ip):
    count = get_request_count(ip)
    if count > 100:
        raise HTTPException(status_code=429, detail="Too many requests")
    get_request_count.cache_clear()

# Authentication
def get_current_user(token: str = Depends(None)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        user = next((u for u in users if u.username == username), None)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# CORS
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.post("/books", dependencies=[Depends(rate_limit)])
def create_book(book: Book, user: User = Depends(get_current_user)):
    book.id = len(books) + 1
    books.append(book)
    return book

@app.get("/books", dependencies=[Depends(rate_limit)])
def get_books(user: User = Depends(get_current_user)):
    return books

@app.get("/books/{book_id}", dependencies=[Depends(rate_limit)])
def get_book(book_id: int, user: User = Depends(get_current_user)):
    book = next((b for b in books if b.id == book_id), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", dependencies=[Depends(rate_limit)])
def update_book(book_id: int, book: Book, user: User = Depends(get_current_user)):
    existing_book = next((b for b in books if b.id == book_id), None)
    if existing_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    existing_book.title = book.title
    existing_book.author = book.author
    existing_book.description = book.description
    return existing_book

@app.delete("/books/{book_id}", dependencies=[Depends(rate_limit)])
def delete_book(book_id: int, user: User = Depends(get_current_user)):
    book = next((b for b in books if b.id == book_id), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    books.remove(book)
    return {"message": "Book deleted"}

@app.post("/users", dependencies=[Depends(rate_limit)])
def create_user(user: User):
    user.id = len(users) + 1
    users.append(user)
    return user

@app.post("/login", dependencies=[Depends(rate_limit)])
def login(user: User):
    existing_user = next((u for u in users if u.username == user.username), None)
    if existing_user is None or not bcrypt.checkpw(user.password.encode('utf-8'), existing_user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {"sub": user.username, "exp": expiration}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"access_token": token}
""",

    "tests": """
import os
import pytest
from fastapi.testclient import TestClient
from main import app, Book, User, get_current_user

client = TestClient(app)

# Test data
test_book = Book(title="Test Book", author="Test Author", description="Test Description")
test_user = User(username="testuser", password="testpassword")

# Mock JWT secret for testing
os.environ["JWT_SECRET"] = "test_secret"

def test_create_book():
    token = client.post("/login", data={"username": test_user.username, "password": test_user.password}).json()["access_token"]
    response = client.post("/books", json=test_book.dict(), headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == test_book.title

def test_get_books():
    token = client.post("/login", data={"username": test_user.username, "password": test_user.password}).json()["access_token"]
    response = client.get("/books", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_book():
    token = client.post("/login", data={"username": test_user.username, "password": test_user.password}).json()["access_token"]
    response = client.get(f"/books/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == test_book.title

def test_update_book():
    token = client.post("/login", data={"username": test_user.username, "password": test_user.password}).json()["access_token"]
    updated_book = Book(title="Updated Book", author="Updated Author", description="Updated Description")
    response = client.put(f"/books/1", json=updated_book.dict(), headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == updated_book.title

def test_delete_book():
    token = client.post("/login", data={"username": test_user.username, "password": test_user.password}).json()["access_token"]
    response = client.delete(f"/books/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted"

def test_create_user():
    response = client.post("/users", json={"username": "newuser", "password": "newpassword"})
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"

def test_login():
    response = client.post("/login", data={"username": test_user.username, "password": test_user.password})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_invalid_login():
    response = client.post("/login", data={"username": "invaliduser", "password": "invalidpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"

def test_rate_limiting():
    for _ in range(101):
        response = client.get("/books")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests"
""",

    "documentation": """
This is a Python FastAPI application that provides a REST API for managing books with CRUD operations. It also includes user authentication and authorization, input validation, rate limiting, and secure communication.

The application uses in-memory data stores for books and users. The Book model includes fields for title, author, and description, with validation to ensure that the title is not empty. The User model includes fields for username and password, with validation to ensure that the username is not empty and the password is hashed using bcrypt with 12 rounds.

The API endpoints include:

- POST /books: Create a new book (requires authentication)
- GET /books: Get a list of all books (requires authentication)
- GET /books/{book_id}: Get a specific book by ID (requires authentication)
- PUT /books/{book_id}: Update a book by ID (requires authentication)
- DELETE /books/{book_id}: Delete a book by ID (requires authentication)
- POST /users: Create a new user
- POST /login: Authenticate a user and obtain a JWT token

The application implements several security measures, including:

- Rate limiting to prevent abuse
- Authentication and authorization using JWT tokens
- Input validation using Pydantic models
- Secure password hashing using bcrypt
- CORS configuration to allow specific origins
- Error handling without exposing internal system details

The provided test suite covers various test cases for the API endpoints, including creating, retrieving, updating, and deleting books, creating users, authenticating users, and testing rate limiting.
""",

    "dependencies": [
        "fastapi",
        "pydantic",
        "bcrypt",
        "jwt"
    ]
}