from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, root_validator

class BaseEntity(BaseModel):
    """ Base class for all entities with common fields"""
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict) 
    
    class config:
        use_enum_values = True
        allow_population_by_field_name = True
        arbitary_types_allowed = True
        
    #Enum
    class DocumentType(str, Enum):
        """Supported Document types"""
        PDF = "pdf"
        DOCX = "docx"
        TXT = "txt"
        MD = "md"
        HTML = "html"
        JSON = "json"
        CSV = "csv"
        URL = "url"
        
    class TaskType(str, Enum):
        """Available Task types"""
        
