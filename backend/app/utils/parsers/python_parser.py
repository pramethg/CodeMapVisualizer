import ast
from typing import Dict, Any, List
from .base import BaseParser

class PythonParser(BaseParser):
  
  def parse(self, filePath: str) -> Dict[str, Any]:
    with open(filePath, 'r', encoding='utf-8') as sourceFile:
      fileContent = sourceFile.read()
    
    tree = ast.parse(fileContent)
    functions: List[str] = []
    classes: List[str] = []

    # TRAVERSE AST
    for node in ast.walk(tree):
      if isinstance(node, ast.FunctionDef):
        functions.append(node.name)
      elif isinstance(node, ast.ClassDef):
        classes.append(node.name)
        # GET METHODS INSIDE CLASS
        for item in node.body:
          if isinstance(item, ast.FunctionDef):
            functions.append(f"{node.name}.{item.name}")

    return {
      "type": "python",
      "functions": functions,
      "classes": classes
    }
