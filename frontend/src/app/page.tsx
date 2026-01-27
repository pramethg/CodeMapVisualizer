"use client";

import React, { useState, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import MindMap from "@/components/MindMap";
import { Menu } from "lucide-react";
import { FileNode, ScanFileResponse } from "@/types";
import { scanFile, addComment, saveComments } from "@/lib/api";
import { fileToGraph } from "@/lib/graphUtils";
import { Node, Edge } from "@xyflow/react";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [currentView, setCurrentView] = useState<string>("Empty");
  const [darkMode, setDarkMode] = useState(true);
  const [dotColor, setDotColor] = useState("#333333");
  const [fontSize, setFontSize] = useState(12);
  const [spacing, setSpacing] = useState(30); // Default spacing
  const [comments, setComments] = useState<{ nodeLabel: string; text: string }[]>([]);
  const [currentPath, setCurrentPath] = useState<string>("");
  const [scanResult, setScanResult] = useState<ScanFileResponse | null>(null);
  const [projectRoot, setProjectRoot] = useState<string>("");
  
  // Ref to expose cleanWorkspace function from MindMap
  const cleanWorkspaceRef = useRef<(() => void) | null>(null);

  const handleFolderLoaded = (rootNode: FileNode) => {
    setCurrentView(`Folder: ${rootNode.name}`);
    setProjectRoot(rootNode.path);
  };

  // Re-calculate layout when spacing or data changes
  React.useEffect(() => {
    if (scanResult && currentPath) {
      const fileName = currentPath.split('/').pop() || "File";
      const { nodes: newNodes, edges: newEdges } = fileToGraph(scanResult, fileName, spacing);
      setNodes(newNodes);
      setEdges(newEdges);
    }
  }, [spacing, scanResult, currentPath]);

  const handleFileSelect = async (path: string) => {
    try {
      const result = await scanFile(path, projectRoot);
      const fileName = path.split('/').pop() || "File";

      setScanResult(result); // Trigger layout effect
      setCurrentView(`File: ${fileName}`);
      setCurrentPath(path);

      if (result.comments) {
        setComments(result.comments);
      } else {
        setComments([]);
      }
    } catch (e) {
      console.error(e);
      alert("Failed to scan file");
    }
  };

  const handleAddComment = async (nodeLabel: string, text: string) => {
    if (!currentPath) {
      alert("No file selected");
      return;
    }
    try {
      const result = await addComment(currentPath, nodeLabel, text, projectRoot);
      if (result.comments) {
        setComments(result.comments);
        // Also update scanResult to keep comments in sync for re-layouts if needed
        // Assuming addComment returns updated structure or just comments?
        // Usually addComment returns ScanFileResponse or similar.
        // For safe side, we rely on comments state for Sidebar, but graph might need update if comments are nodes.
        // If comments are nodes, we might need to update scanResult.comments too.
        if (scanResult) {
          setScanResult({
            ...scanResult,
            comments: result.comments
          });
        }
      }
    } catch (e) {
      console.error(e);
      alert("Failed to add comment");
    }
  };

  const handleSaveComments = async (newComments: { nodeLabel: string; text: string; title?: string; tag?: string }[]) => {
    if (!currentPath) return;
    try {
      const result = await saveComments(currentPath, newComments, projectRoot);
      if (result.comments) {
        setComments(result.comments);
        if (scanResult) {
          setScanResult({
            ...scanResult,
            comments: result.comments
          });
        }
      }
    } catch (e) {
      console.error("Failed to save comments", e);
    }
  };

  return (
    <div className={`flex h-screen w-screen overflow-hidden font-sans transition-colors duration-300 ${darkMode ? "bg-zinc-950 text-white" : "bg-white text-zinc-900"}`}>
      {/* HEADER / TOGGLE - MOVED TO RIGHT */}
      <div className="absolute top-4 right-4 z-40">
        <button
          onClick={() => setSidebarOpen(true)}
          className={`p-2 rounded-full transition shadow-lg ${darkMode ? "bg-zinc-800 hover:bg-zinc-700 text-white" : "bg-white hover:bg-gray-100 text-zinc-900 border border-gray-200"}`}
        >
          <Menu size={20} />
        </button>
      </div>

      <div className={`absolute top-4 left-4 z-40 backdrop-blur px-4 py-2 rounded-full border text-sm ${darkMode ? "bg-zinc-900/80 border-zinc-700" : "bg-white/80 border-gray-200"}`}>
        Viewing: <span className="font-semibold text-blue-500">{currentView}</span>
      </div>

      {/* MAIN CONTENT (MIND MAP) */}
      <main className="flex-1 relative">
        <MindMap
          initialNodes={nodes}
          initialEdges={edges}
          darkMode={darkMode}
          dotColor={dotColor}
          fontSize={fontSize}
          onAddComment={handleAddComment}
          onSaveComments={handleSaveComments}
          cleanWorkspaceRef={cleanWorkspaceRef}
        />
      </main>

      {/* SIDEBAR */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onFolderLoaded={handleFolderLoaded}
        onFileSelect={handleFileSelect}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        dotColor={dotColor}
        setDotColor={setDotColor}
        fontSize={fontSize}
        setFontSize={setFontSize}
        spacing={spacing}
        setSpacing={setSpacing}
        comments={comments}
        currentFile={currentPath}
        onCleanWorkspace={() => cleanWorkspaceRef.current?.()}
      />
    </div>
  );
}
