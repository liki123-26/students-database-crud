from datetime import date, datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Student(Base):
    """
    SQLAlchemy ORM Model representing a Student record in SQLite.
    
    Fields:
    - id: Autoincrementing primary key
    - student_id: Unique string identifier (e.g., STU-1001)
    - name: Full name of the student
    - date_of_birth: Date of birth (YYYY-MM-DD)
    - email: Unique email address
    - phone: Contact phone number (optional)
    - course: Enrolled program / course (optional)
    - address: Residential address / city (optional)
    - enrollment_date: Date of enrollment in the course (optional)
    - created_at: Record creation timestamp
    - updated_at: Record last update timestamp
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(25), nullable=True)
    course = Column(String(100), nullable=True, index=True)
    address = Column(String(255), nullable=True)
    enrollment_date = Column(Date, nullable=True, default=date.today)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}', course='{self.course}')>"
