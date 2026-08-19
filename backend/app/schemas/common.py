from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    total: int
    page: int = 1
    page_size: int = 10
    limit: Optional[int] = None
    offset: Optional[int] = None
    data: List[T]
