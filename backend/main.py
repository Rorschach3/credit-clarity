"""
Credit Clarity Backend Application
Main entry point using application factory pattern
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env file specifically
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

# Add current directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import app factory
from core.app_factory import create_development_app, create_production_app

# Create application based on environment - force development mode
environment = os.getenv("ENVIRONMENT", "development").lower()
print(f"🔧 Environment: {environment}")
print(f"🔧 Debug: {os.getenv('DEBUG', 'false')}")

if environment == "production":
    app = create_production_app()
elif environment == "staging":
    from core.app_factory import create_app, setup_logging, validate_environment
    setup_logging()
    validate_environment()
    app = create_app(
        title="Credit Clarity API (Staging)",
        debug=False,
        environment="staging"
    )
else:
    print("🔧 Creating development app...")
    app = create_development_app()
    print("✅ Development app created")

# For direct execution
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment - force port 8000
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))  # Force port 8000
    workers = int(os.getenv("WORKERS", "1"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting server on {host}:{port} (debug={debug}, workers={workers})")
    
    if workers > 1:
        # Multi-worker production mode
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=workers,
            reload=False
        )
    else:
        # Single worker development mode - use app directly without reload for this case
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,  # Disable reload to avoid import string issues
            log_level="debug" if debug else "info",
            access_log=True
        )