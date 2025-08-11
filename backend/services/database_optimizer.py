"""
Database optimization service for Credit Clarity
Provides query optimization, connection pooling, and batch operations
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import time

from supabase import create_client, Client
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseOptimizer:
    """
    Optimized database operations with:
    - Connection pooling
    - Batch operations
    - Query optimization
    - Connection retry logic
    """
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connection_pool = asyncio.Queue(maxsize=max_connections)
        self._active_connections = 0
        self._query_stats = {
            'total_queries': 0,
            'batch_queries': 0,
            'failed_queries': 0,
            'average_query_time': 0.0,
            'cache_hits': 0
        }
        
        # Query result cache
        self._query_cache = {}
        self._cache_expiry = {}
        self.cache_ttl = 300  # 5 minutes default TTL
        
        # Initialize connections
        asyncio.create_task(self._initialize_pool())
    
    async def _initialize_pool(self):
        """Initialize connection pool."""
        if not settings.supabase_url or not settings.supabase_anon_key:
            logger.warning("Supabase credentials not available")
            return
        
        try:
            for _ in range(self.max_connections):
                client = create_client(settings.supabase_url, settings.supabase_anon_key)
                await self._connection_pool.put(client)
                self._active_connections += 1
            
            logger.info(f"✅ Database connection pool initialized with {self.max_connections} connections")
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        try:
            # Wait for available connection with timeout
            client = await asyncio.wait_for(self._connection_pool.get(), timeout=30.0)
            yield client
        except asyncio.TimeoutError:
            logger.error("Database connection pool timeout")
            raise Exception("Database connection timeout")
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            raise
        finally:
            # Return connection to pool
            try:
                await self._connection_pool.put(client)
            except Exception:
                pass  # Pool might be full
    
    def _generate_cache_key(self, table: str, query_params: Dict) -> str:
        """Generate cache key for query."""
        import hashlib
        key_string = f"{table}_{str(sorted(query_params.items()))}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid."""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _cache_result(self, cache_key: str, result: Any, ttl: Optional[int] = None):
        """Cache query result."""
        ttl = ttl or self.cache_ttl
        self._query_cache[cache_key] = result
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=ttl)
    
    async def optimized_select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Optimized SELECT query with caching and connection pooling.
        """
        start_time = time.time()
        self._query_stats['total_queries'] += 1
        
        # Generate cache key
        cache_key = None
        if use_cache:
            query_params = {
                'table': table,
                'columns': columns,
                'filters': filters or {},
                'order_by': order_by,
                'limit': limit
            }
            cache_key = self._generate_cache_key(table, query_params)
            
            # Check cache
            if self._is_cache_valid(cache_key):
                self._query_stats['cache_hits'] += 1
                logger.debug(f"Cache hit for {table} query")
                return self._query_cache[cache_key]
        
        try:
            async with self.get_connection() as client:
                # Build query
                query = client.table(table).select(columns)
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, list):
                            query = query.in_(key, value)
                        else:
                            query = query.eq(key, value)
                
                # Apply ordering
                if order_by:
                    query = query.order(order_by)
                
                # Apply limit
                if limit:
                    query = query.limit(limit)
                
                # Execute query
                response = query.execute()
                result = response.data
                
                # Cache result
                if use_cache and cache_key:
                    self._cache_result(cache_key, result)
                
                # Update stats
                query_time = time.time() - start_time
                self._update_avg_query_time(query_time)
                
                logger.debug(f"Query completed in {query_time:.3f}s, returned {len(result)} rows")
                return result
                
        except Exception as e:
            self._query_stats['failed_queries'] += 1
            logger.error(f"Database query failed: {e}")
            raise
    
    async def batch_insert_tradelines(
        self,
        tradelines: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Optimized batch insert for tradelines with deduplication.
        """
        if not tradelines:
            return {'inserted': 0, 'errors': 0}
        
        start_time = time.time()
        self._query_stats['batch_queries'] += 1
        
        total_inserted = 0
        total_errors = 0
        
        try:
            async with self.get_connection() as client:
                # Process in batches
                for i in range(0, len(tradelines), batch_size):
                    batch = tradelines[i:i + batch_size]
                    
                    try:
                        # Use upsert to handle duplicates
                        response = client.table("tradelines").upsert(
                            batch,
                            on_conflict="user_id,creditor_name,account_number"
                        ).execute()
                        
                        batch_inserted = len(response.data) if response.data else 0
                        total_inserted += batch_inserted
                        
                        logger.debug(f"Batch {i//batch_size + 1}: inserted {batch_inserted} tradelines")
                        
                    except Exception as e:
                        total_errors += len(batch)
                        logger.error(f"Batch insert failed: {e}")
                        
                        # Check if it's a foreign key constraint error (invalid user_id)
                        if "foreign key constraint" in str(e).lower() or "user_id" in str(e).lower():
                            logger.error(f"Foreign key constraint violation - user_id may not exist in auth table")
                        
                        # Try individual inserts for failed batch
                        for tradeline in batch:
                            try:
                                client.table("tradelines").upsert([tradeline]).execute()
                                total_inserted += 1
                                total_errors -= 1
                            except Exception as individual_error:
                                logger.debug(f"Individual insert failed for tradeline {tradeline.get('creditor_name', 'unknown')}: {individual_error}")
                                pass  # Individual insert failed
                    
                    # Small delay between batches to avoid overwhelming the DB
                    if i + batch_size < len(tradelines):
                        await asyncio.sleep(0.1)
                
                query_time = time.time() - start_time
                logger.info(f"Batch insert completed: {total_inserted} inserted, {total_errors} errors in {query_time:.3f}s")
                
                return {
                    'inserted': total_inserted,
                    'errors': total_errors,
                    'processing_time': query_time
                }
                
        except Exception as e:
            logger.error(f"Batch insert operation failed: {e}")
            return {'inserted': 0, 'errors': len(tradelines)}
    
    async def get_user_tradelines_optimized(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimized tradelines retrieval with pagination and filtering.
        """
        base_filters = {'user_id': user_id}
        if filters:
            base_filters.update(filters)
        
        try:
            # Get total count (cached separately)
            count_cache_key = f"tradelines_count_{user_id}_{hash(str(filters))}"
            
            if not self._is_cache_valid(count_cache_key):
                async with self.get_connection() as client:
                    count_query = client.table("tradelines").select("*", count="exact")
                    for key, value in base_filters.items():
                        count_query = count_query.eq(key, value)
                    
                    count_response = count_query.execute()
                    total_count = count_response.count or 0
                    self._cache_result(count_cache_key, total_count, ttl=60)  # Cache for 1 minute
            else:
                total_count = self._query_cache[count_cache_key]
            
            # Get paginated data
            tradelines = await self.optimized_select(
                table="tradelines",
                columns="*",
                filters=base_filters,
                order_by="created_at",
                limit=limit,
                use_cache=True
            )
            
            # Apply offset manually (Supabase doesn't support offset well)
            if offset > 0:
                tradelines = tradelines[offset:offset + limit]
            
            return {
                'tradelines': tradelines,
                'total_count': total_count,
                'has_more': offset + len(tradelines) < total_count,
                'page_info': {
                    'limit': limit,
                    'offset': offset,
                    'returned': len(tradelines)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user tradelines: {e}")
            return {'tradelines': [], 'total_count': 0, 'has_more': False}
    
    async def bulk_update_tradelines(
        self,
        updates: List[Dict[str, Any]],
        batch_size: int = 25
    ) -> Dict[str, Any]:
        """
        Bulk update tradelines with optimized batching.
        """
        if not updates:
            return {'updated': 0, 'errors': 0}
        
        total_updated = 0
        total_errors = 0
        
        try:
            async with self.get_connection() as client:
                for i in range(0, len(updates), batch_size):
                    batch = updates[i:i + batch_size]
                    
                    # Process each update in the batch
                    for update_data in batch:
                        try:
                            tradeline_id = update_data.pop('id')
                            response = client.table("tradelines").update(
                                update_data
                            ).eq('id', tradeline_id).execute()
                            
                            if response.data:
                                total_updated += 1
                            else:
                                total_errors += 1
                                
                        except Exception as e:
                            total_errors += 1
                            logger.debug(f"Update failed for tradeline: {e}")
                    
                    # Small delay between batches
                    await asyncio.sleep(0.05)
                
                return {'updated': total_updated, 'errors': total_errors}
                
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            return {'updated': 0, 'errors': len(updates)}
    
    async def delete_user_tradelines(
        self,
        user_id: str,
        tradeline_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Optimized tradeline deletion.
        """
        try:
            async with self.get_connection() as client:
                query = client.table("tradelines").delete().eq('user_id', user_id)
                
                if tradeline_ids:
                    query = query.in_('id', tradeline_ids)
                
                response = query.execute()
                deleted_count = len(response.data) if response.data else 0
                
                logger.info(f"Deleted {deleted_count} tradelines for user {user_id}")
                return {'deleted': deleted_count}
                
        except Exception as e:
            logger.error(f"Failed to delete tradelines: {e}")
            return {'deleted': 0}
    
    def _update_avg_query_time(self, query_time: float):
        """Update average query time."""
        alpha = 0.1
        if self._query_stats['average_query_time'] == 0:
            self._query_stats['average_query_time'] = query_time
        else:
            self._query_stats['average_query_time'] = (
                alpha * query_time + 
                (1 - alpha) * self._query_stats['average_query_time']
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database operation statistics."""
        return {
            **self._query_stats,
            'active_connections': self._active_connections,
            'cached_queries': len(self._query_cache)
        }
    
    def clear_cache(self):
        """Clear query cache."""
        self._query_cache.clear()
        self._cache_expiry.clear()
        logger.info("Database query cache cleared")
    
    async def cleanup(self):
        """Cleanup resources."""
        # Clear cache
        self.clear_cache()
        
        # Close connections (Supabase handles this automatically)
        logger.info("Database optimizer cleanup completed")


# Global database optimizer instance
db_optimizer = DatabaseOptimizer()


# Database migration/index creation SQL
DATABASE_OPTIMIZATIONS = """
-- Tradelines table optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_user_id 
ON tradelines (user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_user_created 
ON tradelines (user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_creditor 
ON tradelines (user_id, creditor_name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_status 
ON tradelines (user_id, account_status) 
WHERE account_status IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_negative 
ON tradelines (user_id, is_negative) 
WHERE is_negative = true;

-- Composite index for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_user_bureau_type 
ON tradelines (user_id, credit_bureau, account_type);

-- Unique constraint for preventing duplicates
ALTER TABLE tradelines 
ADD CONSTRAINT IF NOT EXISTS unique_user_account 
UNIQUE (user_id, creditor_name, account_number);

-- User profiles optimizations  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_email 
ON user_profiles (email);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_updated 
ON user_profiles (updated_at DESC);

-- Add created_at index if not exists
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tradelines_created 
ON tradelines (created_at DESC);
"""