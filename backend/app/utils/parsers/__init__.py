from .python_parser import PythonParser
from .matlab_parser import MatlabParser
from .cpp_parser import CppParser

def getParser(filePath: str):
  if filePath.endswith('.py'):
    return PythonParser()
  elif filePath.endswith('.m'):
    return MatlabParser()
  elif filePath.endswith('.cpp') or filePath.endswith('.h'):
    return CppParser()
  return None
