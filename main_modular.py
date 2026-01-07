"""
Root entry point for the modular Credit Clarity API.

This module mirrors the documented architecture guide and exposes a single
`app` object that tests and WSGI/ASGI runners expect.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.main import app  # Re-export the FastAPI instance

if __name__ == "__main__":  # pragma: no cover
    import os
    import uvicorn

    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    reload_mode = os.getenv("ENVIRONMENT", "development").lower() != "production"

    uvicorn.run(app, host=host, port=port, reload=reload_mode)
