from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class StudentBase(BaseModel):
    """Base fields shared across student schemas."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student", examples=["Aarav Sharma"])
    date_of_birth: date = Field(..., description="Date of birth in YYYY-MM-DD format", examples=["2004-06-15"])
    email: EmailStr = Field(..., description="Valid contact email address", examples=["aarav.sharma@example.com"])
    phone: Optional[str] = Field(None, max_length=25, description="Contact phone number", examples=["+91-9876543210"])
    course: Optional[str] = Field(None, max_length=100, description="Enrolled course or major", examples=["Computer Science"])
    address: Optional[str] = Field(None, max_length=255, description="Residential address or city", examples=["Mumbai, Maharashtra"])
    enrollment_date: Optional[date] = Field(default_factory=date.today, description="Date of student enrollment", examples=["2024-08-01"])

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Student name must be at least 2 non-whitespace characters.")
        return clean

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("Date of birth must be a past date.")
        # Basic sanity check for student age (between 3 and 120 years old)
        age = (date.today() - v).days // 365
        if age < 3 or age > 120:
            raise ValueError("Student age must be realistic (between 3 and 120 years old).")
        return v


class StudentCreate(StudentBase):
    """Schema used to create a new student record."""
    student_id: Optional[str] = Field(
        None,
        max_length=50,
        description="Optional custom student ID. If omitted, will be auto-generated (e.g. STU-1001).",
        examples=["STU-1001"]
    )

    @field_validator("student_id")
    @classmethod
    def clean_student_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class StudentUpdate(BaseModel):
    """Schema used for PUT / PATCH updates. All fields optional for flexible updating."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, examples=["Aarav Sharma"])
    date_of_birth: Optional[date] = Field(None, examples=["2004-06-15"])
    email: Optional[EmailStr] = Field(None, examples=["aarav.updated@example.com"])
    phone: Optional[str] = Field(None, max_length=25, examples=["+91-9876543210"])
    course: Optional[str] = Field(None, max_length=100, examples=["Data Science & AI"])
    address: Optional[str] = Field(None, max_length=255, examples=["Pune, Maharashtra"])
    enrollment_date: Optional[date] = Field(None, examples=["2024-08-01"])

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if len(clean) < 2:
                raise ValueError("Student name must be at least 2 non-whitespace characters.")
            return clean
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is not None:
            if v >= date.today():
                raise ValueError("Date of birth must be a past date.")
            age = (date.today() - v).days // 365
            if age < 3 or age > 120:
                raise ValueError("Student age must be realistic (between 3 and 120 years old).")
        return v


class StudentResponse(StudentBase):
    """Schema returned in API responses representing a student."""
    id: int = Field(..., description="Internal database ID", examples=[1])
    student_id: str = Field(..., description="Unique student registration ID", examples=["STU-1001"])
    created_at: datetime = Field(..., description="Timestamp of record creation")
    updated_at: datetime = Field(..., description="Timestamp of last record update")

    model_config = ConfigDict(from_attributes=True)


class PaginatedStudentsResponse(BaseModel):
    """Paginated list of students with metadata."""
    total: int = Field(..., description="Total number of matching student records", examples=[25])
    skip: int = Field(..., description="Number of skipped items", examples=[0])
    limit: int = Field(..., description="Page limit", examples=[10])
    items: List[StudentResponse] = Field(..., description="List of student records")


class DeleteResponse(BaseModel):
    """Response returned upon successful deletion."""
    message: str = Field(..., examples=["Student STU-1001 successfully deleted."])
    student_id: str = Field(..., examples=["STU-1001"])
    id: int = Field(..., examples=[1])


class AIQueryRequest(BaseModel):
    """Natural-language question payload for the optional AI extension."""
    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Natural language question about student records",
        examples=["How many students are there?", "List students born after 2005.", "Which students are enrolled in Computer Science?"]
    )
    model: Optional[str] = Field(
        None,
        description="Optional Ollama model override (default: llama3.2:1b)",
        examples=["llama3.2:1b"]
    )


class AIQueryResponse(BaseModel):
    """Response returned by the AI extension with grounding metadata."""
    question: str
    answer: str
    model_used: str
    grounded_records_count: int
    ai_available: bool
    context_preview: Optional[str] = None
    tip: Optional[str] = None
