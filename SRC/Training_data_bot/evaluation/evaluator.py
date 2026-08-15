import random

from ..core.models import Dataset, TrainingExample, QualityReport, QualityMetric
from ..core.logging import get_logger

class QualityEvaluator:
    """ Evaluate quality of training data """
    
    def __init__(self):
        self.logger = get_logger("evaluator")
        
    async def evaluate_example(self, example: TrainingExample) -> QualityReport:
        """ Evaluate single training example """
        # Mock quality evaluation for now
        scores = {
            QualityMetric.TOXICITY: random.uniform(0.1,0.3),
            QualityMetric.BIAS: random.uniform(0.1, 0.4),
            QualityMetric.DIVERSITY: random.uniform(0.6, 0.9),
            QualityMetric.COHERENCE: random.uniform(0.7, 0.95),
            QualityMetric.RELEVANCE: random.uniform(0.8, 0.95),
        }
        
        overall_score = sum(scores.values()) / len(scores)
        passed = overall_score > 0.6
        
        return QualityReport(
            target_id=example.id,
            target_type="example",
            overall_score=overall_score,
            passed=passed,
            metric_scores=scores,
            issues=[] if passed else ["Quality score too low"],
            warning = []  
        )
        
    async def evaluate_dataset(self, dataset; Dataset):
        """ Evaluate entire dataset """
        # Mock dataset evaluation
        scores = {
            QualityMetric.TOXICITY: 0.2,
            QualityMetric.BIAS: 0.3,
            QualityMetric.DIVERSITY: 0.8,
            QualityMetric.COHERENCE: 0.85,
            QualityMetric.RELEVANCE: 0.9
        }
        
        overall_score = sum(scores.values()) / len(scores)
        passed = overall_score > 0.7
        
        return QualityReport(
            target_id=dataset.id,
            target_type="dataset",
            overall_score=overall_score,
            passed=passed,
            metric_scores=scores,
            issues=[] if passed else ["Dataset quality score too low"],
            warning = []  
        )