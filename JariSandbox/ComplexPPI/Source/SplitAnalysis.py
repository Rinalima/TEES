import Core.ExampleUtils as Example
import sys, os
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import cElementTree as ET
#from ExampleBuilders.SimpleDependencyExampleBuilder import SimpleDependencyExampleBuilder
from InteractionXML.CorpusElements import CorpusElements
from Core.SentenceGraph import *
#from Classifiers.SVMLightClassifier import SVMLightClassifier as Classifier
#from Core.Evaluation import Evaluation
from Visualization.CorpusVisualizer import CorpusVisualizer
from Utils.ProgressCounter import ProgressCounter
from Utils.Parameters import splitParameters
from optparse import OptionParser

def buildExamples(exampleBuilder, sentences, options):
    examples = []
    counter = ProgressCounter(len(sentences), "Build examples")
    for sentence in sentences:
        counter.update(1, "Building examples ("+sentence[0].getSentenceId()+"): ")
        sentence[1] = exampleBuilder.buildExamples(sentence[0])
        examples.extend(sentence[1])
    print >> sys.stderr, "Examples built:", len(examples)    
    # Save examples
    if options.output != None:
        print >> sys.stderr, "Saving examples to", options.output + "/examples.txt"
        commentLines = []
        commentLines.append("Input file: " + options.input)
        commentLines.append("Example builder: " + options.exampleBuilder)
        commentLines.append("Features:")
        commentLines.extend(exampleBuilder.featureSet.toStrings())
        Example.writeExamples(examples, options.output + "/examples.txt", commentLines)
    return examples

def visualize(sentences, classifications, options):   
    print >> sys.stderr, "Making visualization"
    classificationsByExample = {}
    for classification in classifications:
        classificationsByExample[classification[0][0]] = classification
    visualizer = CorpusVisualizer(options.visualization, True)
    visualizer.featureSet = exampleBuilder.featureSet
    visualizer.classSet = exampleBuilder.classSet
    for i in range(len(sentences)):
        sentence = sentences[i]
        print >> sys.stderr, "\rProcessing sentence", sentence[0].getSentenceId(), "          ",
        prevAndNextId = [None,None]
        if i > 0:
            prevAndNextId[0] = sentences[i-1][0].getSentenceId()
        if i < len(sentences)-1:
            prevAndNextId[1] = sentences[i+1][0].getSentenceId()
        visualizer.makeSentencePage(sentence[0],sentence[1],classificationsByExample,prevAndNextId)
    visualizer.makeSentenceListPage()
    print >> sys.stderr

def classify(trainSet, testSet):
    pass

if __name__=="__main__":
    defaultAnalysisFilename = "/usr/share/biotext/ComplexPPI/BioInferForComplexPPI.xml"
    optparser = OptionParser(usage="%prog [options]\nCreate an html visualization for a corpus.")
    optparser.add_option("-i", "--input", default=defaultAnalysisFilename, dest="input", help="Corpus in analysis format", metavar="FILE")
    optparser.add_option("-o", "--output", default=None, dest="output", help="Output directory, useful for debugging")
    optparser.add_option("-c", "--classifier", default="SVMLightClassifier", dest="classifier", help="Classifier Class")
    optparser.add_option("-t", "--tokenization", default="split_gs", dest="tokenization", help="tokenization")
    optparser.add_option("-p", "--parse", default="split_gs", dest="parse", help="parse")
    optparser.add_option("-x", "--exampleBuilderParameters", default=None, dest="exampleBuilderParameters", help="Parameters for the example builder")
    optparser.add_option("-y", "--parameters", default=None, dest="parameters", help="Parameters for the classifier")
    optparser.add_option("-b", "--exampleBuilder", default="SimpleDependencyExampleBuilder", dest="exampleBuilder", help="Example Builder Class")
    optparser.add_option("-e", "--evaluator", default="Evaluation", dest="evaluator", help="Prediction evaluator class")
    optparser.add_option("-v", "--visualization", default=None, dest="visualization", help="Visualization output directory. NOTE: If the directory exists, it will be deleted!")
    (options, args) = optparser.parse_args()
    
    if options.output != None:
        if not os.path.exists(options.output):
            os.mkdir(options.output)
        if not os.path.exists(options.output+"/classifier"):
            os.mkdir(options.output+"/classifier")

    print >> sys.stderr, "Importing modules"
    exec "from ExampleBuilders." + options.exampleBuilder + " import " + options.exampleBuilder + " as ExampleBuilder"
    exec "from Classifiers." + options.classifier + " import " + options.classifier + " as Classifier"
    exec "from Evaluators." + options.evaluator + " import " + options.evaluator + " as Evaluation"
    
    # Load corpus and make sentence graphs
    corpusElements = loadCorpus(options.input, options.parse, options.tokenization)
    sentences = []
    for sentence in corpusElements.sentences:
        sentences.append( [sentence.sentenceGraph,None] )
    
    # Build examples
    exampleBuilder = ExampleBuilder(**splitParameters(options.exampleBuilderParameters))
    examples = buildExamples(exampleBuilder, sentences, options)
       
    # Make test and training sets
    print >> sys.stderr, "Dividing data into test and training sets"
    corpusDivision = Example.makeCorpusDivision(corpusElements)
    exampleSets = Example.divideExamples(examples, corpusDivision)
    
    # Create classifier object
    if options.output != None:
        classifier = Classifier(workDir = options.output + "/classifier")
    else:
        classifier = Classifier()
    classifier.featureSet = exampleBuilder.featureSet
    
    # Optimize
    optimizationSets = Example.divideExamples(exampleSets[0])
    evaluationArgs = {"classSet":exampleBuilder.classSet}
    if options.parameters != None:
        paramDict = splitParameters(options.parameters)
        bestResults = classifier.optimize([optimizationSets[0]], [optimizationSets[1]], paramDict, Evaluation, evaluationArgs)
    else:
        bestResults = classifier.optimize([optimizationSets[0]], [optimizationSets[1]], evaluationClass=Evaluation, evaluationArgs=evaluationArgs)

    # Save example sets
    if options.output != None:
        print >> sys.stderr, "Saving example sets to", options.output
        Example.writeExamples(exampleSets[0], options.output + "/examplesTest.txt")
        Example.writeExamples(exampleSets[1], options.output + "/examplesTrain.txt")
        Example.writeExamples(optimizationSets[0], options.output + "/examplesOptimizationTest.txt")
        Example.writeExamples(optimizationSets[1], options.output + "/examplesOptimizationTrain.txt")
    
    # Classify
    print >> sys.stderr, "Classifying test data"    
    print >> sys.stderr, "Parameters:", bestResults[2]
    classifier.train(exampleSets[0], bestResults[2])
    predictions = classifier.classify(exampleSets[1])
    
    # Calculate statistics
    evaluation = Evaluation(predictions, classSet=exampleBuilder.classSet)
    print >> sys.stderr, evaluation.toStringConcise()
    
    # Visualize
    if options.visualization != None:
        visualize(sentences, evaluation.classifications, options)