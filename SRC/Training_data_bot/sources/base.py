"""
    Base Loader class for document sources
    
    This module provide a abstract base class for all the document loaders to
    inherit from, ensuring consistent interface and behaviour
    
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, AsyncGenerator

from ..core.models import Document, DocumentType
from ..core.exceptions import DocumentLoadError, UnsupportedFormatError
from ..core.logging import get_logger, LogContext

class BaseLoader(ABC):
    """ 
        Abstract Base class for all the loaders 
    """
    
    def __init__(self):
        self.logger = get_logger(f"loader.{self.__class__.__name__}")
        self.supported_formats:  List[DocumentType] = []
        
    @abstractmethod
    async def load_single(
        self,
        source : Union[str, Path],
        **kwargs
    ):
        """ 
            Load single documents
        """
        pass # specific loader will use this function as base
    
        
    async def load_multiple(
        self,
        sources: List[Union[str, Path]],
        max_workers: int = 4,
        **kwargs
    ):
        """ 
            Load multiple documents
        """
        with LogContext("load_multiple", source_count=len(sources)):
            semaphore = asyncio.Semaphore(max_workers)
            
            async def load_with_semaphore(source):
                async with semaphore:
                    try:
                        return await self.load_single(source)
                    except Exception as e:
                        self.logger.error(f"Failed to load '{source}' : {e}")
                        return None 
            
            # Load all sources concurrently
            tasks = [load_with_semaphore(source) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            #Filter out the failed loads and exceptions
            documents = []
            for i, result in enumerate(results):
                if isinstance(result, Document):
                    documents.append(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Error loading {result}")
                # None results (failed loads) are already removed
            
            self.logger.info(f"Sucessfully loaded {len(documents)}")
            return documents
    
    async def load_stream(
        self,
        sources: List[Union[str, Path]],
        **kwargs
    ):
        """
            Load documents as a stream (generator).   
        """
        
        for source in sources:
            try:
                document = await self.load_single(source, **kwargs)
                yield document
            except Exception as e:
                self.logger.error(f"Failed to load {source}: {e}")
                continue
    
    def supports_format(self, doc_type: DocumentType) -> bool:
        """ Check if loader suuport the given format"""
        return doc_type in self.supported_formats
        
    def validate_source(self, source: Union[str, Path]) -> bool:
        """ Validate if source can be loaded by this loader"""
        try:
            if isinstance(source, str):
                if source.startswith(("http://","https://")):
                    # URL 
                    return DocumentType.URL in self.supported_formats
                else:
                    source = Path(source)
                    
                if isinstance(source, Path):
                    if not source.exists():
                        return False
                    
                    # check suffix of the file extension
                    suffix = source.suffix.lower().strip('.')
                    try:
                        doc_type = DocumentType(suffix)
                        return self.supports_format(doc_type)
                    except ValueError:
                        return False
                
                return True
            
        except Exception:
            return False
        
    def get_document_type(self, source: Union[str, Path]) -> DocumentType:
        """ Determine document type from source """
        
        if isinstance(source, str):
            if source.startswith(('http://', "https://")):
                return DocumentType.URL
            else:
                source = Path(source)
                
        if isinstance(source, Path):
            suffix= source.suffix.lower().strip('.')
            try:
                return DocumentType(suffix)
            except ValueError:
                raise UnsupportedFormatError(
                    file_format = suffix,
                    supported_formats = [fmt.value for fmt in self.supported_formats]
                )
        raise UnsupportedFormatError(
            file_format="unknown",
            supported_formats = [fmt.value for fmt in self.supported_formats]
        )
    
    def extract_metadata(self, source: Union[str, Path]) -> Dict[str, Any]:
        """ Extract meta data from the path """
        metadata = {}
        
        if isinstance(source, str):
            metadata["source"] = source
            if source.startswith (("https://, http://")):
                metadata["source_type"] = "url"
            else:
                metadata["source_type"] = "file"
                source = Path(source)
                
        if isinstance (source, Path):
            metadata['source'] = str(source.absolute())
            metadata['source_type'] = "file"
            metadata['filename'] = source.name
            metadata['extension'] = source.suffix   
            
            if source.exists():
                stat = source.stat()
                metadata['size'] = stat.st_size
                metadata['modified_time'] = stat.st_mtime
        
        return metadata
                
    