Here is the Python code for the book models:

from pydantic import BaseModel
from datetime import date

class Book(BaseModel):
    title: str
    author: str
    isbn: str
    publication_date: date

This defines a Pydantic model for a book, with fields for the title, author, ISBN, and publication date. The Pydantic library is used to define the data model and perform data validation.