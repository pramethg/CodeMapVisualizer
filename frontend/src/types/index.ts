export interface FileNode {
  name: string;
  type: "file" | "folder";
  path: string;
  children?: FileNode[];
}

export interface ScanFolderResponse {
  name: string;
  type: "folder";
  path: string;
  children: FileNode[];
}

export interface ClassDetail {
  name: string;
  properties: { name: string; attributes: string[] }[];
  methods: { name: string; attributes: string[]; signature: string }[];
}

export interface ScanFileResponse {
  type: string;
  functions: string[];
  classes: string[];
  classDetails?: ClassDetail[];
  signatures?: Record<string, string>;
  definitions?: Record<string, string>;  // functionName -> full source code
  comments?: { nodeLabel: string; text: string; title?: string; tag?: string }[];
}

