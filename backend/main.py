import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.scanner import ScannerService
from app.services.linear import LinearService

app = FastAPI(title="CodeMapVisualizer Backend")

# CORS CONFIGURATION
# CORS CONFIGURATION
app.add_middleware(
  CORSMiddleware,
  allow_origin_regex="https?://.*",
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# INITIALIZE SERVICES
# assetsPath removed from init, managed dynamically by service
scannerService = ScannerService()
linearService = LinearService()

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

class ListDirectoryRequest(BaseModel):
  path: str | None = None

@app.post("/api/list-directory")
async def listDirectoryHandler(request: ListDirectoryRequest):
  import os
  
  target_path = request.path
  if not target_path or target_path.strip() == "":
    target_path = os.path.expanduser("~")
  
  if not os.path.exists(target_path):
     raise HTTPException(status_code=404, detail="Path not found")
  
  if not os.path.isdir(target_path):
     target_path = os.path.dirname(target_path)

  try:
    items = os.scandir(target_path)
    folders = []
    files = []
    
    for item in items:
      if item.name.startswith('.'):
        continue
      if item.is_dir():
        folders.append(item.name)
      else:
        files.append(item.name)
        
    folders.sort()
    files.sort()
    
    parent = os.path.dirname(target_path)
    
    return {
      "path": target_path,
      "parent": parent,
      "folders": folders,
      "files": files
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))



class LinearCheckRequest(BaseModel):
  rootPath: str

class LinearIssueRequest(BaseModel):
  rootPath: str
  title: str
  description: str
  filePath: str
  lineNumber: int
  tag: str

@app.post("/api/linear/check-connection")
async def checkLinearConnectionHandler(request: LinearCheckRequest):
  try:
    result = linearService.check_connection(request.rootPath)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linear/create-issue")
async def createLinearIssueHandler(request: LinearIssueRequest):
  try:
    result = linearService.create_issue(
      request.rootPath, 
      request.title, 
      request.description, 
      request.filePath, 
      request.lineNumber,
      request.tag
    )
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
