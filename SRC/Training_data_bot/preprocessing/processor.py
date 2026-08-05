import re
from typing import List

from ..core.models import Document, TextChunk
from ..core.config import settings
from ..core.logging import get_logger

class TextProcessor():
    """ Text Processing and chunking """
    
    def __init__(self):
        self.logger = get_logger("preprocessor")
        self.chunk_size = settings.processing.chunk_size
        self.chunk_overlap = settings.processing.chunk_overlap
    
    async def process_document(self, document: Document) -> List[TextChunk]:
        """ Process document into chunk """
        
        #clean text
        cleaned_text = self._clean_text(document.content)
        
        #create chunks
        chunks = self._create_chunks(cleaned_text, document.id)
        
        self.logger.debug(f"Created {len(chunks)} chunks from document")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """ Basic Text Cleaning """
        # Remove excessive whitespaces
        text = re.sub(r'\s+', '', text)
        
        #Remove very short lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return '\n'.join(lines)
    
    def _create_chunks(self, text: str, document_id) -> List[TextChunk]:
        """ Create text chunks with overlap """
        chunks: List[TextChunk] = []
        words = text.split()
        
        if len(words) <= self.chunk_size:
            # single chunk
            chunk = TextChunk(
                document_id = document_id,
                content = text,
                start_index = 0,
                end_index = len(text),
                chunk_index = 0,
                token_count=len(words)
            )
            chunks.append(chunk)
        else:
            #Multiple chunks
            chunk_index = 0
            start_word = 0
            
            if self.chunk_overlap >= self.chunk_size:
                raise ValueError(
                    "chunk_overlap must be smaller than chunk size"
                )
                
            while start_word < len(words):
                end_word = min(start_word + self.chunk_size, len(words))
                chunk_words = words[start_word:end_word]
                chunk_text = ' '.join(chunk_words)
                
                chunk = TextChunk(
                document_id = document_id,
                content = chunk_text,
                start_index = start_word,
                end_index = end_word,
                chunk_index = chunk_index,
                token_count=len(chunk_words)
                )
                chunks.append(chunk)
                
                # Move to next chunk with overlap
                start_word = end_word - self.chunk_overlap
                chunk_index += 1
                
                if end_word >= len(words):
                    break
        return chunks