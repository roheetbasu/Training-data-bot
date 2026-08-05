
from ..core.models import Document, TextChunk
from ..core.config import settings
from ..core.logging import get_logger

class TextProcessor():
    """ Text Processing and chunking """
    
    def __init__(self):
        self.logger = get_logger("preprocessor")
        self.chunk_size = settings.processing.chunk_size
        self.chunk_overlap = settings.processing.chunk_overlap
    
    