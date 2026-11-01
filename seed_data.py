"""
Database Seeding Script
Populates the SQLite database with realistic dummy student records
for testing CRUD operations and Ollama AI queries.
"""
from datetime import date
from app.database import SessionLocal, engine, Base
from app.models import Student

DUMMY_STUDENTS = [
    {
        "student_id": "STU-1001",
        "name": "Aarav Sharma",
        "date_of_birth": date(2004, 6, 15),
        "email": "aarav.sharma@example.edu",
        "phone": "+91-9876543210",
        "course": "Computer Science",
        "address": "Mumbai, Maharashtra",
        "enrollment_date": date(2023, 8, 1)
    },
    {
        "student_id": "STU-1002",
        "name": "Diya Patel",
        "date_of_birth": date(2005, 3, 22),
        "email": "diya.patel@example.edu",
        "phone": "+91-9876543211",
        "course": "Data Analytics",
        "address": "Ahmedabad, Gujarat",
        "enrollment_date": date(2023, 8, 1)
    },
    {
        "student_id": "STU-1003",
        "name": "Rohan Gupta",
        "date_of_birth": date(2006, 11, 5),  # Born after 2005
        "email": "rohan.gupta@example.edu",
        "phone": "+91-9876543212",
        "course": "Artificial Intelligence",
        "address": "Bengaluru, Karnataka",
        "enrollment_date": date(2024, 1, 10)
    },
    {
        "student_id": "STU-1004",
        "name": "Ananya Reddy",
        "date_of_birth": date(2004, 9, 18),
        "email": "ananya.reddy@example.edu",
        "phone": "+91-9876543213",
        "course": "Computer Science",
        "address": "Hyderabad, Telangana",
        "enrollment_date": date(2023, 8, 1)
    },
    {
        "student_id": "STU-1005",
        "name": "Kabir Mehta",
        "date_of_birth": date(2007, 1, 30),  # Born after 2005
        "email": "kabir.mehta@example.edu",
        "phone": "+91-9876543214",
        "course": "Cybersecurity",
        "address": "Delhi, NCR",
        "enrollment_date": date(2024, 7, 15)
    },
    {
        "student_id": "STU-1006",
        "name": "Pooja Nair",
        "date_of_birth": date(2003, 12, 10),
        "email": "pooja.nair@example.edu",
        "phone": "+91-9876543215",
        "course": "Data Analytics",
        "address": "Kochi, Kerala",
        "enrollment_date": date(2022, 8, 1)
    },
    {
        "student_id": "STU-1007",
        "name": "Vikram Singh",
        "date_of_birth": date(2006, 5, 14),  # Born after 2005
        "email": "vikram.singh@example.edu",
        "phone": "+91-9876543216",
        "course": "Artificial Intelligence",
        "address": "Jaipur, Rajasthan",
        "enrollment_date": date(2024, 1, 10)
    },
    {
        "student_id": "STU-1008",
        "name": "Sneha Roy",
        "date_of_birth": date(2004, 2, 8),
        "email": "sneha.roy@example.edu",
        "phone": "+91-9876543217",
        "course": "Mechanical Engineering",
        "address": "Kolkata, West Bengal",
        "enrollment_date": date(2023, 8, 1)
    },
    {
        "student_id": "STU-1009",
        "name": "Arjun Kapoor",
        "date_of_birth": date(2005, 8, 25),  # Born after 2005
        "email": "arjun.kapoor@example.edu",
        "phone": "+91-9876543218",
        "course": "Computer Science",
        "address": "Chandigarh, Punjab",
        "enrollment_date": date(2023, 8, 1)
    },
    {
        "student_id": "STU-1010",
        "name": "Meera Joshi",
        "date_of_birth": date(2007, 4, 19),  # Born after 2005
        "email": "meera.joshi@example.edu",
        "phone": "+91-9876543219",
        "course": "Cybersecurity",
        "address": "Pune, Maharashtra",
        "enrollment_date": date(2024, 7, 15)
    }
]


def seed_database():
    """Initializes schema and seeds dummy students if not already present."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        inserted = 0
        for student_data in DUMMY_STUDENTS:
            existing = db.query(Student).filter(
                (Student.student_id == student_data["student_id"]) |
                (Student.email == student_data["email"])
            ).first()
            if not existing:
                student = Student(**student_data)
                db.add(student)
                inserted += 1

        db.commit()
        total = db.query(Student).count()
        print(f"Successfully seeded {inserted} dummy students. Total students in database: {total}")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
