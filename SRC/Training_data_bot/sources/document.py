
import json
import csv
from pathlib import Path
from typing import Union, Dict, Any, List
import asyncio

from .base import BaseLoader
from ..core.models import Document, DocumentType
from ..core.exceptions import DocumentLoadError
from ..core.logging import LogContext

class DocumentLoader(BaseLoader):
    """ Loader for text based document format """
    def __init__(self):
            
        super().__init__()
        self.supported_formats = [
            DocumentType.TXT,
            DocumentType.MD,
            DocumentType.HTML,
            DocumentType.JSON,
            DocumentType.CSV,
            DocumentType.DOCX
        ]
        
        
    async def load_single(
        self,
        source: Union[str, Path],
        encoding: str = 'utf-8',
        **kwargs
    ) -> Document:
        """ Load single document """
        
        source = Path(source)
        if not source.exists():
            raise DocumentLoadError(f"File not found: {source}")
        
        doc_type = self.get_document_type(source)
        
        with LogContext("load_document", file=str(source), type=doc_type.value):
            try:
                #Route to appropriate loader
                if doc_type == DocumentType.TXT:
                    content = await self._load_text(source, encoding)
                elif doc_type == DocumentType.MD:
                    content = await self._load_markdown(source, encoding)
                elif doc_type == DocumentType.HTML:
                    content = await self._load_html(source, encoding)
                elif doc_type == DocumentType.JSON:
                    content = await self._load_json(source, encoding)
                elif doc_type == DocumentType.CSV:
                    content = await self._load_csv(source, encoding)
                elif doc_type == DocumentType.DOCX:
                    content = await self._Load_docx(source)
                else:
                    raise DocumentLoadError(f"Unsupported format: {doc_type}")
                
                #create Document 
                title = source.stem
                document = self.create_document(
                    title = title,
                    content = content,
                    source = source,
                    doc_type=doc_type,
                    encoding= encoding,
                    extraction_method =f"DocumentLoader.{doc_type.value}"
                )
                
                return document
            except Exception as e:
                raise DocumentLoadError(
                    f"Failed to load {doc_type.value} file:  {source}",
                    file_path = str(source)
                    cause = e
                )
    
    async def _load_text(self, path: Path, encoding: str) -> str:
        """ Load the text file """
        return await asyncio.to_thread(path.read_text, encoding= encoding)
    
    async def _load_markdown(self, path: Path, encoding: str) -> str:
        """ Load Markdown file """
        return await asyncio.to_thread(path.read_text, encoding= encoding)

    async def _load_html(self, path: Path, encoding: str):
        """ Load HTML file and extract text content. """
        def _extract_html_text():
            try:
                from bs4 import BeautifulSoup
                
                with open(path, 'r', encoding=encoding) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Remove script
                for script in soup(["script", "style"]):
                    script.decompose()
                    
                # Extract clean text
                text = soup.get_text()
                
                # clean up whitespaces
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
                return " ".join(chunk for chunk in chunks if chunk)
            
            except ImportError:
                # Fallback if BeautifulSoup not available
                return path.read_text(encoding=encoding)
        return await asyncio.to_thread(_extract_html_text)
    
    async def _load_json(self, path, encoding):
        
        def _extract_json_text():

            with open(path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            # convert JSON to readable test
            if isinstance(data, dict):
                lines = []
                for key, value in data.items():
                    lines.append(f"{key}: {value}")
                return "\n".join(lines)
            elif isinstance(data, list):
                lines = []
                for i, item in enumerate(data):
                    lines.append(f'Item {i+1}: {item}')
                return "\n".join(lines)
            else:
                return str(data)
            
        return await asyncio.to_thread(_extract_json_text)
        
            
                
                
        