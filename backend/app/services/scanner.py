import os
import json
from typing import Dict, Any, List, Optional
from app.utils.parsers import getParser

class ScannerService:
  
  def __init__(self):
    pass # No static assets path in init

  def _get_storage_path(self, target_path: str, root_path: Optional[str] = None) -> str:
    """
    Determines the storage path for the JSON metadata file.
    Strategy: 
    1. If root_path is provided: ALWAYS use {root_path}/assets/.visualizer/
    2. Fallback (no root_path): {parent_of_target}/assets/.visualizer/
    
    Filename: Collision-resistant based on relative path if root exists, else basename.
    """
    # Normalize paths to handle trailing slashes and different formats
    target_path = os.path.normpath(os.path.abspath(target_path))
    
    if root_path:
      root_path = os.path.normpath(os.path.abspath(root_path))
      # ALWAYS use root_path for storage when provided
      storage_dir = os.path.join(root_path, "assets", ".visualizer")
      
      # Try to get relative path for collision-resistant filename
      try:
        rel_path = os.path.relpath(target_path, root_path)
        # If rel_path goes outside root (starts with ..), use absolute path based name
        if rel_path.startswith(".."):
          safe_name = target_path.replace(os.sep, "_").replace(".", "_").replace(":", "_")
        else:
          safe_name = rel_path.replace(os.sep, "_").replace(".", "_")
      except ValueError:
        # On Windows, relpath can fail if paths are on different drives
        safe_name = os.path.basename(target_path).replace(".", "_")
      
      filename = f"meta_{safe_name}.json"
    else:
      # FALLBACK (Single file mode, no root context)
      storage_dir = os.path.join(os.path.dirname(target_path), "assets", ".visualizer")
      filename = f"meta_{os.path.basename(target_path).replace('.', '_')}.json"

    if not os.path.exists(storage_dir):
      os.makedirs(storage_dir, exist_ok=True)
    
    output_path = os.path.join(storage_dir, filename)
    print(f"[DEBUG] _get_storage_path: storage_dir={storage_dir}, filename={filename}")
    return output_path

  def scanFolder(self, folderPath: str) -> Dict[str, Any]:
    # For folder scan, we usually assume folderPath IS the root
    # But this method builds hierarchy. It doesn't write per-file metadata here necessarily?
    # Actually, the original wrote "jsonFolderFOO.json". 
    # We should probably store this hierarchy cache in the same assets dir?
    
    storage_path = self._get_storage_path(folderPath, folderPath)
    # Correct filename for folder structure cache?
    # _get_storage_path would make "meta_.._.._.json" which is weird.
    
    # Custom handling for folder cache:
    storage_dir = os.path.join(folderPath, "assets", ".visualizer")
    if not os.path.exists(storage_dir):
       os.makedirs(storage_dir, exist_ok=True)
    
    outputFileName = f"folder_structure.json"
    outputPath = os.path.join(storage_dir, outputFileName)
    
    structure = self._buildHierarchy(folderPath)
    
    with open(outputPath, 'w', encoding='utf-8') as outFile:
      json.dump(structure, outFile, indent=2)
      
    return structure

  def scanFile(self, filePath: str, rootPath: Optional[str] = None) -> Dict[str, Any]:
    outputPath = self._get_storage_path(filePath, rootPath)
    
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

  def saveComments(self, filePath: str, comments: List[Dict[str, Any]], rootPath: Optional[str] = None) -> Dict[str, Any]:
    outputPath = self._get_storage_path(filePath, rootPath)
    
    # If file doesn't exist, we might need to create it (if only saving comments)
    # But usually we expect scan to happen first.
    # However, to be robust, we can just save valid JSON if not exists.
    
    data = {}
    if os.path.exists(outputPath):
      try:
        with open(outputPath, 'r', encoding='utf-8') as inFile:
          data = json.load(inFile)
      except Exception:
        pass
        
    # OVERWRITE COMMENTS
    data["comments"] = comments
    
    with open(outputPath, 'w', encoding='utf-8') as outFile:
      json.dump(data, outFile, indent=2)
      
    return data

  def addComment(self, filePath: str, nodeLabel: str, commentText: str, rootPath: Optional[str] = None) -> Dict[str, Any]:
    outputPath = self._get_storage_path(filePath, rootPath)
    
    data = {}
    if os.path.exists(outputPath):
      try:
        with open(outputPath, 'r', encoding='utf-8') as inFile:
          data = json.load(inFile)
      except Exception:
        pass
        
    if "comments" not in data:
      data["comments"] = []
    
    data["comments"].append({
      "nodeLabel": nodeLabel,
      "text": commentText,
      "title": "", 
      "timestamp": 0
    })
    
    with open(outputPath, 'w', encoding='utf-8') as outFile:
      json.dump(data, outFile, indent=2)
      
    return data


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
