"""_summary_
        This module provides a unified interface which automatically select the appropriate 
        loader based on format and source type
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Union, Any

from .base import BaseLoader
from .document import DocumentLoader
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
                self.supported_formats = list(DocumentType)
           
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
                                loader = self._select_loader(source)
                                
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
                 
        async def load_directory(
                self,
                directory: Union[str, Path],
                recursive: bool = True,
                file_patterns: Optional[List[str]] = None,
                **kwargs
        ) -> List[Document]:
                """
                        Load all the supported documents  
                """
                directory = Path(directory)
                
                if not directory.exists() or not directory.is_dir():
                        raise DocumentLoadError(f"Directory not found: {directory}")
                
                #Find all supported files
                sources = self._find_supported_files(
                        directory,
                        recursive = recursive,
                        patterns = file_patterns
                )
                
                if not sources:
                        self.logger.warning(f"No supported files found in {directory}")
                        return []
                self.logger.info(f"Found {len(sources)} supported files")
                
                # Load all files
                return await self.load_multiple(sources, **kwargs)
                
                
                
        def _select_loader(self, source:Union[str, Path]) -> Optional[BaseLoader]:
                """
                 Select the appropriate loader for the given source
                """
                
                try:
                        # Handle urls
                        if isinstance(source, str) and source.startswith(('http://','https://')):
                                return self.web_loader
                        
                        # Handle file paths
                        source = Path(source) if isinstance(source, str) else source
                        
                        if not source.exists():
                                return None
                        
                        # Get file Extension
                        suffix = source.suffix.lower().strip('.')
                        
                        try:
                                doc_type = DocumentType(suffix)
                        except ValueError:
                                return None
                        
                        # Route to appropriate loader
                        if doc_type == DocumentType.PDF:
                                return self.pdf_loader
                        elif doc_type in [DocumentType.TXT, DocumentType.MD, DocumentType.HTML,
                                          DocumentType.JSON, DocumentType.CSV, DocumentType.DOCX]:
                                return self.document_loader
                        else:
                                return None
                        
                except Exception as e:
                        self.logger.error(f"Error selecting leader for {source}: {e}")
                        return None
                
         
        def _find_supported_files(
                self,
                directory: Path,
                recursive: bool = True,
                patterns: Optional[List[str]] = None
        ):
                """
                        Find all supported files in the directory  
                """
                supported_files = []
                
                #Build supported extensions
                supported_extensions = {
                        f".{doc_type.value.lower()}"
                        for doc_type in DocumentType
                        if doc_type != DocumentType.URL
                }
                
                #If user didn't specify patterns 
                if patterns is None:
                        patterns = ["*"]
                
                for pattern in patterns: 
                        
                        iterator = (
                                directory.rglob(pattern)
                                if recursive
                                else directory.glob(pattern)
                        )
                        
                        for path in iterator:
                                
                                if not path.is_file():
                                        continue
                                if path.suffix.lower() in supported_extensions:
                                        supported_files.append(path)
                                
                # Remove duplicates
                seen = set()
                unique_files = []
                
                for path in supported_files:
                        if path not in seen:
                                seen.add(path)
                                unique_files.append(path)
                
                return unique_files
                        