import re
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
        
        self.logger.debug(f"Created {len(chunks)} chunks from document: {document.id}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """ Basic Text Cleaning """
        # Remove excessive whitespaces
        text = re.sub(r'\s+', '', text)
        
        #Remove very short lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return '\n'.join(lines)
    