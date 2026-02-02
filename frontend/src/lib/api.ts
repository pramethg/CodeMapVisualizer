import { FileNode, ScanFileResponse, ListDirectoryResponse } from "@/types";

const API_BASE = "http://localhost:8000/api";

async function post(endpoint: string, data: any) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Network error" }));
    throw new Error(error.detail || "API Request Failed");
  }

  return response.json();
}

export async function scanFolder(path: string): Promise<FileNode> {
  return post("/scan-folder", { path });
}

export async function scanFile(path: string, rootPath: string): Promise<ScanFileResponse> {
  return post("/scan-file", { path, rootPath });
}

export async function addComment(
  path: string,
  nodeLabel: string,
  text: string,
  rootPath: string
): Promise<{ comments: any[] }> {
  return post("/add-comment", { path, nodeLabel, text, rootPath });
}

export async function saveComments(
  path: string,
  comments: any[],
  rootPath: string
): Promise<{ comments: any[] }> {
  return post("/save-comments", { path, comments, rootPath });
}

export async function listDirectory(path: string): Promise<ListDirectoryResponse> {
  return post("/list-directory", { path });
}

export async function checkLinearConnection(rootPath: string): Promise<{ connected: boolean; user: { name: string }; message?: string }> {
  return post("/linear/check-connection", { rootPath });
}
