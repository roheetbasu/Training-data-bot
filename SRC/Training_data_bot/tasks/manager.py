
import asyncio
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..core.models import TaskType, TaskTemplate, TextChunk, TaskResult
from ..core.exceptions import TaskError, TemplateError
from ..core.logging import get_logger, LogContext
from .qa_generation import QAGenerator
from .classification import ClassficationGenerator
from .summarization import SummarizationGenerator

class TaskManager:
    """
        Manage task templates and execution  
    """
    def __init__(self):
        self.logger = get_logger("task_manager")
        self.templates: Dict[UUID, TaskTemplate] = {}
        
        #Initialize task generators
        self.generators = {
            TaskType.QA_GENERATION: QAGenerator(),
            TaskType.CLASSIFICATION: ClassficationGenerator(),
            TaskType.SUMMARIZATION: SummarizationGenerator(),
        }
        
        #Load Default templates
        self._load_default_templates()
    
    async def execute_task(
        self,
        task_type: TaskType,
        input_chunk: TextChunk,
        client,
        template_id: Optional[UUID] =None   
    ) -> TaskResult :
        """ Execute a task on given text """
        with LogContext("execute_task", task_type=task_type.value):
            try:
                # Get Template
                if template_id:
                    template = self.templates.get(template_id)
                    if not template:
                        raise TemplateError(f"Template not found: {template_id}")
                    else:
                        template = self._get_default_template(task_type.value)
                        
                        # get appropriate generetor
                        generator = self.generators.get(task_type)
        
    def _get_default_templates(self, task_type: TaskType):
        """ Get the default template for task type """
        # Find first template of the given type
        for template in self.templates.values():
            
            if template.task_type == task_type:
                return template
            
        # if no template found create a basic one
        return self._create_basic_template(task_type)
    
    def _create_basic_template(self, task_type: TaskType) -> TaskTemplate:
        """ Create basic template for task type """
        templates = {
            TaskType.QA_GENERATION: {
                "name": "Basic QA Generation",
                "prompt": "Generate question-answer pairs from the following text: \n\n{{text}}\n\nQuestion and Answers:",
                "description": "Basic question-answer generation template"
            },
            TaskType.CLASSIFICATION: {
                "name": "Basic Classification",
                "prompt": "Classify the following text: \n\n{{ text }}\n\nClassification:",
                "description": "Basic Text classification template"
            },
            TaskType.SUMMARIZATION: {
                "name": "Basic Summarization",
                "prompt": "Summarize the following text: \n\n{{ text }}\n\nSummarization:",
                "description": "Basic Text summarization template"
            }
        }
        
        template_config = templates.get(task_type)
        if not template_config:
            raise TaskError(f"No default task template available for {task_type}")
        