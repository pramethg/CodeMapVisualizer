import re
from typing import Dict, Any, List
from .base import BaseParser

class CppParser(BaseParser):
  
  def parse(self, filePath: str) -> Dict[str, Any]:
    with open(filePath, 'r', encoding='utf-8', errors='ignore') as sourceFile:
      fileContent = sourceFile.read()
      
    functions: List[str] = []
    classes: List[str] = []
    signatures: Dict[str, str] = {}
    
    # FIND CLASSES
    classPattern = r'\bclass\s+(\w+)'
    classMatches = re.finditer(classPattern, fileContent)
    for match in classMatches:
      className = match.group(1)
      classes.append(className)
      # Use the full match as signature (e.g. "class MyClass")
      signatures[className] = match.group(0).strip()
      
    # FIND FUNCTIONS (SIMPLE HEURISTIC)
    # Type Name(Args) {
    # limit to common types to avoid false positives
    funcPattern = r'\b(void|int|float|double|bool|string|auto)\s+(\w+)\s*\([^)]*\)\s*\{'
    funcMatches = re.finditer(funcPattern, fileContent)
    for match in funcMatches:
      funcName = match.group(2)
      functions.append(funcName)
      # Signature: full match minus keys
      fullMatch = match.group(0)
      # Remove trailing { if present
      signatures[funcName] = fullMatch.replace('{', '').strip()

    return {
      "type": "cpp",
      "functions": functions,
      "classes": classes,
      "signatures": signatures
    }
