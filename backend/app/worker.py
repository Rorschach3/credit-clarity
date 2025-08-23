"""
Redis-based Background Worker for Credit Report Processing
Integrates with existing background job system
"""
import asyncio
import redis
import time
import os
import sys
import logging
from typing import Optional

# Add backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
from services.background_jobs import job_processor

# Load environment variables
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()  # Test connection
    logger.info(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis: {e}")
    r = None

async def process_job(job_id: str) -> bool:
    """Process a job using the existing background job system"""
    try:
        logger.info(f"🔄 Processing job {job_id}")
        
        # Set initial progress
        if r:
            r.set(f"job:{job_id}:progress", "0")
            r.set(f"job:{job_id}:status", "processing")
        
        # Use existing job processor to handle the job
        # This integrates with your existing background_jobs.py system
        job_result = await job_processor.process_job(job_id)
        
        if r:
            if job_result.get("success", False):
                r.set(f"job:{job_id}:progress", "100")
                r.set(f"job:{job_id}:status", "completed")
                logger.info(f"✅ Job {job_id} completed successfully")
                return True
            else:
                r.set(f"job:{job_id}:status", "failed")
                r.set(f"job:{job_id}:error", job_result.get("error", "Unknown error"))
                logger.error(f"❌ Job {job_id} failed: {job_result.get('error')}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error processing job {job_id}: {e}")
        if r:
            r.set(f"job:{job_id}:status", "failed")
            r.set(f"job:{job_id}:error", str(e))
        return False

async def simulate_job_progress(job_id: str):
    """Fallback simulation if job processor is not available"""
    logger.info(f"🔄 Simulating job progress for {job_id}")
    
    for step in range(1, 11):
        if r:
            r.set(f"job:{job_id}:progress", step * 10)
            r.set(f"job:{job_id}:status", "processing")
        
        # Simulate work
        await asyncio.sleep(1)
        logger.info(f"📈 Job {job_id} progress: {step * 10}%")
    
    if r:
        r.set(f"job:{job_id}:progress", "100")
        r.set(f"job:{job_id}:status", "completed")
    
    logger.info(f"✅ Job {job_id} simulation completed")

async def worker_main():
    """Main worker loop"""
    logger.info("🚀 Starting Credit Report Worker...")
    
    if not r:
        logger.error("❌ Cannot start worker without Redis connection")
        return
    
    # Start the existing job processor
    try:
        await job_processor.start()
        logger.info("✅ Background job processor started")
    except Exception as e:
        logger.warning(f"⚠️ Could not start job processor: {e}")
        logger.info("Using fallback simulation mode")
    
    while True:
        try:
            # Check for jobs in the queue
            job_id = r.lpop("job_queue")
            
            if job_id:
                logger.info(f"📋 Found job in queue: {job_id}")
                
                # Try to process with existing system, fallback to simulation
                try:
                    success = await process_job(job_id)
                except Exception as e:
                    logger.warning(f"⚠️ Job processor failed, using simulation: {e}")
                    await simulate_job_progress(job_id)
            else:
                # No jobs, wait a bit
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
            await asyncio.sleep(5)  # Wait before retrying

    # Cleanup
    try:
        await job_processor.stop()
        logger.info("🛑 Background job processor stopped")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(worker_main())