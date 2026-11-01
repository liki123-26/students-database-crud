from datetime import date
import pytest


def test_root_endpoint(client):
    """Test API root welcome endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data


def test_create_student_success(client):
    """Test creating a student with valid fields."""
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2004-06-15",
        "email": "aarav.sharma@example.com",
        "phone": "+91-9876543210",
        "course": "Computer Science",
        "address": "Mumbai, Maharashtra"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aarav Sharma"
    assert data["email"] == "aarav.sharma@example.com"
    assert data["student_id"].startswith("STU-")
    assert "id" in data


def test_create_student_custom_id(client):
    """Test creating a student with a custom student ID."""
    payload = {
        "student_id": "CUSTOM-001",
        "name": "Diya Patel",
        "date_of_birth": "2005-03-22",
        "email": "diya.patel@example.com",
        "course": "Data Analytics"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == "CUSTOM-001"


def test_create_student_duplicate_email(client):
    """Test duplicate email rejection (400 Bad Request)."""
    payload = {
        "name": "Student One",
        "date_of_birth": "2004-01-01",
        "email": "duplicate@example.com"
    }
    resp1 = client.post("/students", json=payload)
    assert resp1.status_code == 201

    payload2 = {
        "name": "Student Two",
        "date_of_birth": "2004-05-05",
        "email": "duplicate@example.com"
    }
    resp2 = client.post("/students", json=payload2)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]


def test_create_student_invalid_data(client):
    """Test validation errors for invalid email and future birth date."""
    # Invalid email
    invalid_email = {
        "name": "Bad Email",
        "date_of_birth": "2004-01-01",
        "email": "not-an-email"
    }
    res = client.post("/students", json=invalid_email)
    assert res.status_code == 422

    # Future birth date
    future_dob = {
        "name": "Time Traveler",
        "date_of_birth": "2099-01-01",
        "email": "future@example.com"
    }
    res2 = client.post("/students", json=future_dob)
    assert res2.status_code == 422


def test_get_and_filter_students(client):
    """Test listing, filtering by course and date of birth, and pagination."""
    # Seed 3 students
    students = [
        {"name": "Alice CS", "date_of_birth": "2004-01-01", "email": "alice@ex.com", "course": "Computer Science"},
        {"name": "Bob Data", "date_of_birth": "2006-05-10", "email": "bob@ex.com", "course": "Data Analytics"},
        {"name": "Charlie CS", "date_of_birth": "2007-08-20", "email": "charlie@ex.com", "course": "Computer Science"}
    ]
    for s in students:
        client.post("/students", json=s)

    # 1. List all
    res = client.get("/students")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3

    # 2. Filter by course
    res_cs = client.get("/students?course=Computer%20Science")
    assert res_cs.status_code == 200
    body_cs = res_cs.json()
    assert body_cs["total"] == 2
    assert all(item["course"] == "Computer Science" for item in body_cs["items"])

    # 3. Filter by born_after (2005-01-01)
    res_after = client.get("/students?born_after=2005-01-01")
    assert res_after.status_code == 200
    body_after = res_after.json()
    assert body_after["total"] == 2  # Bob (2006) and Charlie (2007)

    # 4. Search by name
    res_name = client.get("/students?name=Bob")
    assert res_name.status_code == 200
    assert res_name.json()["total"] == 1


def test_get_student_by_id_and_code(client):
    """Test fetching single student by numeric ID and string student_id."""
    created = client.post("/students", json={
        "student_id": "STU-9999",
        "name": "Target Student",
        "date_of_birth": "2003-11-12",
        "email": "target@example.com"
    }).json()

    pk_id = created["id"]
    code = created["student_id"]

    # Fetch by numeric PK
    res_pk = client.get(f"/students/{pk_id}")
    assert res_pk.status_code == 200
    assert res_pk.json()["name"] == "Target Student"

    # Fetch by custom code
    res_code = client.get(f"/students/{code}")
    assert res_code.status_code == 200
    assert res_code.json()["name"] == "Target Student"

    # Nonexistent
    res_404 = client.get("/students/NONEXISTENT-999")
    assert res_404.status_code == 404


def test_update_student_put_and_patch(client):
    """Test PUT and PATCH update operations."""
    created = client.post("/students", json={
        "name": "Original Name",
        "date_of_birth": "2004-01-01",
        "email": "orig@example.com",
        "course": "Physics"
    }).json()

    sid = created["student_id"]

    # PATCH course and address
    patch_res = client.patch(f"/students/{sid}", json={
        "course": "Applied Physics",
        "address": "New Delhi"
    })
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["course"] == "Applied Physics"
    assert updated["address"] == "New Delhi"
    assert updated["name"] == "Original Name"

    # PUT name
    put_res = client.put(f"/students/{sid}", json={
        "name": "Updated Name"
    })
    assert put_res.status_code == 200
    assert put_res.json()["name"] == "Updated Name"


def test_delete_student(client):
    """Test deleting a student record and verifying removal."""
    created = client.post("/students", json={
        "name": "To Be Deleted",
        "date_of_birth": "2004-01-01",
        "email": "delete.me@example.com"
    }).json()

    sid = created["student_id"]

    # Delete
    del_res = client.delete(f"/students/{sid}")
    assert del_res.status_code == 200
    assert "successfully deleted" in del_res.json()["message"]

    # Check 404 after deletion
    get_res = client.get(f"/students/{sid}")
    assert get_res.status_code == 404


def test_summary_stats(client):
    """Test summary stats endpoint."""
    client.post("/students", json={"name": "S1", "date_of_birth": "2004-01-01", "email": "s1@ex.com", "course": "AI"})
    client.post("/students", json={"name": "S2", "date_of_birth": "2004-01-01", "email": "s2@ex.com", "course": "AI"})
    client.post("/students", json={"name": "S3", "date_of_birth": "2004-01-01", "email": "s3@ex.com", "course": "Robotics"})

    res = client.get("/students/stats/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_students"] == 3
    assert data["courses_breakdown"]["AI"] == 2
    assert data["courses_breakdown"]["Robotics"] == 1
