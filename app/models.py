from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for RAG query endpoint."""

    query: str = Field(..., description="The user's query")
    user_id: str = Field(..., description="User ID for permission checking")
    # department: str = Field(
    #     ..., description="User's department (marketing, engineering, finance)"
    # )


class QueryResponse(BaseModel):
    """Response model for RAG query endpoint."""

    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents used")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    mongodb: bool = Field(..., description="MongoDB connection status")
    permit: bool = Field(..., description="Permit.io connection status")
