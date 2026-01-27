import os
import tkinter as tk
from tkinter import filedialog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.scanner import ScannerService

app = FastAPI(title="CodeMapVisualizer Backend")

# CORS CONFIGURATION
originsList = [
  "http://localhost:3000",
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=originsList,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# INITIALIZE SERVICES
assetsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
if not os.path.exists(assetsPath):
  os.makedirs(assetsPath)

scannerService = ScannerService(assetsPath)

class ScanRequest(BaseModel):
  path: str

class CommentRequest(BaseModel):
  path: str
  nodeLabel: str
  text: str

@app.get("/")
async def rootHandler():
  return {"message": "Welcome to CodeMapVisualizer Backend"}

@app.post("/api/scan-folder")
async def scanFolderHandler(request: ScanRequest):
  if not os.path.exists(request.path):
    raise HTTPException(status_code=404, detail="Path not found")
  
  try:
    result = scannerService.scanFolder(request.path)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan-file")
async def scanFileHandler(request: ScanRequest):
  if not os.path.exists(request.path):
    raise HTTPException(status_code=404, detail="File not found")
    
  try:
    result = scannerService.scanFile(request.path)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-comment")
async def addCommentHandler(request: CommentRequest):
  # Legacy endpoint
  try:
    result = scannerService.addComment(request.path, request.nodeLabel, request.text)
    if "error" in result:
      raise HTTPException(status_code=400, detail=result["error"])
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

class SaveCommentsRequest(BaseModel):
  path: str
  comments: list

@app.post("/api/save-comments")
async def saveCommentsHandler(request: SaveCommentsRequest):
  try:
    result = scannerService.saveComments(request.path, request.comments)
    if "error" in result:
      raise HTTPException(status_code=400, detail=result["error"])
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pick-folder")
async def pickFolderHandler():
  import sys
  import subprocess
  
  if sys.platform == 'darwin':
    try:
      cmd = [
          "osascript",
          "-e",
          'POSIX path of (choose folder with prompt "Select Project Folder")'
      ]
      result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
      if not result:
           return {"path": ""}
      return {"path": result}
    except subprocess.CalledProcessError:
      return {"path": ""}
    except Exception as e:
      print(f"Mac Picker Error: {e}")
      raise HTTPException(status_code=500, detail="Failed to open macOS picker")
      
  else:
    # Linux / Windows fallback to tkinter
    # Note: Requires DISPLAY environment variable on Linux to be set (X11 forwarding)
    try:
      # We check availability by trying to import and initialize a root
      cmd = [
          sys.executable,
          "-c",
          "import tkinter as tk; from tkinter import filedialog; root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); print(filedialog.askdirectory())"
      ]
      result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
      if not result:
           return {"path": ""}
      return {"path": result}
    except Exception as e:
      print(f"Tkinter Picker Error: {e}")
      # If it fails (e.g. headless linux), we return a specific message or just empty
      # Returning empty path with console log is safer than 500
      print("Folder picker not supported or display not available on this OS.")
      return {"path": "", "message": "Folder picker requires a desktop environment or X11 forwarding."}
