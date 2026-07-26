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
    QA_GENERATION = "qa_generation"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    NER = "named_entity_recognition"
    RED_TEAMING = "red_teaming"
    INSTRUCTION_RESPONSE = "instruction_response"
    
class QualityMetrics(str, Enum):
    """ Quality assessment metrics"""
    TOXICITY = "toxicity"
    BIAS = "bias"
    DIVERSITY = "diversity"
    COHERENCE = "coherence"
    RELEVANCE = "relevance"
    
class ProcessingStatus(str, Enum):
    """ Processing status values """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
class ExportFormat(str, Enum):
    """ Export format options """
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    
class Document(BaseEntity):
    """ Represent a source documents """
    
    title: str
    content: str
    source: str  # file path, url
    doc_type: DocumentType
    language: Optional[str] = "en"
    encoding: Optional[str] = "utf-8"
    size: int = 0
    word_count: int = 0
    char_count: int = 0
    
    #processing info
    extraction_method: Optional[str] = None
    processing_time: Optional[float] = None
    
    @validator("word_count", pre=True, always=True)
    def calculate_word_count(cls, v ,values):
        if v == 0 and "content" in values:
            return len(values["content"].split())
        return v
    
    @validator("char_count", pre=True, always=True)
    def calculate_char_count(cls, v ,values):
        if v == 0 and "content" in values:
            return len(values["content"])
        return v

    class TextChunk(BaseEntity):
        """ Represent the chunk from the documents """
        
        document_id : UUID
        content: str
        start_index: int
        end_index: int
        chunk_index: int
        token_count: int = 0
        
        #context preservation
        preceding_context: Optional[str] = None
        following_context: Optional[str] = None
        
        #semantic info
        embeddings: Optional[List[float]] = None
        topics: List[str] = Field(default_factory=list)
        
        @validator ("token_count", pre=True, always=True)
        def estimate_token_count(cls, v, values):
            if v == 0 and "content" in values:
                # Rough estimation: 1 token nearly equal to 4 character
                return  len(values["content"])//4
            return v 
        
        
