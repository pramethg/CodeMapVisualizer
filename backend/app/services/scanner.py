import os
import json
from typing import Dict, Any, List
from app.utils.parsers import getParser

class ScannerService:
  
  def __init__(self, assetsPath: str):
    self.assetsPath = assetsPath
    
  def scanFolder(self, folderPath: str) -> Dict[str, Any]:
    folderName = os.path.basename(os.path.normpath(folderPath))
    outputFileName = f"jsonFolder{folderName.upper()}.json"
    outputPath = os.path.join(self.assetsPath, outputFileName)
    
    structure = self._buildHierarchy(folderPath)
    
    with open(outputPath, 'w', encoding='utf-8') as outFile:
      json.dump(structure, outFile, indent=2)
      
    return structure

  def scanFile(self, filePath: str) -> Dict[str, Any]:
    fileName = os.path.basename(filePath)
    fileNameNoExt = os.path.splitext(fileName)[0]
    outputFileName = f"jsonScript{fileNameNoExt.upper()}.json"
    outputPath = os.path.join(self.assetsPath, outputFileName)
    
    parser = getParser(filePath)
    if not parser:
      return {"error": "Unsupported file type"}
      
    parsedData = parser.parse(filePath)
    
    # PRESERVE COMMENTS IF FILE EXISTS
    if os.path.exists(outputPath):
      try:
        with open(outputPath, 'r', encoding='utf-8') as inFile:
          existingData = json.load(inFile)
          if "comments" in existingData:
            parsedData["comments"] = existingData["comments"]
      except Exception:
        pass # IGNORE IF READ FAILS
    
    # INITIALIZE COMMENTS LIST IF NOT PRESENT
    if "comments" not in parsedData:
      parsedData["comments"] = []

    with open(outputPath, 'w', encoding='utf-8') as outFile:
      json.dump(parsedData, outFile, indent=2)
      
    return parsedData

  def saveComments(self, filePath: str, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    fileName = os.path.basename(filePath)
    fileNameNoExt = os.path.splitext(fileName)[0]
    outputFileName = f"jsonScript{fileNameNoExt.upper()}.json"
    outputPath = os.path.join(self.assetsPath, outputFileName)
    
    if not os.path.exists(outputPath):
      return {"error": "Scan file first"}
      
    try:
      with open(outputPath, 'r', encoding='utf-8') as inFile:
        data = json.load(inFile)
        
      # OVERWRITE COMMENTS
      data["comments"] = comments
      
      with open(outputPath, 'w', encoding='utf-8') as outFile:
        json.dump(data, outFile, indent=2)
        
      return data
    except Exception as e:
      return {"error": str(e)}

  def addComment(self, filePath: str, nodeLabel: str, commentText: str) -> Dict[str, Any]:
    # Legacy/Append method - kept for reference or alternative use
    fileName = os.path.basename(filePath)
    fileNameNoExt = os.path.splitext(fileName)[0]
    outputFileName = f"jsonScript{fileNameNoExt.upper()}.json"
    outputPath = os.path.join(self.assetsPath, outputFileName)
    
    if not os.path.exists(outputPath):
      return {"error": "Scan file first"}
      
    try:
      with open(outputPath, 'r', encoding='utf-8') as inFile:
        data = json.load(inFile)
        
      if "comments" not in data:
        data["comments"] = []
      
      data["comments"].append({
        "nodeLabel": nodeLabel,
        "text": commentText,
        "title": "", # Default empty title for legacy add
        "timestamp": 0
      })
      
      with open(outputPath, 'w', encoding='utf-8') as outFile:
        json.dump(data, outFile, indent=2)
        
      return data
    except Exception as e:
      return {"error": str(e)}

  def _buildHierarchy(self, path: str) -> Dict[str, Any]:
    name = os.path.basename(path)
    if os.path.isdir(path):
      children = []
      try:
        # IGNORE HIDDEN FILES AND COMMON IGNORES
        ignored = {'.git', 'node_modules', '__pycache__', '.DS_Store', 'venv', '.next'}
        
        # Sort alphabetically (case-insensitive)
        items = sorted(os.listdir(path), key=lambda s: s.lower())
        
        for item in items:
          if item in ignored or item.startswith('.'):
            continue
          itemPath = os.path.join(path, item)
          children.append(self._buildHierarchy(itemPath))
      except PermissionError:
        pass
        
      return {
        "name": name,
        "type": "folder",
        "path": path,
        "children": children
      }
    else:
      return {
        "name": name,
        "type": "file",
        "path": path
      }
