from pydantic import BaseModel
from datetime import date

class Book(BaseModel):
    title: str
    author: str
    isbn: str
    publication_date: date