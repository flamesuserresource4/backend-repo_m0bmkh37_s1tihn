"""
Database Schemas

Pydantic models that define collections used by the app.
Each class name lowercased becomes its collection name.
"""
from typing import Optional, Literal, Any, Dict
from pydantic import BaseModel, Field

class ExtractionJob(BaseModel):
    """
    Stores a log of a document extraction/analysis job
    Collection name: "extractionjob" (lowercase of class)
    """
    job_type: Literal[
        "bank_statement",
        "invoice",
        "receipt",
        "salary_slip",
        "credit_card",
        "table_extract",
        "summarize",
        "translate",
        "chat",
    ] = Field(..., description="Type of job executed")
    filename: str = Field(..., description="Original uploaded filename")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    status: Literal["success", "error"] = Field(..., description="Job status")
    result_summary: Optional[str] = Field(None, description="Short human summary of result")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata for the job")

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
