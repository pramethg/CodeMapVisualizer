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
    locations: Dict[str, int] = {}    # Line number for each symbol
    classDetails: List[Dict[str, Any]] = []

    # TRAVERSE TOP-LEVEL NODES
    lines = fileContent.splitlines()
    
    for node in tree.body:
      if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        funcName = node.name
        functions.append(funcName)
        signatures[funcName] = self._get_signature(node)
        definitions[funcName] = self._get_source(fileContent, node)
        # Use accurate definition line
        locations[funcName] = self._find_def_lineno(lines, node)
        
      elif isinstance(node, ast.ClassDef):
        classes.append(node.name)
        # Use accurate definition line
        locations[node.name] = self._find_def_lineno(lines, node)
        
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
            
            # Use accurate definition line
            defLine = self._find_def_lineno(lines, item)
            locations[qualifiedName] = defLine
            # Also invoke short name if unique? Maybe risky. But qualified is safer.
            locations[methodName] = defLine 
          
          elif isinstance(item, ast.Assign):
            # Class-level attributes
            for target in item.targets:
              if isinstance(target, ast.Name):
                classInfo["properties"].append({
                  "name": target.id,
                  "attributes": []
                })
                locations[f"{node.name}.{target.id}"] = item.lineno
                locations[target.id] = item.lineno # Short name convenient
        
        classDetails.append(classInfo)

    return {
      "type": "python",
      "functions": functions,
      "classes": classes,
      "classDetails": classDetails,
      "signatures": signatures,
      "definitions": definitions,
      "locations": locations
    }

  def _find_def_lineno(self, lines: List[str], node: ast.AST) -> int:
    """
    Find the line number of the 'def' or 'class' keyword, skipping decorators.
    """
    if not hasattr(node, 'lineno'):
        return 0
        
    startLine = node.lineno - 1 # 0-indexed
    # If no decorators, the ast.lineno is usually the definition line
    if hasattr(node, 'decorator_list') and not node.decorator_list:
        return node.lineno
        
    # Scan forward looking for 'def ' or 'class '
    import re
    # We scan from startLine down to end_lineno (if available) or arbitrary limit
    limit = getattr(node, 'end_lineno', startLine + 50)
    
    for i in range(startLine, limit):
        if i >= len(lines):
            break
        line = lines[i]
        # Match 'def <name>' or 'async def <name>' or 'class <name>'
        # We need to be careful about indentation
        if re.search(r'^\s*(async\s+)?(def|class)\s+', line):
            return i + 1
            
    return node.lineno # Fallback
  
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
