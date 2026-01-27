import os
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
# assetsPath removed from init, managed dynamically by service
scannerService = ScannerService()

class ScanRequest(BaseModel):
  path: str
  rootPath: str | None = None

class CommentRequest(BaseModel):
  path: str
  nodeLabel: str
  text: str
  rootPath: str | None = None

@app.get("/")
async def rootHandler():
  return {"message": "Welcome to CodeMapVisualizer Backend"}

@app.post("/api/scan-folder")
async def scanFolderHandler(request: ScanRequest):
  if not os.path.exists(request.path):
    raise HTTPException(status_code=404, detail="Path not found")
  
  try:
    # Scan folder structure
    result = scannerService.scanFolder(request.path)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan-file")
async def scanFileHandler(request: ScanRequest):
  print(f"[DEBUG] scan-file: path={request.path}, rootPath={request.rootPath}")
  
  if not os.path.exists(request.path):
    raise HTTPException(status_code=404, detail="File not found")
    
  try:
    result = scannerService.scanFile(request.path, request.rootPath)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-comment")
async def addCommentHandler(request: CommentRequest):
  # Legacy endpoint
  try:
    result = scannerService.addComment(request.path, request.nodeLabel, request.text, request.rootPath)
    if "error" in result:
      raise HTTPException(status_code=400, detail=result["error"])
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

class SaveCommentsRequest(BaseModel):
  path: str
  comments: list
  rootPath: str | None = None

@app.post("/api/save-comments")
async def saveCommentsHandler(request: SaveCommentsRequest):
  try:
    result = scannerService.saveComments(request.path, request.comments, request.rootPath)
    if "error" in result:
      raise HTTPException(status_code=400, detail=result["error"])
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pick-folder")
async def pickFolderHandler():
  import sys
  import subprocess
  import shutil
  
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
      
  elif sys.platform.startswith('linux'):
    # Try zenity (GNOME/GTK) first, then kdialog (KDE)
    try:
      if shutil.which("zenity"):
        cmd = ["zenity", "--file-selection", "--directory", "--title=Select Project Folder"]
        result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
        if result:
          return {"path": result}
        return {"path": ""}
      elif shutil.which("kdialog"):
        cmd = ["kdialog", "--getexistingdirectory", os.path.expanduser("~"), "--title", "Select Project Folder"]
        result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
        if result:
          return {"path": result}
        return {"path": ""}
      else:
        # No GUI picker available
        print("No folder picker available (zenity/kdialog not found)")
        return {"path": "", "message": "No folder picker available. Please enter the path manually in the input field."}
    except subprocess.CalledProcessError:
      # User cancelled the dialog
      return {"path": ""}
    except Exception as e:
      print(f"Linux Picker Error: {e}")
      return {"path": "", "message": "Folder picker failed. Please enter the path manually."}
  
  else:
    # Windows or other - return message to use manual input
    print("Folder picker not supported on this platform without tkinter")
    return {"path": "", "message": "Folder picker not available. Please enter the path manually."}

