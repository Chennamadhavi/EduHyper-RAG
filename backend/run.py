"""
Script to launch the EduHyper-RAG FastAPI Backend Server.
Usage:
    py backend/run.py
"""

import sys
from pathlib import Path
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name} on http://{settings.api_host}:{settings.api_port}...")
    print(f"API Docs available at http://{settings.api_host}:{settings.api_port}/docs")
    print(f"Health check at http://{settings.api_host}:{settings.api_port}{settings.api_prefix}/health")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production(),
    )
