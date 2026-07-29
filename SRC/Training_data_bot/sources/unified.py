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
                super().__init__()
                self.logger = get_logger("loader.UnifiedLoader")
                
                #Initialize sub-loader (share DecodoClient with WebLoader)
                self.document_loader = DocumentLoader()
                self.pdf_loader = PDFLoader() 
                
                if decodo_client:
                        #use shared DecodoClient instances for better resources management
                        self.web_loader = WebLoader(use_decodo=True)
                        self.web_loader.decodo_client = decodo_client
                        self.web_loader.use_decodo = True
                        self.logger.info("Unified Loader using shared Decodo Client")
                else:
                        self.web_loader = WebLoader()
                
                # All supported formats
                self.supported_formats = list(DocumentLoader)
                
                
        