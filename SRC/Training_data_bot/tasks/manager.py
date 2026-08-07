
import asyncio
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import time
from ..core.models import TaskType, TaskTemplate, TextChunk, TaskResult, ProcessingStatus
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
            start_time = time.perf_counter()
            try:
                # Get Template
                if template_id:
                    template = self.templates.get(template_id)
                    if not template:
                        raise TemplateError(f"Template not found: {template_id}")
                else:
                    template = self._get_default_template(task_type)
                        
                # get appropriate generetor
                generator = self.generators.get(task_type)
                
                if not generator:
                    raise TaskError(f"No generator found for task type: {task_type}")
                        
                #Execute task
                result = await generator.execute(
                    template=template,
                    input_chunk=input_chunk,
                    client=client
                )
                        
                self.logger.debug(f"Successfully executed {task_type.value} for chunk {input_chunk.id}")
                return result
                    
            except Exception as e:
                self.logger.error(f"Task {task_type.value} failed: {e}")
                
                # Return failed result
                return TaskResult(
                    task_id = uuid4(),
                    template_id=template.id if "template" in locals() else None,
                    input_chunk_id=input_chunk.id,
                    output = "",
                    status=ProcessingStatus.FAILED,
                    error_message=str(e),
                    processing_time=time.perf_counter() - start_time                    
                )
                    
                        
    def _load_default_templates(self):
        """Load default templates."""

        for task_type in TaskType:
            self._create_basic_template(task_type)
        
    async def create_template(
        self,
        name:str,
        task_type: TaskType,
        prompt_template: str,
        description: str="",
        **parameters
    ) -> UUID:
        """ Create new template """
        
        template = TaskTemplate(
            name=name,
            task_type=task_type,
            description=description,
            prompt_template=prompt_template,
            parameters=parameters
        )
        
        self.templates[template.id] = template
        self.logger.info(f"Created template '{name}' with ID: {template.id}")
        
        return template.id
        
        
    def get_template(self, template_id: UUID):
        """ Get template by ID. """
        return self.templates.get(template_id)
    
    def list_templates(self, task_type: Optional[TaskType]):
        """ List all templates """
        if task_type is None:
            return list(self.templates.values())
        
        return [
            template 
            for template in self.templates.values()
            if template.task_type == task_type
        ]   
     
    def _get_default_template(self, task_type: TaskType):
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
        
        template = TaskTemplate(
        name=template_config["name"],
        task_type=task_type,
        description=template_config["description"],
        prompt_template=template_config["prompt"]
        )

        self.templates[template.id] = template

        return template
    
    if __name__ == "__main__":
        template = TaskTemplate(
        name="Test",
        task_type=TaskType.QA_GENERATION,
        description="test",
        prompt_template="Hello {{ text }}"
    )

        print(template)
        print(template.id)