import sys, os
import shutil
import subprocess
import tempfile
import codecs
from ProcessUtils import *

stanfordParserDir = "/home/jari/biotext/tools/stanford-parser-2008-10-26"

def convert(input, output=None):
    global stanfordParserDir

    workdir = tempfile.mkdtemp()
    if output == None:
        output = os.path.join(workdir, "stanford-output.txt")
    
    input = os.path.abspath(input)
    numCorpusSentences = 0
    inputFile = codecs.open(input, "rt", "utf-8")
    for line in inputFile:
        numCorpusSentences += 1
    inputFile.close()
    cwd = os.getcwd()
    os.chdir(stanfordParserDir)
    args = ["java", "-mx150m", "-cp", "stanford-parser.jar", "edu.stanford.nlp.trees.EnglishGrammaticalStructure", "-CCprocessed", "-treeFile", input] 
    #subprocess.call(args,
    process = subprocess.Popen(args, 
        stdout=codecs.open(output, "wt", "utf-8"))
    waitForProcess(process, numCorpusSentences, True, output, "StanfordParser", "Stanford Conversion")
    os.chdir(cwd)

    lines = None    
    if output == None:
        outFile = codecs.open(output, "rt", "utf-8")
        lines = outFile.readlines()
        outFile.close()
    
    shutil.rmtree(workdir)
    return lines