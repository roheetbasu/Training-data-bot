
import time
from abc import ABC, abstractmethod
from uuid import uuid4

from ..core.models import TaskTemplate, TaskType, TextChunk
from ..core.logging import get_logger

class BaseTaskGenerator(ABC):
    """ Base class for task generator """
    
    def __init__(self):
        self.logger = get_logger(f"task.{self.__class__.__name__}")
    
    @abstractmethod
    async def execute(
        self,
        template: TaskTemplate,
        input_chunk: TextChunk,
        client
                      ):
        pass
    
    def _render_prompt(self, template: TaskTemplate, input_chunk: TextChunk):
        """ Render prompt template with input chunk"""
        try:
            from jinja2 import Template
            
            jinja_template = Template(template.prompt_template)
            return jinja_template.render(
                text = input_chunk.content,
                chunk = input_chunk,
                **template.parameters
            )
        except ImportError:
            # Simple fallback without Jinja2
            prompt = template.prompt_template
            prompt = prompt.replace("{{ text }}", input_chunk.content)
            prompt = prompt.replace("{{text}}", input_chunk.content)

            return prompt