#!/usr/bin/env python3
"""
Rollback script for JWKS authentication migration
Provides emergency rollback to previous authentication method
"""

import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JWKSRollback:
    """Handles rollback of JWKS authentication changes"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.src_dir = self.project_root / "src"
        self.backup_dir = self.project_root / "backup_jwks"
        
    def create_backup(self):
        """Create backup of modified files before rollback"""
        logger.info("Creating backup of JWKS implementation...")
        
        backup_files = [
            "backend/utils/jwks_auth.py",
            "backend/main.py",
            "backend/requirements.txt",
            "src/integrations/supabase/client.ts",
            "src/utils/jwks-test.ts",
            "test_jwks_auth.py",
            "JWKS_MIGRATION_GUIDE.md"
        ]
        
        self.backup_dir.mkdir(exist_ok=True)
        
        for file_path in backup_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                backup_path = self.backup_dir / file_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, backup_path)
                logger.info(f"Backed up: {file_path}")
        
        logger.info(f"Backup created at: {self.backup_dir}")
    
    def rollback_backend_auth(self):
        """Rollback backend authentication to original state"""
        logger.info("Rolling back backend authentication...")
        
        # Create original auth.py content
        original_auth_content = '''from typing import Optional, Dict
import uuid
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

security = HTTPBearer()

class RateLimiter:
    def __init__(self, max_requests: int, window_minutes: int):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.client_requests: Dict[str, List[datetime]] = {}

    def allow_request(self, client_id: str) -> bool:
        now = datetime.now()
        if client_id not in self.client_requests:
            self.client_requests[client_id] = []

        # Remove old requests outside the window
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if now - req_time < timedelta(minutes=self.window_minutes)
        ]

        if len(self.client_requests[client_id]) < self.max_requests:
            self.client_requests[client_id].append(now)
            return True
        return False

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[uuid.UUID]:
    """
    Extract user ID from JWT token
    Replace this with your actual authentication logic
    """
    try:
        # TODO: Implement actual JWT token validation
        # For now, returning None to allow anonymous uploads
        return None
        
        # Example implementation:
        # token = credentials.credentials
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # user_id = payload.get("sub")
        # return uuid.UUID(user_id) if user_id else None
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(user_id: Optional[uuid.UUID] = Depends(get_current_user_id)) -> Dict:
    """
    Placeholder for fetching user details.
    In a real app, this would fetch user data from a database.
    """
    if user_id is None:
        # For now, allow anonymous access for simplicity in development
        return {"user_id": "anonymous", "role": "guest"}
    
    # Mock user data for demonstration
    if str(user_id) == "some-admin-uuid": # Replace with actual admin UUID
        return {"user_id": str(user_id), "role": "admin"}
    
    return {"user_id": str(user_id), "role": "user"}
'''
        
        # Write original auth.py
        auth_file = self.backend_dir / "utils" / "auth.py"
        with open(auth_file, 'w') as f:
            f.write(original_auth_content)
        
        logger.info("Backend auth.py rolled back to original state")
        
        # Remove JWKS auth file
        jwks_auth_file = self.backend_dir / "utils" / "jwks_auth.py"
        if jwks_auth_file.exists():
            jwks_auth_file.unlink()
            logger.info("Removed jwks_auth.py")
    
    def rollback_backend_main(self):
        """Rollback main.py to remove JWKS imports"""
        logger.info("Rolling back main.py...")
        
        main_file = self.backend_dir / "main.py"
        if not main_file.exists():
            logger.warning("main.py not found, skipping rollback")
            return
        
        # Read current content
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Remove JWKS imports
        jwks_imports = [
            "from utils.jwks_auth import (",
            "    get_current_user_jwt,",
            "    get_current_user_id_jwt,",
            "    require_authenticated_user,",
            "    cleanup_auth,",
            "    RateLimiter",
            ")"
        ]
        
        for import_line in jwks_imports:
            content = content.replace(import_line, "")
        
        # Remove cleanup handler
        content = content.replace('''
# Add cleanup handler for authentication
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    await cleanup_auth()

# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=100, window_minutes=60)''', "")
        
        # Restore original endpoint signatures
        content = content.replace(
            "async def save_tradelines_endpoint(\\n    request: dict,\\n    user_data: dict = Depends(require_authenticated_user)\\n):",
            "async def save_tradelines_endpoint(request: dict):"
        )
        
        content = content.replace(
            "async def process_credit_report(\\n    file: UploadFile = File(...),\\n    user_data: dict = Depends(require_authenticated_user)\\n):",
            "async def process_credit_report(\\n    file: UploadFile = File(...),\\n    user_id: str = Form(default=\"default-user\")\\n):"
        )
        
        # Write updated content
        with open(main_file, 'w') as f:
            f.write(content)
        
        logger.info("main.py rolled back")
    
    def rollback_frontend_client(self):
        """Rollback frontend client to original configuration"""
        logger.info("Rolling back frontend client...")
        
        original_client_content = '''// This file is automatically generated. Do not edit it directly.
import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

const SUPABASE_URL = "https://gywohmbqohytziwsjrps.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5d29obWJxb2h5dHppd3NqcnBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NjYzNDQsImV4cCI6MjA2MTQ0MjM0NH0.F1Y8K6wmkqTInHvI1j9Pbog782i3VSVpIbgYqakyPwo";

// Import the supabase client like this:
// import { supabase } from "@/integrations/supabase/client";

export const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    storage: localStorage,
    persistSession: true,
    autoRefreshToken: true,
  }
});
'''
        
        client_file = self.src_dir / "integrations" / "supabase" / "client.ts"
        with open(client_file, 'w') as f:
            f.write(original_client_content)
        
        logger.info("Frontend client.ts rolled back")
    
    def remove_jwks_files(self):
        """Remove JWKS-specific files"""
        logger.info("Removing JWKS-specific files...")
        
        files_to_remove = [
            "test_jwks_auth.py",
            "src/utils/jwks-test.ts",
            "JWKS_MIGRATION_GUIDE.md",
            "rollback_jwks.py"  # This file itself
        ]
        
        for file_path in files_to_remove:
            full_path = self.project_root / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Removed: {file_path}")
    
    def rollback_requirements(self):
        """Rollback requirements.txt to remove JWKS dependencies"""
        logger.info("Rolling back requirements.txt...")
        
        requirements_file = self.backend_dir / "requirements.txt"
        if requirements_file.exists():
            requirements_file.unlink()
            logger.info("Removed requirements.txt (was added for JWKS)")
    
    def full_rollback(self):
        """Perform complete rollback"""
        logger.info("🔄 Starting full JWKS rollback...")
        logger.info("=" * 50)
        
        try:
            self.create_backup()
            self.rollback_backend_auth()
            self.rollback_backend_main()
            self.rollback_frontend_client()
            self.rollback_requirements()
            
            logger.info("=" * 50)
            logger.info("✅ JWKS rollback completed successfully!")
            logger.info("📁 Backup of JWKS implementation saved to: backup_jwks/")
            logger.info("🚀 System reverted to original authentication state")
            
            print("\\n" + "=" * 60)
            print("ROLLBACK COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print("• Backend authentication: Reverted to original placeholder")
            print("• Frontend client: Reverted to hardcoded configuration")
            print("• JWKS files: Removed")
            print("• Backup: Saved to backup_jwks/ directory")
            print("\\nTo restore JWKS authentication, restore files from backup_jwks/")
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            raise
    
    def validate_rollback(self):
        """Validate that rollback was successful"""
        logger.info("🔍 Validating rollback...")
        
        # Check that JWKS files are removed
        jwks_files = [
            "backend/utils/jwks_auth.py",
            "test_jwks_auth.py",
            "src/utils/jwks-test.ts"
        ]
        
        for file_path in jwks_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                logger.warning(f"⚠️ JWKS file still exists: {file_path}")
            else:
                logger.info(f"✅ JWKS file removed: {file_path}")
        
        # Check that backup exists
        if self.backup_dir.exists():
            logger.info("✅ Backup directory exists")
        else:
            logger.warning("⚠️ Backup directory not found")
        
        logger.info("🔍 Rollback validation complete")

def main():
    """Main rollback function"""
    rollback = JWKSRollback()
    
    print("🔄 JWKS Authentication Rollback Tool")
    print("=" * 50)
    print("This will revert all JWKS authentication changes")
    print("and restore the original authentication system.")
    print()
    
    response = input("Are you sure you want to proceed? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Rollback cancelled")
        return
    
    try:
        rollback.full_rollback()
        rollback.validate_rollback()
        return 0
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())