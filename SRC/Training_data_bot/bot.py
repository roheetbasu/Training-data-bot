"""
    Main Bot Class
"""
import asyncio
from pathlib import Path
from typing import Dict,List,Optional,Union,Any
from uuid import UUID

from .core.config import settings
from .core.logging import get_logger, LogContext
from .core.exceptions import TrainingDataBotError, ConfigurationError
from .core.models import (
    Document,
    Dataset,
    TrainingExample,
    TaskType,
    DocumentType,
    ProcessingJob,
    ProcessingStatus,
    QualityReport,
    ExportFormat,
)

from .sources import UnifiedLoader
from .decodo import DecodoClient
from .ai import AIClient
from .tasks import TaskManager
from .preprocessing import TextPreprocessor
from .evaluation import QualityEvaluator
from .storage import DatasetExporter, DatabaseManager 


class TrainingDataBot:
    """ 
    Main Training Bot Class
    
    This class  provides a high level interface for:
    - Loading documents from various sources
    - Processing text with task templates
    - Quality Assessment and filtering 
    - Dataset Creation and export
    """
    
    def __init__(self, config: Optional[Dict[str, Any]]):
        
        self.logger = get_logger("training_data_bot")
        self.config = config or {}
        self._init_components()
        self.logger.info("Training Data Bot intialized sucessfully")
        
    def _init_components(self):
        """Initiaize all bot components"""
        try:
            self.loader =UnifiedLoader()
            self.decodo_client = DecodoClient()
            self.ai_client = AIClient()
            self.taskmanager = TaskManager()
            self.preprocessing = TextPreprocessor()
            self.evaluator = QualityEvaluator()
            self.exporter = DatasetExporter()
            self.db_manager = DatabaseManager()
            
            #state (memory boxes)
            self.documents: Dict[UUID, Document] = {}
            self.datasets: Dict[UUID, Dataset] = {}
            self.jobs: Dict[UUID, ProcessingJob] = {}
            
        except Exception as e:
            raise ConfigurationError("Failed to initialize bot components",
                                     context={"error": str(e)},
                                     cause=e
                                     )
        
    async def load_documents(
        self,
        sources: Union[str, Path, List[Union[str, Path]]],
        doc_types: Optional[List[DocumentType]] = None,
        **kwargs
                )-> Document:
        
        with LogContext("documents_loading", sources=str(sources)):
            try:
                # Ensuring sources is a list 
                if isinstance ( sources , (str , Path )):
                    sources = [ sources ]
                
                # checking if any source is a directory
                documents = []
                for source in sources:
                    source_path = Path(source)
                    if source_path.is_dir():
                        dir_docs = await self.loader.load_directory(source_path)
                        documents.extend(dir_docs)
                    else:
                        doc =  await self.loader.load_single(source_path)
                        documents.append(doc)
                
                #store docs
                for doc in documents:
                    self.documents[doc.id] = doc
                    
                self.logger.info(f"Loaded {len(documents)} documents")
                return documents
            
            except Exception as e:
                self.logger.error(f"Failed to load documents: {e}")
                raise 
            
        
    async def process_documents(
        self,
        documents: Optional[List[Document]] = None,
        task_types: Optional[List[TaskType]] = None,
        quality_filter: bool = True,
        **kwargs    
    )-> Dataset:
        with LogContext("documents processing"):
            try:
                # use all documents if none is specified
                if documents is None:
                    documents = list(self.documents.values())
                
                if not documents:
                    raise TrainingDataBotError("No documents to process")
                
                # use a default task if none is specified
                if task_types is None:
                    task_types = [TaskType.QA_GENERATION]
                    
                #create a processing job 
                job = ProcessingJob(
                    name=f"Process {len(documents)} documents",
                    job_type="document_processing",
                    total_items=len(documents) * len(task_types),
                    input_data={
                        "document_count": len(documents),
                        "task_types": [t.values for t in task_types],
                        "quality_filter": quality_filter
                    }   
                )
                self.jobs[job.id]= job
                job.status = ProcessingStatus.PROCESSING
                
                #process documents
                all_examples = []
                
                for doc in documents:
                    #preprocessing the documents( chunking, cleaning)
                    chunks = await self.preprocessing.process_document(doc)
                    
                    # process each chunks with each chunks types
                    for task_type in task_types:
                        for chunk in chunks:
                            try:
                                #execute the task
                                result = await self.taskmanager.execute_task(
                                    task_type = task_type,
                                    input_chunk = chunk,
                                    client = self.ai_client
                                )
                                
                                #create an trainingexamples:
                                example = TrainingExample(
                                    input_text = chunk.content,
                                    output_text = result.output,
                                    task_type = task_type,
                                    source_document_id = doc.id,
                                    source_chunk_id = chunk.id,
                                    template_id = result.template_id,
                                    quality_scores = result.quality_scores
                                )
                                
                                # Apply quality filter
                                if quality_filter:
                                    quality_report = await self.evaluator.evaluate(example)
                                    if quality_report.passed:
                                        all_examples.append(example)
                                        example.quality_approved = True
                                    else:
                                        example.quality_approved = False
                                        self.logger.debug(f"Example filtered due to lack of quality")
                                else:
                                    all_examples.append(example)
                                
                                job.processed_items += 1
                                    
                            except Exception as e:
                                self.logger.error(f"Failed to process the chunk: {e}")
                                job.failed_items += 1
                                continue
                
                # create dataset
                dataset = Dataset(
                    name=f"Generated Dataset {len(self.datasets)  + 1}",
                    description=f"Dataset generated from {len(documents)} documents",
                    examples=all_examples
                )
                
                #store dataset
                self.datasets[dataset.id]=dataset
                
                #update job status
                job.status = ProcessingStatus.COMPLETED
                job.output_data = {
                    "dataset_id" : str(dataset.id),
                    "examples_generated": len(all_examples),
                    "quality_filtered": quality_filter,
                }
                
                self.logger.info(f"Processing Completed. Generated {len(all_examples)} examples")
                return dataset
        
            except Exception as e:
                if "job" in locals():
                    job.status = ProcessingStatus.FAILED
                    job.error_message = str(e)
                self.logger.error(f"Document processing failed: {e}")
                raise
            
    async def evaluate_dataset(
        self,
        dataset: Dataset,
        detailed_report: bool = True
    ):
        with LogContext("Dataset_evaluation", dataset_id=str(dataset.id)):
            try:
                report = await self.evaluator.evaluate_dataset(
                    dataset = dataset,
                    detailed = detailed_report
                )
                
                self.logger.info(f"Dataset Evaluation Completed. Overall score: {report.overall_score:.2f}")
                return report
            except Exception as e:
                self.logger.error(f"Dataset Evaluation failed: {e}")
                raise
    
    async def export_dataset(
        self,
        dataset: Dataset,
        output_path: Union[str, Path],
        format: ExportFormat = ExportFormat.JSONL,
        split_data: bool = True,
        **kwargs
    ):
        with LogContext("dataset_export", dataset_id=str(dataset.id), format=format.value):
            try:
                exported_path = await self.exporter.export_dataset(
                    dataset=dataset,
                    output_path=Path(output_path),
                    format=format,
                    split_data=split_data,
                    **kwargs
                )
                
                # Update dataset metadata
                dataset.export_format = format
                dataset.export_path = exported_path
                
                self.logger.info(f"Dataset exported to {exported_path}")
                return exported_path
            
            except Exception as e:
                self.logger.error(f"Dataset export failed: {e}")
                raise
    
    def get_statistics(self):
        return{
            "documents":{
                "total":len(self.documents),
                "by_type":self._count_by_type(self.documents.values(), "doc_type"),
                "total_size":sum(doc.size for doc in self.documents.values()),
            },
            "datasets":{
                "total":len(self.datasets),
                "total_examples":sum(len(ds.examples) for ds in self.datasets.values()),
                "by_task_types": self._count_examples_by_task_type(),
            },
            "jobs":{
                "total":len(self.jobs),
                "by_status":self._count_by_type(self.jobs.values(), "status"),
                "active":len([j for j in self.jobs.values() if j.status == ProcessingStatus.COMPLETED]),
            },
            "quality":{
                "approved_examples":sum(
                    len([ex for ex in ds.examples if ex.quality_approved])
                    for ds in self.datasets.values()
                ),
                "total_examples": sum(len(ds.examples) for ds in self.datasets.values()),
            }      
        }
        
    def _count_by_type(self, items, attr_name: str):
        
        counts={}
        for item in items:
            value = getattr(item, attr_name)
            if hasattr(value, "value"): #handle enums
                value = value.value
            counts[str(value)] = counts.get(str(value),0) + 1
        return counts
    
    def _count_examples_by_task_type(self):
        
        counts={}
        for dataset in self.datasets.values():
            for example in dataset.examples:
                task_type = example.task_type.value
                counts[task_type] = counts.get(task_type , 0)  + 1
        
        return counts
    
    async def cleanup(self):
        
        try:
            
            #close database connections
            await self.db_manager.close()
            
            #close Loader
            if hasattr(self.loader, 'close'):
                await self.loader.close()
                
            #close remaining http client
            if hasattr(self.decodo_client, 'close'):
                await self.decodo_client.close()
                
            # AI client cleanup
            if hasattr(self.ai_client, 'close'):
                await self.ai_client.close()
                
            self.logger.info("Bot cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Bot cleanup failed: {e}")
            
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    #Convenience methods
    async def quick_process(
        self,
        source:Union[str, Path],
        output_path: Union[str, Path],
        task_types: Optional[List[TaskType]] = None,
        export_format: ExportFormat = ExportFormat.JSONL
    ):
        
        #Load Documents
        documents = await self.load_documents([source])
        
        #Process documents
        dataset = await self.process_documents(
            documents=documents,
            task_types=task_types
        )
        
        #Export dataset
        
        

                
            
        
        
            
                
                                
                