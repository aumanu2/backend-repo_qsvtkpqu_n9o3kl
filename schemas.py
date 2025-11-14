"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Habit Tracker Schemas

class Habit(BaseModel):
    """
    Habits collection schema
    Collection name: "habit"
    """
    name: str = Field(..., description="Short name of the habit")
    description: Optional[str] = Field(None, description="Brief description")
    color: str = Field("#6366f1", description="Hex color used for UI chips")
    frequency: str = Field("daily", description="Frequency type: daily/weekly")
    days_of_week: Optional[List[int]] = Field(
        None,
        description="For weekly habits: which weekdays are active (0=Mon..6=Sun)",
    )

class Habitlog(BaseModel):
    """
    Habit logs collection schema
    Collection name: "habitlog"
    """
    habit_id: str = Field(..., description="ID of the habit (stringified ObjectId)")
    day: date = Field(..., description="The calendar day for the check-in (YYYY-MM-DD)")
    value: int = Field(1, description="Numeric value for the day, default 1 meaning done")
