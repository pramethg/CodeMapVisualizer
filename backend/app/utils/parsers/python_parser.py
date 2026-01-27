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
    signatures: Dict[str, str] = {}
    definitions: Dict[str, str] = {}  # Full source code for each function
    classDetails: List[Dict[str, Any]] = []

    # TRAVERSE TOP-LEVEL NODES
    for node in tree.body:
      if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        funcName = node.name
        functions.append(funcName)
        signatures[funcName] = self._get_signature(node)
        definitions[funcName] = self._get_source(fileContent, node)
        
      elif isinstance(node, ast.ClassDef):
        classes.append(node.name)
        
        classInfo = {
          "name": node.name,
          "properties": [],
          "methods": []
        }
        
        # GET METHODS AND PROPERTIES INSIDE CLASS
        for item in node.body:
          if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
            methodName = item.name
            qualifiedName = f"{node.name}.{methodName}"
            
            classInfo["methods"].append({
              "name": methodName,
              "attributes": self._get_decorators(item),
              "signature": self._get_signature(item)
            })
            
            signatures[methodName] = self._get_signature(item)
            definitions[methodName] = self._get_source(fileContent, item)
            definitions[qualifiedName] = self._get_source(fileContent, item)
          
          elif isinstance(item, ast.Assign):
            # Class-level attributes
            for target in item.targets:
              if isinstance(target, ast.Name):
                classInfo["properties"].append({
                  "name": target.id,
                  "attributes": []
                })
        
        classDetails.append(classInfo)

    return {
      "type": "python",
      "functions": functions,
      "classes": classes,
      "classDetails": classDetails,
      "signatures": signatures,
      "definitions": definitions
    }
  
  def _get_signature(self, node: ast.FunctionDef) -> str:
    """Extract function signature as a string"""
    args = []
    
    # Handle positional args
    for arg in node.args.args:
      argStr = arg.arg
      if arg.annotation:
        argStr += f": {ast.unparse(arg.annotation)}"
      args.append(argStr)
    
    # Handle *args
    if node.args.vararg:
      args.append(f"*{node.args.vararg.arg}")
    
    # Handle **kwargs
    if node.args.kwarg:
      args.append(f"**{node.args.kwarg.arg}")
    
    signature = f"def {node.name}({', '.join(args)})"
    
    # Return type annotation
    if node.returns:
      signature += f" -> {ast.unparse(node.returns)}"
    
    return signature
  
  def _get_decorators(self, node: ast.FunctionDef) -> List[str]:
    """Extract decorator names"""
    decorators = []
    for decorator in node.decorator_list:
      if isinstance(decorator, ast.Name):
        decorators.append(decorator.id)
      elif isinstance(decorator, ast.Attribute):
        decorators.append(decorator.attr)
      elif isinstance(decorator, ast.Call):
        if isinstance(decorator.func, ast.Name):
          decorators.append(decorator.func.id)
        elif isinstance(decorator.func, ast.Attribute):
          decorators.append(decorator.func.attr)
    return decorators
  
  def _get_source(self, source: str, node: ast.AST) -> str:
    """Extract source code for a node"""
    try:
      return ast.get_source_segment(source, node) or ""
    except Exception:
      # Fallback for older Python versions
      lines = source.splitlines()
      if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
        start = node.lineno - 1
        end = node.end_lineno
        return '\n'.join(lines[start:end])
      return ""
