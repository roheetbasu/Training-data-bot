import time
from uuid import uuid4

from .base import BaseTaskGenerator
from ..core.models import TaskTemplate, TaskResult, TextChunk, ProcessingStatus


class ClassficationGenerator(BaseTaskGenerator):
    """ Classify text into categories. """
    
    async def execute(
        self,
        template: TaskTemplate,
        input_chunk: TextChunk,
        client
    ) -> TaskResult:
        """ Execute classification task """
        start_time = time.time()
        
        try:
            # Render Prompt
            prompt = self._render_prompt(template, input_chunk)
            
            # Call Decodo API
            response = await client.process_text(
                prompt=prompt,
                input_text=input_chunk.content,
                task_type=template.task_type
            )
            
            processing_time = time.time() - start_time
            
            return TaskResult(
                task_id=uuid4(),
                template_id=template.id,
                input_chunk_id=input_chunk.id,
                output=response.output or "",
                confidence=response.confidence,
                processing_time=processing_time,
                token_usage=response.token_usage,
                cost=response.cost,
                status=ProcessingStatus.COMPLETED
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return TaskResult(
                task_id=uuid4(),
                template_id=template.id,
                input_chunk_id=input_chunk.id,
                output="",
                processing_time=processing_time,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            
            