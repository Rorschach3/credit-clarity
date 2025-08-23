#!/usr/bin/env python3
"""
Background Worker Process
Runs the job processor for handling background tasks
"""
import asyncio
import logging
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from services.background_jobs import job_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Main worker process"""
    logger.info("🚀 Starting background worker...")
    
    try:
        # Start the job processor
        await job_processor.start()
        logger.info("✅ Background worker started successfully")
        
        # Keep the worker running
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        logger.info("📋 Received shutdown signal...")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
    finally:
        # Cleanup
        try:
            await job_processor.stop()
            logger.info("🛑 Background worker stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping worker: {e}")

if __name__ == "__main__":
    asyncio.run(main())