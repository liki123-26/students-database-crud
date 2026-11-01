import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.crud import get_all_students_for_ai_context

logger = logging.getLogger(__name__)


def build_grounded_prompt(question: str, records: List[Dict[str, Any]]) -> str:
    """
    Constructs a grounded prompt containing database records for Ollama.
    Enforces strict hallucination limits and prevents SQL injection.
    """
    formatted_records = "\n".join([
        f"- ID: {r['student_id']} | Name: {r['name']} | DOB: {r['date_of_birth']} | Course: {r['course']} | Enrollment Date: {r['enrollment_date']} | Address: {r['address']}"
        for r in records
    ]) if records else "No student records found in database."

    prompt = f"""You are an accurate, helpful AI Assistant for an Educational Institution's Student Database.
Answer the user's question accurately based SOLELY on the student records provided below.
Rules:
1. Only state facts that appear in the provided student database records.
2. If there are no records matching the query, say "No matching students were found in the database."
3. Do not invent or hallucinate any student names, IDs, dates, or courses.
4. Keep your answer concise, polite, and well-formatted.

=== STUDENT DATABASE RECORDS ({len(records)} total records) ===
{formatted_records}
=============================================================

User Question: {question}

Helpful Answer:"""
    return prompt


def generate_fallback_answer(question: str, records: List[Dict[str, Any]]) -> str:
    """
    Intelligent fallback rule-based engine when Ollama is offline.
    Directly computes grounded answers from SQLite records for common queries.
    """
    q = question.lower()
    total = len(records)

    # 1. Total count questions
    if any(phrase in q for phrase in ["how many students", "total students", "count of students", "number of students"]):
        return f"There are currently {total} student record(s) in the database."

    # 2. Born after / before year query
    # E.g., "List students born after 2005"
    born_after_match = re.search(r"born after\s+(\d{4})", q)
    if born_after_match:
        year = int(born_after_match.group(1))
        matches = [
            r for r in records
            if r.get("date_of_birth") and int(r["date_of_birth"].split("-")[0]) > year
        ]
        if not matches:
            return f"No students were found in the database born after {year}."
        names = ", ".join([f"{m['name']} (DOB: {m['date_of_birth']}, Course: {m['course']})" for m in matches])
        return f"Found {len(matches)} student(s) born after {year}: {names}."

    born_before_match = re.search(r"born before\s+(\d{4})", q)
    if born_before_match:
        year = int(born_before_match.group(1))
        matches = [
            r for r in records
            if r.get("date_of_birth") and int(r["date_of_birth"].split("-")[0]) < year
        ]
        if not matches:
            return f"No students were found in the database born before {year}."
        names = ", ".join([f"{m['name']} (DOB: {m['date_of_birth']}, Course: {m['course']})" for m in matches])
        return f"Found {len(matches)} student(s) born before {year}: {names}."

    # 3. Course filter questions
    # E.g., "Which students are in Computer Science?"
    for record in records:
        course = (record.get("course") or "").lower()
        if course and course in q:
            matches = [r for r in records if (r.get("course") or "").lower() == course]
            names = ", ".join([f"{m['name']} ({m['student_id']})" for m in matches])
            return f"There are {len(matches)} student(s) enrolled in {record['course']}: {names}."

    # 4. General list question
    if any(phrase in q for phrase in ["list all", "list students", "show all", "who are the students"]):
        if not records:
            return "The database currently has no student records."
        student_list = "\n".join([f"- {r['student_id']}: {r['name']} ({r['course']})" for r in records[:10]])
        more = f"\n...and {total - 10} more." if total > 10 else ""
        return f"Here are the students in the database ({total} total):\n{student_list}{more}"

    # Default fallback summary
    summary_courses = set(r.get("course") for r in records if r.get("course"))
    courses_str = ", ".join(summary_courses) if summary_courses else "None"
    return (
        f"The database contains {total} student records across courses: {courses_str}. "
        f"You asked: '{question}'. For advanced open-ended reasoning, please start Ollama locally (`ollama run {settings.ollama_model}`)."
    )


async def query_ollama_ai(
    db: Session,
    question: str,
    model_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes a natural-language question against the student database.
    1. Fetches safe records from SQLite (security: no raw SQL from model).
    2. Builds grounded prompt.
    3. Attempts to query Ollama at the configured base URL.
    4. Falls back gracefully with grounded answer if Ollama is unreachable.
    """
    records = get_all_students_for_ai_context(db, limit=100)
    prompt = build_grounded_prompt(question, records)
    model = model_override or settings.ollama_model

    ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

    # Context preview (first 2 records) for verification
    preview_records = records[:2]
    context_preview = json.dumps(preview_records, indent=2)

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2  # Low temperature for factual grounding
                }
            }
            response = await client.post(ollama_url, json=payload)

            if response.status_code == 200:
                data = response.json()
                ai_text = data.get("response", "").strip()
                return {
                    "question": question,
                    "answer": ai_text,
                    "model_used": model,
                    "grounded_records_count": len(records),
                    "ai_available": True,
                    "context_preview": context_preview,
                    "tip": "Response generated by local Ollama model grounded on live SQLite records."
                }
            else:
                logger.warning(f"Ollama returned HTTP {response.status_code}: {response.text}")

    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as ex:
        logger.info(f"Ollama local instance not reachable at {ollama_url}: {ex}. Using grounded fallback engine.")

    # Graceful fallback: Grounded answers calculated directly from SQLite records
    fallback_text = generate_fallback_answer(question, records)
    return {
        "question": question,
        "answer": fallback_text,
        "model_used": "sqlite-grounded-fallback",
        "grounded_records_count": len(records),
        "ai_available": False,
        "context_preview": context_preview,
        "tip": f"Ollama is offline or unreachable at {settings.ollama_base_url}. To enable local LLM answers, start Ollama and run 'ollama run {model}'."
    }
