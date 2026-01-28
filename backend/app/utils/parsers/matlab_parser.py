import re
from typing import Dict, Any, List, Set
from .base import BaseParser

class MatlabParser(BaseParser):
  """
  MATLAB parser that handles classdef files with:
  - Multiple methods/properties blocks
  - Getter/setter functions (get.propName, set.propName)
  - Nested control flow (if/for/while/switch/try)
  - Full function body extraction for definitions
  - Dependency analysis (method calls and property usage)
  """
  
  def parse(self, filePath: str) -> Dict[str, Any]:
    with open(filePath, 'r', encoding='utf-8') as sourceFile:
      fileContent = sourceFile.read()
    
    functions: List[str] = []
    signatures: Dict[str, str] = {}
    definitions: Dict[str, str] = {}  # Full source code for each function
    locations: Dict[str, int] = {}    # Line number for each symbol
    classDetails: List[Dict[str, Any]] = []

    lines = fileContent.splitlines()
    
    currentClass = None
    inProperties = False
    
    # Track class indentation to know when class ends
    classIndent = None
    propsIndent = None
    
    # For function body extraction
    funcStartLine = None
    funcName = None
    funcNestLevel = 0
    
    # Collect all method and property names for dependency analysis later
    allMethodNames: Set[str] = set()
    allPropertyNames: Set[str] = set()
    
    for i, rawLine in enumerate(lines):
        strippedLine = rawLine.lstrip()
        indent = len(rawLine) - len(strippedLine)
        
        if not strippedLine or strippedLine.startswith('%'):
            continue
        
        codeLine = strippedLine.split('%')[0].strip()
        if not codeLine:
            continue
        
        # Track nested blocks for function body extraction
        if funcStartLine is not None:
            if re.match(r'^(if|for|while|switch|try|parfor)\b', codeLine):
                funcNestLevel += 1
            elif codeLine == 'end':
                if funcNestLevel > 0:
                    funcNestLevel -= 1
                else:
                    funcEndLine = i
                    funcBody = '\n'.join(lines[funcStartLine:funcEndLine + 1])
                    if funcName:
                        definitions[funcName] = funcBody
                    funcStartLine = None
                    funcName = None
                    funcNestLevel = 0
        
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
            locations[className] = i + 1
            classIndent = indent
            continue
        
        # 2. CLASS END
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
                locations[fName] = i + 1
                funcStartLine = i
                funcName = fName
                funcNestLevel = 0
                allMethodNames.add(fName)
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
            inProperties = False
            
            funcStartLine = i
            funcName = fullName
            funcNestLevel = 0
            
            # Track method name for dependency analysis
            baseName = fullName.split('.')[-1] if '.' in fullName else fullName
            allMethodNames.add(baseName)
            
            # Line number
            locations[fullName] = i + 1
            # Also store short name if needed, though qualified is safer
            if '.' not in fullName:
                locations[fullName] = i + 1
            else:
                # Store simple name too? Maybe risky for methods
                pass

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
                        locations[f"{currentClass['name']}.{pName}"] = i + 1
                        locations[pName] = i + 1
                        allPropertyNames.add(pName)
        
    # === DEPENDENCY ANALYSIS ===
    # Now analyze each method body to find calls and property usage
    dependencies: Dict[str, Dict[str, List[str]]] = {}
    
    for methodName, methodBody in definitions.items():
      deps = self._extract_dependencies(methodBody, allMethodNames, allPropertyNames, methodName)
      if deps['calls'] or deps['uses_properties']:
        dependencies[methodName] = deps
    
    return {
      "type": "matlab",
      "functions": functions,
      "classes": [],
      "classDetails": classDetails,
      "signatures": signatures,
      "definitions": definitions,
      "dependencies": dependencies,
      "locations": locations
    }

  def _extract_dependencies(
    self, 
    methodBody: str, 
    allMethods: Set[str], 
    allProperties: Set[str],
    currentMethod: str
  ) -> Dict[str, List[str]]:
    """
    Extract method calls and property usage from a method body.
    Looks for patterns like:
    - obj.methodName( or self.methodName( or this.methodName(
    - obj.propertyName or self.propertyName (not followed by '(')
    """
    calls: Set[str] = set()
    uses_properties: Set[str] = set()
    
    # Pattern for method calls: obj.methodName(
    # Match self., obj., this., or just direct calls
    call_pattern = r'(?:self|obj|this)\s*\.\s*(\w+)\s*\('
    for match in re.finditer(call_pattern, methodBody, re.IGNORECASE):
      called = match.group(1)
      # Only add if it's a known method and not self-reference
      if called in allMethods and called != currentMethod:
        calls.add(called)
    
    # Also match direct function calls (without obj.)
    direct_call_pattern = r'(?<![.\w])(\w+)\s*\('
    for match in re.finditer(direct_call_pattern, methodBody):
      called = match.group(1)
      # Skip common MATLAB built-ins and current method
      if called in allMethods and called != currentMethod:
        if called.lower() not in ['if', 'for', 'while', 'switch', 'try', 'catch', 'function', 'end']:
          calls.add(called)
    
    # Pattern for property access: obj.propertyName (not followed by '(')
    prop_pattern = r'(?:self|obj|this)\s*\.\s*(\w+)(?!\s*\()'
    for match in re.finditer(prop_pattern, methodBody, re.IGNORECASE):
      prop = match.group(1)
      if prop in allProperties:
        uses_properties.add(prop)
    
    return {
      "calls": sorted(list(calls)),
      "uses_properties": sorted(list(uses_properties))
    }
