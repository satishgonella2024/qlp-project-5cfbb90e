from fastapi import APIRouter, HTTPException
from models import Book
from typing import List
from database import books

book_router = APIRouter()

@book_router.post("/books", status_code=201)
def create_book(book: Book):
    # Input validation
    if len(book.title) > 100:
        raise HTTPException(status_code=400, detail="Title must be less than 100 characters")
    if len(book.author) > 50:
        raise HTTPException(status_code=400, detail="Author must be less than 50 characters")
    if len(book.description) > 500:
        raise HTTPException(status_code=400, detail="Description must be less than 500 characters")

    book.id = len(books) + 1
    books.append(book.dict())
    return book

@book_router.get("/books", response_model=List[Book])
def get_books():
    return books

@book_router.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return Book(**book)
    raise HTTPException(status_code=404, detail="Book not found")

@book_router.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: Book):
    for i, b in enumerate(books):
        if b["id"] == book_id:
            books[i] = book.dict()
            return book
    raise HTTPException(status_code=404, detail="Book not found")

@book_router.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    for i, book in enumerate(books):
        if book["id"] == book_id:
            del books[i]
            return

    raise HTTPException(status_code=404, detail="Book not found")