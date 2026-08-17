from pathlib import Path

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
        split_data: bool = True
    ) -> Path:
        """ Export dataset to file """
        
        if format == ExportFormat.JSONL:
            return await self._export_jsonl(dataset, output_path, split_data)
        elif format == ExportFormat.CSV:
            return await self._export_csv(dataset, output_path)
        else:
            # Default to JSONL
            return await self._export_jsonl(dataset, output_path, split_data)
        