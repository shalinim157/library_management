from datetime import date, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import engine, Base, get_db
import models
import schemas

# Create DB Tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library Management System")

# Mount Static & Template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DAILY_FINE_RATE = 5.00  # $5.00 per day past due date

# ==================== PAGE ROUTE ====================
# ✅ NEW (Updated syntax for modern FastAPI)
@app.get("/")
def serve_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# ==================== CATEGORIES ====================
@app.post("/api/categories", response_model=schemas.CategoryResponse, status_code=210)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Category).filter(models.Category.name.ilike(category.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists.")
    
    db_cat = models.Category(**category.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@app.get("/api/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

# ==================== MEMBERS ====================
@app.post("/api/members", response_model=schemas.MemberResponse, status_code=201)
def register_member(member: schemas.MemberCreate, db: Session = Depends(get_db)):
    if db.query(models.Member).filter(models.Member.student_id == member.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered.")
    if db.query(models.Member).filter(models.Member.email == member.email).first():
        raise HTTPException(status_code=400, detail="Email address already in use.")

    db_member = models.Member(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@app.get("/api/members", response_model=List[schemas.MemberResponse])
def list_members(db: Session = Depends(get_db)):
    return db.query(models.Member).all()

# ==================== BOOKS ====================
@app.post("/api/books", response_model=schemas.BookResponse, status_code=201)
def add_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    if db.query(models.Book).filter(models.Book.isbn == book.isbn).first():
        raise HTTPException(status_code=400, detail="A book with this ISBN already exists.")

    if book.category_id:
        if not db.query(models.Category).filter(models.Category.id == book.category_id).first():
            raise HTTPException(status_code=404, detail="Selected category not found.")

    db_book = models.Book(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        category_id=book.category_id,
        total_copies=book.total_copies,
        available_copies=book.total_copies
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/api/books", response_model=List[schemas.BookResponse])
def search_books(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Book)
    if category_id:
        query = query.filter(models.Book.category_id == category_id)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(models.Book.title.ilike(term), models.Book.author.ilike(term), models.Book.isbn.ilike(term)))
    return query.all()

# ==================== BORROW & RETURN ====================
@app.post("/api/borrow", response_model=schemas.BorrowRecordResponse)
def borrow_book(req: schemas.BorrowRequest, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == req.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member/Student not found.")

    book = db.query(models.Book).filter(models.Book.id == req.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No available copies left for this book.")

    # Check if student already holds an unreturned copy
    existing = db.query(models.BorrowRecord).filter(
        models.BorrowRecord.member_id == req.member_id,
        models.BorrowRecord.book_id == req.book_id,
        models.BorrowRecord.status == models.BorrowStatus.BORROWED
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student has already borrowed this book and not returned it.")

    # Process borrowing
    book.available_copies -= 1
    borrow_date = date.today()
    due_date = borrow_date + timedelta(days=req.days_allowed)

    record = models.BorrowRecord(
        member_id=req.member_id,
        book_id=req.book_id,
        borrow_date=borrow_date,
        due_date=due_date,
        status=models.BorrowStatus.BORROWED
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# Change status_code=210 to status_code=201
@app.post("/api/categories", response_model=schemas.CategoryResponse, status_code=201)
def return_book(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.BorrowRecord).filter(models.BorrowRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Borrow record not found.")

    if record.status == models.BorrowStatus.RETURNED:
        raise HTTPException(status_code=400, detail="Book has already been returned.")

    today = date.today()
    record.return_date = today
    record.status = models.BorrowStatus.RETURNED

    # Calculate fine ($5/day past due date)
    if today > record.due_date:
        overdue_days = (today - record.due_date).days
        record.fine_amount = overdue_days * DAILY_FINE_RATE
    else:
        record.fine_amount = 0.0

    # Restock book copy
    book = db.query(models.Book).filter(models.Book.id == record.book_id).first()
    if book:
        book.available_copies += 1

    db.commit()
    db.refresh(record)
    return record

@app.get("/api/records", response_model=List[schemas.BorrowRecordResponse])
def get_borrow_records(member_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.BorrowRecord)
    if member_id:
        query = query.filter(models.BorrowRecord.member_id == member_id)
    return query.order_by(models.BorrowRecord.id.desc()).all()
# main.py
@app.post("/api/return/{record_id}", response_model=schemas.BorrowRecordResponse)
def return_book(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.BorrowRecord).filter(models.BorrowRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Borrow record not found.")

    if str(record.status) == "RETURNED" or record.status == models.BorrowStatus.RETURNED:
        raise HTTPException(status_code=400, detail="Book has already been returned.")

    today = date.today()
    record.return_date = today
    record.status = models.BorrowStatus.RETURNED

    if today > record.due_date:
        overdue_days = (today - record.due_date).days
        record.fine_amount = float(overdue_days * DAILY_FINE_RATE)
    else:
        record.fine_amount = 0.0

    book = db.query(models.Book).filter(models.Book.id == record.book_id).first()
    if book:
        book.available_copies += 1

    db.commit()
    db.refresh(record)
    return record