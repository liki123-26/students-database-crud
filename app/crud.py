from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
from fastapi import HTTPException, status
from app.models import Student
from app.schemas import StudentCreate, StudentUpdate


def generate_next_student_id(db: Session) -> str:
    """Generate a clean sequential unique student identifier like STU-1001."""
    # Look for the current maximum numerical suffix
    max_id = db.query(func.max(Student.id)).scalar() or 0
    next_num = 1000 + max_id + 1
    candidate = f"STU-{next_num}"

    # Ensure uniqueness in case user created custom STU-xxxx
    counter = 0
    while db.query(Student).filter(Student.student_id == candidate).first():
        counter += 1
        candidate = f"STU-{next_num + counter}"
    return candidate


def get_student_by_id(db: Session, student_pk: int) -> Optional[Student]:
    """Retrieve a student by integer primary key."""
    return db.query(Student).filter(Student.id == student_pk).first()


def get_student_by_student_id(db: Session, student_id: str) -> Optional[Student]:
    """Retrieve a student by unique student_id string."""
    return db.query(Student).filter(Student.student_id == student_id).first()


def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    """Retrieve a student by email address."""
    return db.query(Student).filter(Student.email.ilike(email)).first()


def get_student_by_identifier(db: Session, identifier: str) -> Optional[Student]:
    """
    Flexible lookup: retrieves by numeric primary key ID if integer,
    or by unique student_id code (e.g. 'STU-1001').
    """
    identifier_clean = identifier.strip()
    if identifier_clean.isdigit():
        student = get_student_by_id(db, int(identifier_clean))
        if student:
            return student
    return get_student_by_student_id(db, identifier_clean)


def get_students(
    db: Session,
    name: Optional[str] = None,
    course: Optional[str] = None,
    born_after: Optional[date] = None,
    born_before: Optional[date] = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    order: str = "asc"
) -> Tuple[List[Student], int]:
    """
    List students with optional filtering by name, course, date of birth range,
    and sorting with pagination.
    Returns (list_of_students, total_matching_records).
    """
    query = db.query(Student)

    if name:
        query = query.filter(Student.name.ilike(f"%{name.strip()}%"))

    if course:
        query = query.filter(Student.course.ilike(f"%{course.strip()}%"))

    if born_after:
        query = query.filter(Student.date_of_birth > born_after)

    if born_before:
        query = query.filter(Student.date_of_birth < born_before)

    total = query.count()

    # Dynamic sorting
    sort_col = getattr(Student, sort_by, Student.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    students = query.offset(skip).limit(limit).all()
    return students, total


def create_student(db: Session, student_in: StudentCreate) -> Student:
    """Create and persist a new student record in SQLite."""
    # Check if email is already taken
    existing_email = get_student_by_email(db, student_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A student with email '{student_in.email}' already exists (ID: {existing_email.student_id})."
        )

    # Determine student_id
    if student_in.student_id:
        existing_sid = get_student_by_student_id(db, student_in.student_id)
        if existing_sid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student ID '{student_in.student_id}' is already assigned."
            )
        sid = student_in.student_id
    else:
        sid = generate_next_student_id(db)

    db_student = Student(
        student_id=sid,
        name=student_in.name,
        date_of_birth=student_in.date_of_birth,
        email=student_in.email,
        phone=student_in.phone,
        course=student_in.course,
        address=student_in.address,
        enrollment_date=student_in.enrollment_date or date.today()
    )

    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(db: Session, db_student: Student, update_in: StudentUpdate) -> Student:
    """Update student fields."""
    update_data = update_in.model_dump(exclude_unset=True)

    # If updating email, check for duplicate
    if "email" in update_data and update_data["email"]:
        new_email = update_data["email"]
        if new_email.lower() != db_student.email.lower():
            conflict = get_student_by_email(db, new_email)
            if conflict and conflict.id != db_student.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{new_email}' is already in use by student '{conflict.student_id}'."
                )

    for field, value in update_data.items():
        setattr(db_student, field, value)

    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, db_student: Student) -> Student:
    """Remove a student record from the database."""
    db.delete(db_student)
    db.commit()
    return db_student


def get_all_students_for_ai_context(db: Session, limit: int = 100) -> List[dict]:
    """
    Safely retrieve student summaries to supply as context for Ollama AI queries.
    Does not allow arbitrary SQL execution.
    """
    students = db.query(Student).order_by(Student.id.asc()).limit(limit).all()
    return [
        {
            "student_id": s.student_id,
            "name": s.name,
            "date_of_birth": s.date_of_birth.isoformat() if s.date_of_birth else None,
            "course": s.course or "Undeclared",
            "enrollment_date": s.enrollment_date.isoformat() if s.enrollment_date else None,
            "address": s.address or "N/A"
        }
        for s in students
    ]
