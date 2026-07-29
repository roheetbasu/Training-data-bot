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
from ..core.exceptions import DocumentLoadError, UnsupportedFormatError
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
           
        async def load_single(
                self,
                source: Union[str, Path],
                **kwargs
        ) -> Document:
                """
                Loads document 
                """
                with LogContext("Unified_load_single", source=str(source)):
                        try:
                                #Determine source type and select appropriate leader
                                loader = self.__select__loader(source)
                                
                                if loader is None:
                                        raise UnsupportedFormatError(
                                                file_format=str(source),
                                                supported_formats=[fmt.value for fmt in self.supported_formats]
                                        )

                                #Load using selected loader
                                document = await loader.load_single(source, **kwargs)
                                self.logger.debug(f"Successfully loaded {source} using {loader.__class__.__name__}")
                                
                                return document
                        
                        except Exception as e:
                                raise DocumentLoadError(
                                        f"failed to load document from {source}",
                                        file_path=str(source),
                                        cause=e
                                )
                 
                
        