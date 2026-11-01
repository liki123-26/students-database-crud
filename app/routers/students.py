from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Student
from app.schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    PaginatedStudentsResponse,
    DeleteResponse
)
from app import crud

router = APIRouter(
    prefix="/students",
    tags=["Students CRUD"]
)


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student",
    description="Adds a new student record to the SQLite database. If `student_id` is omitted, it will be automatically generated (e.g. STU-1001)."
)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db)
):
    return crud.create_student(db, student_in)


@router.get(
    "",
    response_model=PaginatedStudentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter students",
    description="Retrieve students with optional search filters (name, course, date of birth range) and pagination (skip, limit)."
)
def list_students(
    name: Optional[str] = Query(None, description="Case-insensitive partial match on student name"),
    course: Optional[str] = Query(None, description="Case-insensitive filter by course name"),
    born_after: Optional[date] = Query(None, description="Filter students born strictly after this date (YYYY-MM-DD)"),
    born_before: Optional[date] = Query(None, description="Filter students born strictly before this date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of records to return"),
    sort_by: str = Query("id", pattern="^(id|name|date_of_birth|enrollment_date)$", description="Field to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    students, total = crud.get_students(
        db,
        name=name,
        course=course,
        born_after=born_after,
        born_before=born_before,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order
    )
    return PaginatedStudentsResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=students
    )


@router.get(
    "/stats/summary",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get student statistics summary",
    description="Returns aggregate statistics including total student count and breakdown by course."
)
def get_students_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Student.id)).scalar() or 0
    courses_query = (
        db.query(Student.course, func.count(Student.id))
        .group_by(Student.course)
        .all()
    )
    courses_breakdown = {
        (course or "Unassigned"): count for course, count in courses_query
    }
    return {
        "total_students": total,
        "courses_breakdown": courses_breakdown
    }


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="View student by ID",
    description="Retrieve a single student record using either database primary key (e.g. `1`) or unique student registration ID (e.g. `STU-1001`)."
)
def get_student(
    student_id: str,
    db: Session = Depends(get_db)
):
    student = crud.get_student_by_identifier(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found."
        )
    return student


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student details (Full or Partial)",
    description="Update an existing student's details using either primary key or student ID."
)
def update_student_put(
    student_id: str,
    student_in: StudentUpdate,
    db: Session = Depends(get_db)
):
    student = crud.get_student_by_identifier(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found."
        )
    return crud.update_student(db, student, student_in)


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially modify student details",
    description="Patch specific fields of an existing student's details."
)
def update_student_patch(
    student_id: str,
    student_in: StudentUpdate,
    db: Session = Depends(get_db)
):
    student = crud.get_student_by_identifier(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found."
        )
    return crud.update_student(db, student, student_in)


@router.delete(
    "/{student_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a student",
    description="Remove a student record permanently from the SQLite database."
)
def delete_student(
    student_id: str,
    db: Session = Depends(get_db)
):
    student = crud.get_student_by_identifier(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found."
        )
    deleted_id = student.id
    deleted_sid = student.student_id
    crud.delete_student(db, student)
    return DeleteResponse(
        message=f"Student '{student.name}' ({deleted_sid}) has been successfully deleted.",
        student_id=deleted_sid,
        id=deleted_id
    )
