"""_summary_
        This module provides a unified interface which automatically select the appropriate 
        loader based on format and source type
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Union, Any

from .base import BaseLoader
from .documents import DocumentLoader
from .pdf import PDFLoader
from .web import WebLoader
from ..core.models import Document, DocumentType
from ..core.exceptions import DocumentLoadError, UnsupportedFormat
from ..core.logging import get_logger, LogContext

class UnifiedLoader(BaseLoader):
        """
        Unified Loader automatically select appropriate sub loader
        """
        
        def __init__(self, decodo_client = None):
                
                
                
                
        