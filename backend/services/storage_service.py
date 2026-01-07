"""
Enhanced Storage Service for Credit Clarity
Handles file storage with duplicate detection and hash-based deduplication
"""
import hashlib
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from datetime import datetime, timedelta

from ..models.tradeline_models import ProcessingStatus

logger = logging.getLogger(__name__)


class StorageService:
    """Enhanced service for handling file and data storage operations."""
    
    def __init__(self, storage_path: str = "storage"):
        """
        Initialize storage service.
        
        Args:
            storage_path: Base storage directory path
        """
        self.storage_path = Path(storage_path)
        self.base_path = self.storage_path
        self.ensure_storage_directories()
        
        # File hash tracking
        self.hash_storage_path = self.storage_path / "hashes"
        self.hash_storage_path.mkdir(parents=True, exist_ok=True)
        self.hash_index_file = self.hash_storage_path / "hash_index.json"
        
        # Load existing hash index
        self._hash_index: Dict[str, Dict[str, Any]] = self._load_hash_index()
    
    def ensure_storage_directories(self):
        """Create necessary storage directories."""
        directories = [
            self.storage_path / "uploads",
            self.storage_path / "ai_results",
            self.storage_path / "llm_input",
            self.storage_path / "processed",
            self.storage_path / "jobs",
            self.storage_path / "avatars",
            self.storage_path / "hashes"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_hash_index(self) -> Dict[str, Dict[str, Any]]:
        """Load hash index from disk."""
        if self.hash_index_file.exists():
            try:
                with open(self.hash_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load hash index: {e}")
        return {}
    
    def _save_hash_index(self):
        """Save hash index to disk."""
        try:
            with open(self.hash_index_file, 'w') as f:
                json.dump(self._hash_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save hash index: {e}")
    
    async def calculate_file_hash(self, file_content: bytes) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file_content: File content as bytes
            
        Returns:
            SHA-256 hash as hex string
        """
        hasher = hashlib.sha256()
        hasher.update(file_content)
        return hasher.hexdigest()
    
    async def check_duplicate_hash(
        self,
        file_hash: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a file with this hash already exists.
        
        Args:
            file_hash: SHA-256 hash to check
            user_id: Optional user ID to check against
            
        Returns:
            Tuple of (is_duplicate, existing_file_info)
        """
        if file_hash in self._hash_index:
            entry = self._hash_index[file_hash]
            
            # If user_id specified, check if user owns the file
            if user_id and entry.get("user_id") != user_id:
                # Same file content but different user - still a duplicate
                return True, entry
            
            return True, entry
        
        return False, None
    
    def _register_file_hash(
        self,
        file_hash: str,
        file_path: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a file hash in the index.
        
        Args:
            file_hash: SHA-256 hash
            file_path: Path to stored file
            user_id: User who owns the file
            metadata: Additional file metadata
        """
        self._hash_index[file_hash] = {
            "file_path": file_path,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "file_size": metadata.get("file_size", 0) if metadata else 0,
            "original_filename": metadata.get("filename") if metadata else None,
            "content_type": metadata.get("content_type") if metadata else None
        }
        self._save_hash_index()
    
    async def store_with_deduplication(
        self,
        file_content: bytes,
        relative_path: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        allow_duplicate: bool = False
    ) -> Dict[str, Any]:
        """
        Store file with automatic deduplication.
        
        Args:
            file_content: File content as bytes
            relative_path: Relative path within storage (e.g., "uploads/file.pdf")
            user_id: User ID owning the file
            metadata: Additional file metadata
            allow_duplicate: If True, store even if duplicate exists
            
        Returns:
            Dictionary with storage result and deduplication info
        """
        # Calculate file hash
        file_hash = await self.calculate_file_hash(file_content)
        
        # Check for duplicates
        is_duplicate, existing_info = await self.check_duplicate_hash(file_hash, user_id)
        
        if is_duplicate and not allow_duplicate:
            logger.info(
                f"Duplicate file detected (hash={file_hash[:16]}...), "
                f"using existing file: {existing_info.get('file_path')}"
            )
            
            return {
                "stored": False,
                "file_path": existing_info.get("file_path"),
                "file_hash": file_hash,
                "is_duplicate": True,
                "duplicate_of": existing_info.get("file_path"),
                "message": "File already exists, using existing copy",
                "metadata": metadata
            }
        
        # Store the file
        file_path = self.storage_path / relative_path
        directory = file_path.parent
        
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Register hash (even for duplicates if allow_duplicate=True)
        file_metadata = {
            **(metadata or {}),
            "file_size": len(file_content)
        }
        
        self._register_file_hash(
            file_hash=str(file_path),
            file_path=str(file_path),
            user_id=user_id,
            metadata=file_metadata
        )
        
        logger.info(
            f"Stored file: {file_path} (hash={file_hash[:16]}..., "
            f"size={len(file_content)} bytes)"
        )
        
        return {
            "stored": True,
            "file_path": str(file_path),
            "file_hash": file_hash,
            "is_duplicate": False,
            "duplicate_of": None,
            "message": "File stored successfully",
            "metadata": file_metadata
        }
    
    async def store_uploaded_file(self, job_id: str, file_content: bytes, metadata: Dict[str, Any]) -> str:
        """Store uploaded file with metadata (enhanced with deduplication)."""
        try:
            file_path = self.storage_path / "uploads" / f"{job_id}.bin"
            metadata_path = self.storage_path / "uploads" / f"{job_id}.json"

            # Write file content
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Calculate hash
            file_hash = hashlib.sha256(file_content).hexdigest()

            storage_metadata = {
                "job_id": job_id,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "stored_at": datetime.now().isoformat(),
                **metadata
            }

            with open(metadata_path, 'w') as f:
                json.dump(storage_metadata, f, indent=2)

            logger.info(f"Stored file for job {job_id}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to store file for job {job_id}: {str(e)}")
            raise

    async def get_file(self, job_id: str) -> Dict[str, Any]:
        """Retrieve uploaded file and metadata."""
        try:
            file_path = self.storage_path / "uploads" / f"{job_id}.bin"
            metadata_path = self.storage_path / "uploads" / f"{job_id}.json"

            with open(file_path, 'rb') as f:
                content = f.read()

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return {
                "content": content,
                "metadata": metadata
            }

        except FileNotFoundError:
            logger.error(f"File not found for job {job_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve file for job {job_id}: {str(e)}")
            raise

    async def store_document_ai_results(self, job_id: str, ai_results: Dict[str, Any]) -> None:
        """Store Document AI processing results."""
        try:
            results_path = self.storage_path / "ai_results" / f"{job_id}.json"
            with open(results_path, 'w') as f:
                json.dump(ai_results, f, indent=2)
            logger.info(f"Stored AI results for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to store AI results for job {job_id}: {str(e)}")
            raise

    async def get_document_ai_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Document AI processing results."""
        try:
            results_path = self.storage_path / "ai_results" / f"{job_id}.json"
            if not results_path.exists():
                return None
            with open(results_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to retrieve AI results for job {job_id}: {str(e)}")
            return None

    async def store_job_data(self, job_id: str, job_data: Dict[Any, Any]) -> None:
        """Store job processing data."""
        try:
            job_path = self.storage_path / "jobs" / f"{job_id}.json"
            serializable_data = self._make_serializable(job_data)
            async with aiofiles.open(job_path, 'w') as f:
                await f.write(json.dumps(serializable_data, indent=2))
            logger.info(f"Stored job data for {job_id}")
        except Exception as e:
            logger.error(f"Failed to store job data for {job_id}: {e}")
            raise

    async def get_job_data(self, job_id: str) -> Optional[Dict[Any, Any]]:
        """Retrieve job processing data."""
        try:
            job_path = self.storage_path / "jobs" / f"{job_id}.json"
            if not job_path.exists():
                return None
            async with aiofiles.open(job_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to retrieve job data for {job_id}: {e}")
            return None

    async def update_job_status(self, job_id: str, status: ProcessingStatus, error_message: Optional[str] = None) -> None:
        """Update job status."""
        try:
            job_data = await self.get_job_data(job_id)
            if not job_data:
                logger.warning(f"Job {job_id} not found for status update")
                return

            job_data["status"] = status.value
            if error_message:
                job_data["error_message"] = error_message
            if status == ProcessingStatus.COMPLETED:
                job_data["completed_at"] = datetime.now().isoformat()

            await self.store_job_data(job_id, job_data)

        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            raise

    async def store_llm_input(self, job_id: str, llm_input: Dict[str, Any]) -> None:
        """Store prepared input data for LLM processing."""
        try:
            input_path = self.storage_path / "llm_input" / f"{job_id}.json"
            llm_input["prepared_at"] = datetime.now().isoformat()
            with open(input_path, 'w') as f:
                json.dump(llm_input, f, indent=2)
            logger.info(f"Stored LLM input for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to store LLM input for job {job_id}: {str(e)}")
            raise

    async def cleanup_old_files(self, retention_days: int = 7) -> None:
        """Clean up old files and job data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # Cleanup uploads
            upload_dir = self.storage_path / "uploads"
            for file_path in upload_dir.iterdir():
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")

            # Cleanup job data
            jobs_dir = self.storage_path / "jobs"
            for file_path in jobs_dir.iterdir():
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Cleaned up old job data: {file_path}")

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")

    async def store_avatar(
        self,
        user_id: str,
        file_content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store user avatar with deduplication.
        
        Args:
            user_id: User ID
            file_content: Avatar image content
            metadata: Additional metadata
            
        Returns:
            Storage result dictionary
        """
        # Check for duplicate
        file_hash = await self.calculate_file_hash(file_content)
        is_duplicate, existing_info = await self.check_duplicate_hash(file_hash, user_id)
        
        if is_duplicate and existing_info:
            return {
                "success": True,
                "avatar_url": f"/avatars/{user_id}",
                "file_hash": file_hash,
                "is_duplicate": True,
                "message": "Using existing avatar"
            }
        
        # Store avatar
        avatar_path = self.storage_path / "avatars" / f"{user_id}.jpg"
        
        with open(avatar_path, 'wb') as f:
            f.write(file_content)
        
        # Register hash
        self._register_file_hash(
            file_hash=file_hash,
            file_path=str(avatar_path),
            user_id=user_id,
            metadata=metadata
        )
        
        return {
            "success": True,
            "avatar_url": f"/avatars/{user_id}",
            "file_path": str(avatar_path),
            "file_hash": file_hash,
            "is_duplicate": False,
            "message": "Avatar uploaded successfully"
        }
    
    def get_file_hash_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stored file by its hash.
        
        Args:
            file_hash: SHA-256 hash
            
        Returns:
            File info dictionary or None
        """
        return self._hash_index.get(file_hash)
    
    def get_user_files(self, user_id: str) -> list:
        """
        Get all files stored by a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of file info dictionaries
        """
        user_files = []
        for file_hash, info in self._hash_index.items():
            if info.get("user_id") == user_id:
                user_files.append({
                    "file_hash": file_hash,
                    **info
                })
        return user_files
    
    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            return obj


# Import aiofiles for async file operations
import aiofiles


# Global storage service instance
storage_service = StorageService()
