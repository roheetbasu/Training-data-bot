import time 
from uuid import uuid4

from .base import BaseTaskGenerator
from ..core.models import TaskTemplate, TaskResult, TextChunk, ProcessingStatus

class SummarizationGenerator(BaseTaskGenerator):
    """ Generate summaries from text """
    
    async def execute(
        self,
        template = TaskTemplate,
        input_chunk = TextChunk,
        client
    ) -> TaskResult:
        """ Execute summarization task """
        