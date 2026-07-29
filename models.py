from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from database import Base

class BorrowStatus(str, PyEnum):
    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    books = relationship("Book", back_populates="category", cascade="all, delete")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(50), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)

    category = relationship("Category", back_populates="books")
    borrow_records = relationship("BorrowRecord", back_populates="book")

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    joined_date = Column(Date, default=date.today)

    borrow_records = relationship("BorrowRecord", back_populates="member")

class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    borrow_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    fine_amount = Column(Float, default=0.0)
    # models.py
    status = Column(String(20), default="BORROWED", nullable=False)
    

    member = relationship("Member", back_populates="borrow_records")
    book = relationship("Book", back_populates="borrow_records")