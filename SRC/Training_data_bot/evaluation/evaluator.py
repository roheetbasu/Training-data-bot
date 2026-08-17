import random

from ..core.models import Dataset, TrainingExample, QualityReport, QualityMetric, TaskType
from ..core.logging import get_logger

class QualityEvaluator:
    """ Evaluate quality of training data """
    
    def __init__(self):
        self.logger = get_logger("evaluator")
        
    async def evaluate_example(self, example: TrainingExample) -> QualityReport:
        """ Evaluate single training example """
        # Mock quality evaluation for now
        scores = {
            QualityMetric.TOXICITY: self._check_toxicity(example),
            QualityMetric.BIAS: self._check_bias(example),
            QualityMetric.DIVERSITY: self._check_diversity(example),
            QualityMetric.COHERENCE: self._check_coherence(example),
            QualityMetric.RELEVANCE: self._check_relevance(example),
        }
        
        overall_score = sum(scores.values()) / len(scores)
        passed = overall_score > 0.6
        
        issues = []
        warnings = []
        if not passed:
            issues.append("Quality score too low")
        if scores[QualityMetric.TOXICITY] < 0.7:
            warnings.append("Possible toxic content detected")
        if scores[QualityMetric.BIAS] < 0.7:
            warnings.append("Possible biased language detected")
            
        return QualityReport(
            target_id=example.id,
            target_type="example",
            overall_score=overall_score,
            passed=passed,
            metric_scores=scores,
            issues= issues,
            warnings = warnings  
        )
        
    async def evaluate_dataset(self, dataset: Dataset):
        """Evaluate an entire dataset by aggregating example-level scores."""
        if not dataset.examples:
            return QualityReport(
                target_id=dataset.id,
                target_type="dataset",
                overall_score=0.0,
                passed=False,
                metric_scores={},
                issues=["Dataset has no examples"],
                warnings=[],
            )
 
        # Score every example, then average each metric across the dataset
        example_reports = [await self.evaluate_example(ex) for ex in dataset.examples]
 
        metric_totals = {metric: 0.0 for metric in QualityMetric}
        for report in example_reports:
            for metric, score in report.metric_scores.items():
                metric_totals[metric] += score
 
        num_examples = len(example_reports)
        scores = {metric: total / num_examples for metric, total in metric_totals.items()}
 
        overall_score = sum(scores.values()) / len(scores)
        passed = overall_score > 0.7
 
        failed_count = sum(1 for r in example_reports if not r.passed)
        issues = []
        if not passed:
            issues.append("Dataset quality score too low")
        if failed_count > 0:
            issues.append(f"{failed_count}/{num_examples} examples failed quality checks")
 
        return QualityReport(
            target_id=dataset.id,
            target_type="dataset",
            overall_score=overall_score,
            passed=passed,
            metric_scores=scores,
            issues=issues,
            warnings=[],
        )
    
    def _check_toxicity(self, example):
        """ check for harmful or inappropriate content """
        
        content = example.input_text  + " " + example.output_text
        
        # check for toxic keywords
        toxic_keywords = ["hate", "violence", "discrimination", "harassment"]
        toxicity_score = 0.0
        
        for keyword in toxic_keywords:
            if keyword in content.lower():
                toxicity_score += 0.1
            
        # Lower score is better (less toxicity)
        return max(0.0, 1.0-toxicity_score)
    
    def _check_bias(self, example):
        """ Check for unfair bias in content """
        
        content = example.input_text + " " + example.output_text
        
        # check for biased language
        bias_indicators = ["always", "never", "all people", "everyone"]
        bias_score = 0.0
        
        for indicator in bias_indicators:
            if indicator in content.lower():
                bias_score += 0.1   
                
            
        return max(0.0, 1.0 - bias_score)
    
    def _check_diversity(self, example):
        """ Check content variety and uniqueness """
        
        #check the vocabulary diversity
        words = example.output_text.split()
        unique_words = set(words)
        
        if len(words) == 0:
            return 0.0
        
        # Higher diversity score is better
        diversity_ratio = len(unique_words) / len(words)
        return min(1.0, diversity_ratio * 2) #scale to 0-1 
        
    def _check_coherence(self, example):
        """ check logical consistency and clarity """
        
        # Basic coherence check
        output = example.output_text
        
        #check if output is not empty
        if not output.strip():
            return 0.0
        
        # check if output is related to input
        input_words = set(example.input_text.lower().split())
        output_words = set(output.lower().split())
        
        # calculate the words overlapping
        overlap = len(input_words.intersection(output_words))
        coherence_score = min(1.0, overlap/10) 
        
        return max(0.7, coherence_score) # minimum baseline
    
    def _check_relevance(self, example):
        """ check if output is relevant to input """
        
        # check task specific relevance
        if example.task_type == TaskType.QA_GENERATION:
            return self._check_qa_relevance(example)
        elif example.task_type == TaskType.CLASSIFICATION:
            return self._check_classification_relevance(example)
        elif example.task_type == TaskType.SUMMARIZATION:
            return self._check_summary_relevance(example)

        return 0.0 # Default relevance score
    
    def _check_qa_relevance(self, example):
        
        # check if output contain Q&A format
        output = example.output_text
        if "Q:" in output and "A:" in output:
            return 0.9
        return 0.3
    
    
    def _check_classification_relevance(self, example):
        
        # check whether the output looks like valid classification
        output = example.output_text.strip()
        
        if not output:
            return 0.0
        if len(output.split()) <= 5:
            return 0.9
        return 0.4
    
    def _check_summary_relevance(self, example):
        """ check if output is genuine summary """
        input_text = example.input_text
        output_text = example.output_text
        
        if not output_text:
            return 0.0
        
        input_len = len(input_text.split())
        output_len = len(output_text.split())
        
        if input_len == 0:
            return 0.0
        
        compression_ratio = output_len/input_len
        
        if compression_ratio < 0.5:
            return 0.9
        elif compression_ratio < 0.8:
            return 0.6
        return 0.3
     