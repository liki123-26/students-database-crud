import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html

from app.config import settings
from app.database import engine, Base
from app.routers import students, ai

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")
SWAGGER_THEME_CSS = os.path.join(STATIC_DIR, "swagger_theme.css")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager: Runs before the application starts up
    and after it shuts down. Automatically creates tables in SQLite.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
# 🎓 Students Database CRUD Application
**Python Backend Development Project**

A robust REST API built with **FastAPI** and **SQLite** for managing student records with complete Create, Read, Update, and Delete (CRUD) operations, comprehensive input validation, and an **Optional Local AI Extension powered by Ollama**.

---
### 🚀 Key Features:
- **Full CRUD Support**: Create, Read (List & Filter), Update (PUT & PATCH), and Delete student records.
- **SQLite Persistence**: Safe and transactional data persistence using SQLAlchemy ORM.
- **Input Validation**: Strict schema enforcement using Pydantic v2 (email validation, realistic birth dates, required names).
- **Advanced Querying**: Search by name, course filter, birth date range, and pagination with sorting.
- **Optional Local AI (Ollama)**: Natural-language query interface with grounding context and offline fallback.
    """,
    lifespan=lifespan,
    docs_url=None,   # Custom dark glassmorphic Swagger UI implemented below
    redoc_url=None   # Custom dark ReDoc implemented below
)

# Enable CORS for frontend applications or local testing tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register route modules
app.include_router(students.router)
app.include_router(ai.router)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with innovative dark glassmorphic background and glowing accents."""
    base_response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )
    # Inject our custom dark glassmorphic stylesheet
    html_str = base_response.body.decode("utf-8").replace(
        "</head>",
        "<link rel='stylesheet' href='/static/swagger_theme.css'></head>"
    )
    return HTMLResponse(html_str)


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc page with innovative dark theme and modern typography."""
    html_content = f"""<!DOCTYPE html>
<html>
  <head>
    <title>{app.title} - ReDoc API Reference</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: #080d1a;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', sans-serif;
      }}
      /* Ambient top glow */
      body::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 350px;
        background: radial-gradient(circle at 50% -20%, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
      }}
      #redoc-container {{ position: relative; z-index: 1; }}
    </style>
  </head>
  <body>
    <div id="redoc-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js"></script>
    <script>
      Redoc.init('{app.openapi_url}', {{
        theme: {{
          colors: {{
            primary: {{ main: '#818cf8' }},
            success: {{ main: '#10b981' }},
            warning: {{ main: '#f59e0b' }},
            error: {{ main: '#ef4444' }},
            text: {{
              primary: '#f1f5f9',
              secondary: '#94a3b8'
            }},
            http: {{
              get: '#38bdf8',
              post: '#34d399',
              put: '#fbbf24',
              patch: '#a78bfa',
              delete: '#f87171'
            }}
          }},
          typography: {{
            fontSize: '14px',
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            code: {{ fontFamily: "'JetBrains Mono', monospace" }},
            headings: {{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontWeight: '700',
              lineHeight: '1.4em'
            }}
          }},
          sidebar: {{
            backgroundColor: '#050811',
            textColor: '#cbd5e1',
            activeTextColor: '#ffffff'
          }},
          rightPanel: {{
            backgroundColor: '#03050c',
            textColor: '#e2e8f0',
            width: '42%'
          }}
        }}
      }}, document.getElementById('redoc-container'));
    </script>
  </body>
</html>"""
    return HTMLResponse(html_content)


@app.get(
    "/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False
)
def get_dashboard():
    """Serves the interactive web dashboard with particle constellation background."""
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)


@app.get(
    "/",
    tags=["Root"],
    summary="API Health and Navigation Overview"
)
def root_overview(request: Request):
    """Root endpoint: serves interactive web dashboard for browsers, and JSON overview for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        if os.path.exists(INDEX_HTML):
            return FileResponse(INDEX_HTML)

    return {
        "project": "Students Database CRUD Application",
        "status": "online",
        "version": settings.app_version,
        "dashboard": "/dashboard",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "create_student": "POST /students",
            "list_students": "GET /students",
            "view_student": "GET /students/{student_id}",
            "update_student_put": "PUT /students/{student_id}",
            "update_student_patch": "PATCH /students/{student_id}",
            "delete_student": "DELETE /students/{student_id}",
            "summary_stats": "GET /students/stats/summary",
            "ai_query": "POST /ai/ask",
            "ai_status": "GET /ai/status"
        }
    }
