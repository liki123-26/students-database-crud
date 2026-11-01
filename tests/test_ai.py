from unittest.mock import patch, AsyncMock
import httpx
import pytest


def test_ai_status(client):
    """Test AI status endpoint."""
    res = client.get("/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "ollama_available" in data
    assert "configured_model" in data


def test_ai_ask_fallback_count(client):
    """Test AI query offline fallback for student count."""
    client.post("/students", json={
        "name": "Student A",
        "date_of_birth": "2004-01-01",
        "email": "sa@example.com",
        "course": "Computer Science"
    })
    client.post("/students", json={
        "name": "Student B",
        "date_of_birth": "2006-05-15",
        "email": "sb@example.com",
        "course": "Data Analytics"
    })

    # When Ollama is offline, fallback engine provides accurate grounded count
    res = client.post("/ai/ask", json={"question": "How many students are there?"})
    assert res.status_code == 200
    data = res.json()
    assert "2 student record(s)" in data["answer"]
    assert data["grounded_records_count"] == 2


def test_ai_ask_fallback_born_after(client):
    """Test AI query offline fallback for born after 2005."""
    client.post("/students", json={
        "name": "Old Student",
        "date_of_birth": "2003-01-01",
        "email": "old@example.com"
    })
    client.post("/students", json={
        "name": "Young Student",
        "date_of_birth": "2007-06-20",
        "email": "young@example.com"
    })

    res = client.post("/ai/ask", json={"question": "List students born after 2005"})
    assert res.status_code == 200
    data = res.json()
    assert "Young Student" in data["answer"]
    assert "Old Student" not in data["answer"]


def test_ai_ask_with_mocked_ollama(client):
    """Test AI query when Ollama returns a valid response."""
    client.post("/students", json={
        "name": "Test Student",
        "date_of_birth": "2004-01-01",
        "email": "test@example.com",
        "course": "AI/ML"
    })

    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "llama3.2:1b",
        "response": "Based on the records, there is 1 student enrolled in AI/ML."
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        res = client.post("/ai/ask", json={"question": "Who is in AI/ML?"})
        assert res.status_code == 200
        data = res.json()
        assert data["ai_available"] is True
        assert "1 student enrolled in AI/ML" in data["answer"]
        assert data["model_used"] == "llama3.2:1b"
