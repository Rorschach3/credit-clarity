"""
Tradelines management endpoints
CRUD operations for credit report tradelines
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_supabase_user
from schemas.responses import APIResponse, PaginatedResponse
from schemas.requests import PaginationParams
from schemas.tradelines import (
    TradelineResponse, 
    TradelineCreate,
    TradelineUpdate,
    TradeLinesStats,
    BulkTradelineOperation
)
from services.database_optimizer import db_optimizer
from services.monitoring import monitor_api_call, track_user_activity

router = APIRouter(prefix="/tradelines", tags=["Tradelines"])

@router.get("/", response_model=PaginatedResponse[TradelineResponse])
@monitor_api_call
async def get_user_tradelines(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    pagination: PaginationParams = Depends(),
    credit_bureau: Optional[str] = Query(None, description="Filter by credit bureau"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    is_negative: Optional[bool] = Query(None, description="Filter by negative status"),
    disputed: Optional[bool] = Query(None, description="Filter by dispute status")
):
    """
    Get user's tradelines with pagination and filtering.
    Supports filtering by credit bureau, account type, and dispute status.
    """
    user_id = current_user.get('id')
    track_user_activity("get_tradelines", user_id)
    
    # Build filters
    filters = {}
    if credit_bureau:
        filters['credit_bureau'] = credit_bureau
    if account_type:
        filters['account_type'] = account_type
    if is_negative is not None:
        filters['is_negative'] = is_negative
    if disputed is not None:
        filters['dispute_count'] = {'$gt': 0} if disputed else {'$eq': 0}
    
    # Get paginated results
    result = await db_optimizer.get_user_tradelines_paginated(
        user_id=user_id,
        page=pagination.page,
        limit=pagination.limit,
        filters=filters,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order
    )
    
    return PaginatedResponse[TradelineResponse](
        success=True,
        data=[TradelineResponse(**item) for item in result['items']],
        meta=result['meta'],
        message=f"Retrieved {len(result['items'])} tradelines"
    )

@router.get("/{tradeline_id}", response_model=APIResponse[TradelineResponse])
@monitor_api_call
async def get_tradeline(
    tradeline_id: int,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get specific tradeline by ID."""
    user_id = current_user.get('id')
    
    tradeline = await db_optimizer.get_tradeline_by_id(tradeline_id, user_id)
    
    if not tradeline:
        raise HTTPException(status_code=404, detail="Tradeline not found")
    
    return APIResponse[TradelineResponse](
        success=True,
        data=TradelineResponse(**tradeline),
        message="Tradeline retrieved"
    )

@router.post("/", response_model=APIResponse[TradelineResponse])
@monitor_api_call
async def create_tradeline(
    tradeline_data: TradelineCreate,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Create a new tradeline."""
    user_id = current_user.get('id')
    track_user_activity("create_tradeline", user_id)
    
    # Set user ID
    tradeline_dict = tradeline_data.dict()
    tradeline_dict['user_id'] = user_id
    
    # Create tradeline
    created_tradeline = await db_optimizer.create_tradeline(tradeline_dict)
    
    return APIResponse[TradelineResponse](
        success=True,
        data=TradelineResponse(**created_tradeline),
        message="Tradeline created successfully"
    )

@router.put("/{tradeline_id}", response_model=APIResponse[TradelineResponse])
@monitor_api_call
async def update_tradeline(
    tradeline_id: int,
    update_data: TradelineUpdate,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Update existing tradeline."""
    user_id = current_user.get('id')
    track_user_activity("update_tradeline", user_id)
    
    # Verify ownership
    existing = await db_optimizer.get_tradeline_by_id(tradeline_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tradeline not found")
    
    # Update with only provided fields
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    updated_tradeline = await db_optimizer.update_tradeline(tradeline_id, update_dict)
    
    return APIResponse[TradelineResponse](
        success=True,
        data=TradelineResponse(**updated_tradeline),
        message="Tradeline updated successfully"
    )

@router.delete("/{tradeline_id}", response_model=APIResponse[Dict[str, str]])
@monitor_api_call
async def delete_tradeline(
    tradeline_id: int,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Delete a tradeline."""
    user_id = current_user.get('id')
    track_user_activity("delete_tradeline", user_id)
    
    # Verify ownership
    existing = await db_optimizer.get_tradeline_by_id(tradeline_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tradeline not found")
    
    # Delete tradeline
    deleted = await db_optimizer.delete_tradeline(tradeline_id, user_id)
    
    if not deleted:
        raise HTTPException(status_code=400, detail="Failed to delete tradeline")
    
    return APIResponse[Dict[str, str]](
        success=True,
        data={"id": str(tradeline_id), "status": "deleted"},
        message="Tradeline deleted successfully"
    )

@router.get("/stats/summary", response_model=APIResponse[TradeLinesStats])
@monitor_api_call
async def get_tradelines_stats(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get comprehensive statistics about user's tradelines."""
    user_id = current_user.get('id')
    track_user_activity("get_tradeline_stats", user_id)
    
    stats = await db_optimizer.get_tradelines_statistics(user_id)
    
    return APIResponse[TradeLinesStats](
        success=True,
        data=TradeLinesStats(**stats),
        message="Tradeline statistics retrieved"
    )

@router.post("/bulk", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def bulk_tradeline_operation(
    operation: BulkTradelineOperation,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Perform bulk operations on multiple tradelines."""
    user_id = current_user.get('id')
    track_user_activity(f"bulk_{operation.operation}", user_id)
    
    # Verify all tradelines belong to user
    for tradeline_id in operation.tradeline_ids:
        existing = await db_optimizer.get_tradeline_by_id(tradeline_id, user_id)
        if not existing:
            raise HTTPException(
                status_code=404, 
                detail=f"Tradeline {tradeline_id} not found"
            )
    
    # Perform bulk operation
    if operation.operation == "update":
        if not operation.update_data:
            raise HTTPException(status_code=400, detail="Update data required")
        
        result = await db_optimizer.bulk_update_tradelines(
            tradeline_ids=operation.tradeline_ids,
            update_data=operation.update_data,
            batch_size=operation.batch_size
        )
        
    elif operation.operation == "delete":
        result = await db_optimizer.bulk_delete_tradelines(
            tradeline_ids=operation.tradeline_ids,
            user_id=user_id,
            batch_size=operation.batch_size
        )
        
    elif operation.operation == "dispute":
        # Increment dispute count for selected tradelines
        result = await db_optimizer.bulk_update_tradelines(
            tradeline_ids=operation.tradeline_ids,
            update_data={"dispute_count": "increment"},
            batch_size=operation.batch_size
        )
        
    else:
        raise HTTPException(status_code=400, detail="Invalid operation")
    
    return APIResponse[Dict[str, Any]](
        success=True,
        data={
            "operation": operation.operation,
            "affected_count": result.get("affected_count", 0),
            "processed_ids": operation.tradeline_ids
        },
        message=f"Bulk {operation.operation} completed successfully"
    )