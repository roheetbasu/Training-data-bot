import json,csv
from pathlib import Path
from typing import Union

from ..core.logging import get_logger
from ..core.models import Dataset, ExportFormat

class DatasetExporter:
    """ Export datasets to various format """
    
    def __init__(self):
        self.logger = get_logger("exporter")
    
    async def export_dataset(
        self,
        dataset: Dataset,
        output_path: Path,
        format: ExportFormat = ExportFormat.JSONL,
        split_data: bool = True,
        **kwargs
    ) -> Path:
        """ Export dataset to file """
        
        if format == ExportFormat.JSONL:
            return await self._export_jsonl(dataset, output_path, split_data)
        elif format == ExportFormat.CSV:
            return await self._export_csv(dataset, output_path)
        else:
            # Default to JSONL
            return await self._export_jsonl(dataset, output_path, split_data)
        
    async def _export_jsonl(self, dataset: Dataset, output_path: Path, split_data: bool = True):
        """ Export to JSONL format """
        output_path = output_path.with_suffix(".jsonl")
        
        # create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # convert example into jsonl format
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in dataset.examples:
                line = {
                    "input": example.input_text,
                    "output": example.output_text,
                    "task_type": example.task_type.value if hasattr(example.task_type, 'value') else example.task_type,
                    "id": str(example.id),
                    "metadata": {
                        "source_document_id": str(example.source_document_id),
                        "quality_scores": {k.value if hasattr(k, 'value') else k:v
                                           for k,v in example.quality_scores.items()},
                        "quality_approved": example.quality_approved,
                    }
                }
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        
        self.logger.info(f"Exported {len(dataset.examples)} examples to {output_path} in JSONL format")
        return output_path
    
    async def _export_csv(self, dataset: Dataset, output_path: Path) -> Path:
        """ Export to CSV format """
        
        output_path = output_path.with_suffix('.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # write header
            writer.writerow(['input', 'output', 'task_type', 'id', 'quality_approved'])
            
            #write data
            for example in dataset.examples:
                writer.writerow([
                    example.input_text,
                    example.output_text,
                    example.task_type.value if hasattr(example.task_type, 'value') else example.task_type,
                    str(example.id),
                    example.quality_approved]
                )
                
        self.logger.info(f"Exported {len(dataset.examples)} examples to {output_path} in CSV format")
        return output_path