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
        words = example.output_text
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
     