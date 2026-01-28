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
    2. If not provided: auto-detect project root by looking for .git, existing assets, etc
    3. Ultimate fallback: use grandparent directory (2 levels up from file)
    
    Filename: Collision-resistant based on relative path if root exists, else basename.
    """
    # Normalize paths to handle trailing slashes and different formats
    target_path = os.path.normpath(os.path.abspath(target_path))
    
    # If no root_path provided, try to auto-detect
    if not root_path:
      root_path = self._detect_project_root(target_path)
    
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
      # Ultimate fallback - shouldn't normally happen
      storage_dir = os.path.join(os.path.dirname(target_path), "assets", ".visualizer")
      filename = f"meta_{os.path.basename(target_path).replace('.', '_')}.json"

    if not os.path.exists(storage_dir):
      os.makedirs(storage_dir, exist_ok=True)
    
    print(f"[DEBUG] _get_storage_path: storage_dir={storage_dir}, filename={filename}")
    return os.path.join(storage_dir, filename)

  def _detect_project_root(self, file_path: str) -> Optional[str]:
    """
    Auto-detect project root by traversing up the directory tree.
    Looks for: .git folder, existing assets/.visualizer, or stops 3 levels up.
    """
    current = os.path.dirname(os.path.abspath(file_path))
    levels = 0
    max_levels = 5  # Don't go more than 5 levels up
    
    while current and levels < max_levels:
      # Check for .git directory (common project root indicator)
      if os.path.isdir(os.path.join(current, ".git")):
        return current
      
      # Check for existing assets/.visualizer (we've used this folder before)
      if os.path.isdir(os.path.join(current, "assets", ".visualizer")):
        return current
      
      # Move up one level
      parent = os.path.dirname(current)
      if parent == current:
        break  # Reached filesystem root
      current = parent
      levels += 1
    
    # Fallback: return the directory 2 levels up from the file
    current = os.path.dirname(os.path.abspath(file_path))
    for _ in range(2):
      parent = os.path.dirname(current)
      if parent == current:
        break
      current = parent
    
    return current

  def _write_json_atomic(self, path: str, data: Any):
    """
    Writes JSON data to a file atomically.
    Writes to a temp file first, then renames it to the target path.
    This prevents race conditions where the file is truncated/empty during write.
    """
    import tempfile
    dir_name = os.path.dirname(path)
    # Create temp file in same dir to ensure atomic move works across filesystems
    # We use a fixed suffix so we can easily ignore/clean them if needed, 
    # but mkstemp is safer for uniqueness.
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp', text=True)
    
    try:
      with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
      # Atomic replace
      os.replace(tmp_path, path)
    except Exception as e:
      # Clean up if something failed
      if os.path.exists(tmp_path):
        os.unlink(tmp_path)
      raise e

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
    
    self._write_json_atomic(outputPath, structure)
      
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

    self._write_json_atomic(outputPath, parsedData)
      
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
    
    self._write_json_atomic(outputPath, data)
      
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
    
    self._write_json_atomic(outputPath, data)
      
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
