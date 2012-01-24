from SingleStageDetector import SingleStageDetector
from ExampleBuilders.UnmergingExampleBuilder import UnmergingExampleBuilder
from Classifiers.SVMMultiClassClassifier import SVMMultiClassClassifier
from Evaluators.AveragingMultiClassEvaluator import AveragingMultiClassEvaluator

class UnmergingDetector(SingleStageDetector):
    def __init__(self):
        SingleStageDetector.__init__(self)
        self.exampleBuilder = UnmergingExampleBuilder
        self.classifier = SVMMultiClassClassifier
        self.evaluator = AveragingMultiClassEvaluator
        self.tag = "unmerging-"