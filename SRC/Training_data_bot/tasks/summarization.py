import time 
from uuid import uuid4

from .base import BaseTaskGenerator
from ..core.models import TaskTemplate, TaskResult, TextChunk, ProcessingStatus

class SummarizationGenerator(BaseTaskGenerator):
    """ Generate summaries from text """
    
    async def execute(
        self,
        template: TaskTemplate,
        input_chunk: TextChunk,
        client
    ) -> TaskResult:
        """ Execute summarization task """
        start_time = time.time()
        
        try:
            # Render Prompt
            prompt = self._render_prompt(template, input_chunk)
            
            #call Decodo Api
            response = await client.process_text(
                prompt = prompt,
                input_text = input_chunk,
                task_type = template.task_type
            ) 
            
            processing_time = time.time() - start_time
            
            return TaskResult(
                task_id = uuid4(),
                template_id = template.id,
                input_chunk_id=input_chunk.id,
                output = response.output or "",
                confidence = response.confidence,
                processing_time = processing_time,
                token_usage = response.token_usage,
                cost = response.cost,
                status = ProcessingStatus.COMPLETED
            )
            
        