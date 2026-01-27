import re
from typing import Dict, Any, List
from .base import BaseParser

class MatlabParser(BaseParser):
  """
  MATLAB parser that handles classdef files with:
  - Multiple methods/properties blocks
  - Getter/setter functions (get.propName, set.propName)
  - Nested control flow (if/for/while/switch/try)
  """
  
  def parse(self, filePath: str) -> Dict[str, Any]:
    with open(filePath, 'r', encoding='utf-8') as sourceFile:
      fileContent = sourceFile.read()
    
    functions: List[str] = []
    signatures: Dict[str, str] = {}
    classDetails: List[Dict[str, Any]] = []

    lines = fileContent.splitlines()
    
    currentClass = None
    inProperties = False
    
    # Track class indentation to know when class ends
    classIndent = None
    propsIndent = None
    
    for i, rawLine in enumerate(lines):
        # Calculate indentation
        strippedLine = rawLine.lstrip()
        indent = len(rawLine) - len(strippedLine)
        
        # Skip empty lines and comments
        if not strippedLine or strippedLine.startswith('%'):
            continue
        
        # Remove inline comments
        codeLine = strippedLine.split('%')[0].strip()
        if not codeLine:
            continue
        
        # 1. CLASS DEF
        classMatch = re.search(r'^classdef\s*(?:\([^)]*\))?\s*(\w+)', codeLine)
        if classMatch:
            className = classMatch.group(1)
            currentClass = {
                "name": className,
                "properties": [],
                "methods": []
            }
            classDetails.append(currentClass)
            signatures[className] = codeLine
            classIndent = indent
            continue
        
        # 2. CLASS END - end at same or lower indentation as classdef
        if currentClass and codeLine == 'end' and indent <= classIndent:
            currentClass = None
            classIndent = None
            inProperties = False
            propsIndent = None
            continue
            
        # If not in a class, check for standalone functions
        if not currentClass:
            funcMatch = re.search(
                r'^function\s+(?:(?:\[[^\]]*\]|\w+)\s*=\s*)?([a-zA-Z_][\w\.]*)',
                codeLine
            )
            if funcMatch:
                fName = funcMatch.group(1)
                functions.append(fName)
                signatures[fName] = codeLine
            continue
        
        # Inside a class from here on
            
        # 3. PROPERTIES BLOCK START
        if re.match(r'^properties(\s*$|\s*\()', codeLine):
            inProperties = True
            propsIndent = indent
            continue
        
        # 4. PROPERTIES END
        if inProperties and codeLine == 'end' and indent <= propsIndent:
            inProperties = False
            propsIndent = None
            continue
        
        # 5. METHODS/EVENTS/ENUMERATION BLOCK START
        if re.match(r'^(methods|events|enumeration)(\s*$|\s*\()', codeLine):
            inProperties = False
            propsIndent = None
            continue
        
        # 6. FUNCTION DEFINITIONS (inside class)
        funcMatch = re.search(
            r'^function\s+(?:(?:\[[^\]]*\]|\w+)\s*=\s*)?([a-zA-Z_][\w\.]*)',
            codeLine
        )
        if funcMatch:
            fullName = funcMatch.group(1)
            inProperties = False  # Can't be in properties if we see a function
            
            if '.' in fullName:
                parts = fullName.split('.')
                prefix = parts[0]
                propName = parts[1] if len(parts) > 1 else parts[0]
                
                currentClass['methods'].append({
                    "name": fullName,
                    "signature": codeLine,
                    "attributes": [prefix],
                    "property": propName
                })
                signatures[fullName] = codeLine
            else:
                currentClass['methods'].append({
                    "name": fullName,
                    "signature": codeLine,
                    "attributes": []
                })
                signatures[fullName] = codeLine
            continue
        
        # 7. PROPERTY PARSING (inside properties block)
        if inProperties:
            pNameMatch = re.match(r'^([a-zA-Z_]\w*)', codeLine)
            if pNameMatch:
                pName = pNameMatch.group(1)
                if pName.lower() not in ['end', 'properties', 'methods', 'events', 'enumeration', 'classdef', 'function']:
                    existing = [p['name'] for p in currentClass['properties']]
                    if pName not in existing:
                        currentClass['properties'].append({
                            "name": pName,
                            "attributes": []
                        })
        
    return {
      "type": "matlab",
      "functions": functions,
      "classes": [],
      "classDetails": classDetails,
      "signatures": signatures
    }
