from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import date
from models import BorrowStatus

# ==================== CATEGORY SCHEMAS ====================
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==================== BOOK SCHEMAS ====================
class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    category_id: Optional[int] = None
    total_copies: int = 1

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int
    available_copies: int
    category: Optional[CategoryResponse] = None
    model_config = ConfigDict(from_attributes=True)


# ==================== MEMBER SCHEMAS ====================
class MemberCreate(BaseModel):
    student_id: str
    name: str
    email: EmailStr

class MemberResponse(MemberCreate):
    id: int
    joined_date: date
    model_config = ConfigDict(from_attributes=True)


# ==================== BORROW & RETURN SCHEMAS ====================
class BorrowRequest(BaseModel):
    member_id: int
    book_id: int
    days_allowed: int = 14

class BorrowRecordResponse(BaseModel):
    id: int
    member_id: int
    book_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: float
    status: BorrowStatus
    book: BookResponse
    member: MemberResponse

    model_config = ConfigDict(from_attributes=True)