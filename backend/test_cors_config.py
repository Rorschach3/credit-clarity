#!/usr/bin/env python3
"""
Quick test to verify CORS configuration is valid
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cors_config():
    """Test that the CORS configuration is properly set"""
    try:
        # Import main module
        print("Importing main module...")
        import main

        # Check if app exists
        assert hasattr(main, 'app'), "FastAPI app not found"
        print("✓ FastAPI app found")

        # Get middleware
        middlewares = main.app.user_middleware
        print(f"✓ Found {len(middlewares)} middleware(s)")

        # Find CORS middleware
        cors_middleware = None
        for middleware in middlewares:
            if 'CORSMiddleware' in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None, "CORS middleware not found"
        print("✓ CORS middleware found")

        # Check configuration
        options = cors_middleware.options

        # Verify allow_headers is not wildcard
        allow_headers = options.get('allow_headers', [])
        assert allow_headers != ["*"], "allow_headers should not be wildcard"
        assert isinstance(allow_headers, list), "allow_headers should be a list"
        assert len(allow_headers) > 0, "allow_headers should not be empty"
        print(f"✓ allow_headers: {allow_headers}")

        # Verify expose_headers is not wildcard
        expose_headers = options.get('expose_headers', [])
        assert expose_headers != ["*"], "expose_headers should not be wildcard"
        assert isinstance(expose_headers, list), "expose_headers should be a list"
        assert len(expose_headers) > 0, "expose_headers should not be empty"
        print(f"✓ expose_headers: {expose_headers}")

        # Verify allow_credentials
        allow_credentials = options.get('allow_credentials', False)
        assert allow_credentials == True, "allow_credentials should be True"
        print(f"✓ allow_credentials: {allow_credentials}")

        # Verify origins
        allow_origins = options.get('allow_origins', [])
        assert isinstance(allow_origins, list), "allow_origins should be a list"
        assert len(allow_origins) > 0, "allow_origins should not be empty"
        print(f"✓ allow_origins: {len(allow_origins)} origins configured")

        print("\n✅ All CORS configuration tests passed!")
        print("\nCORS Configuration Summary:")
        print(f"  - Origins: {len(allow_origins)} configured")
        print(f"  - Allow Headers: {len(allow_headers)} headers")
        print(f"  - Expose Headers: {len(expose_headers)} headers")
        print(f"  - Allow Credentials: {allow_credentials}")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cors_config()
    sys.exit(0 if success else 1)
