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
        sources: Union[str, Path],
        **kwargs
    ):
        