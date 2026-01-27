import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { scanFolder, pickFolder } from "@/lib/api";
import { FileNode } from "@/types";
import { Folder, File, ChevronRight, ChevronDown, X, Play, FolderOpen, Clock, Star, StarOff, Plus, Minus, Trash2 } from "lucide-react";
import { clsx } from "clsx";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onFileSelect: (path: string) => void;
  onFolderLoaded: (node: FileNode) => void;
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  dotColor: string;
  setDotColor: (value: string) => void;
  fontSize: number;

  setFontSize: (value: number) => void;
  spacing: number;
  setSpacing: (value: number) => void;
  comments?: { nodeLabel: string; text: string }[];
  currentFile?: string;
}

// LocalStorage keys
const RECENT_FILES_KEY = 'codemap_recent_files';
const BOOKMARKS_KEY = 'codemap_bookmarks';
const MAX_RECENT = 10;

export default function Sidebar({
  isOpen,
  onClose,
  onFileSelect,
  onFolderLoaded,
  darkMode,
  setDarkMode,
  dotColor,
  setDotColor,
  fontSize,
  setFontSize,
  comments,
  spacing,
  setSpacing,
  currentFile
}: SidebarProps) {
  const [path, setPath] = useState("");
  const [rootNode, setRootNode] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentFiles, setRecentFiles] = useState<string[]>([]);
  const [bookmarks, setBookmarks] = useState<string[]>([]);

  // Load recent files and bookmarks from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_FILES_KEY);
      if (stored) setRecentFiles(JSON.parse(stored));
      const storedBookmarks = localStorage.getItem(BOOKMARKS_KEY);
      if (storedBookmarks) setBookmarks(JSON.parse(storedBookmarks));
    } catch (e) {
      console.error("Failed to load from localStorage", e);
    }
  }, []);

  // Save recent files when they change
  useEffect(() => {
    localStorage.setItem(RECENT_FILES_KEY, JSON.stringify(recentFiles));
  }, [recentFiles]);

  // Save bookmarks when they change
  useEffect(() => {
    localStorage.setItem(BOOKMARKS_KEY, JSON.stringify(bookmarks));
  }, [bookmarks]);

  const addRecentFile = (filePath: string) => {
    setRecentFiles(prev => {
      const filtered = prev.filter(p => p !== filePath);
      return [filePath, ...filtered].slice(0, MAX_RECENT);
    });
  };

  const toggleBookmark = (filePath: string) => {
    setBookmarks(prev => {
      if (prev.includes(filePath)) {
        return prev.filter(p => p !== filePath);
      }
      return [...prev, filePath];
    });
  };

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await scanFolder(path);
      setRootNode(result);
      onFolderLoaded(result);
    } catch (err) {
      setError("Failed to load folder. Check path and backend.");
    } finally {
      setLoading(false);
    }
  };

  const handlePickFolder = async () => {
    try {
      const result = await pickFolder();
      if (result.path) {
        setPath(result.path);
        setError(null);
      }
    } catch (e) {
      console.error(e);
      setError("Failed to open folder picker. Is backend running?");
    }
  };

  const handleFileClick = (filePath: string) => {
    addRecentFile(filePath);
    onFileSelect(filePath);
  };

  const handleClearCache = () => {
    if (confirm("Are you sure you want to clear recent files and bookmarks? This cannot be undone.")) {
      setRecentFiles([]);
      setBookmarks([]);
      localStorage.removeItem(RECENT_FILES_KEY);
      localStorage.removeItem(BOOKMARKS_KEY);
    }
  };

  const getFileName = (path: string) => path.split('/').pop() || path;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed right-0 top-0 h-full w-80 bg-zinc-900 border-l border-zinc-700 shadow-2xl p-4 text-white z-50 overflow-y-auto"
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-white">
              Project Explorer
            </h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-zinc-800 rounded-full transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex gap-2 mb-4">
            <div className="flex-1 flex gap-1">
              <input
                type="text"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="/absolute/path/to/project"
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
              />
              <button
                onClick={handlePickFolder}
                title="Select Folder from System"
                className="bg-zinc-700 hover:bg-zinc-600 p-2 rounded transition-colors text-zinc-300 hover:text-white"
              >
                <FolderOpen size={18} />
              </button>
            </div>
            <button
              onClick={handleScan}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 p-2 rounded transition-colors disabled:opacity-50"
            >
              <Play size={18} />
            </button>
          </div>

          {error && <div className="text-red-400 text-sm mb-4">{error}</div>}

          {loading && (
            <div className="flex justify-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}

          {/* BOOKMARKS SECTION */}
          {bookmarks.length > 0 && (
            <div className="mb-4 border-b border-zinc-700/50 pb-4">
              <h3 className="text-xs font-semibold text-zinc-400 mb-2 uppercase tracking-wider flex items-center gap-1">
                <Star size={12} className="text-yellow-400" /> Bookmarks
              </h3>
              <div className="space-y-1">
                {bookmarks.map((file) => (
                  <div
                    key={file}
                    className="flex items-center gap-2 py-1 px-2 rounded cursor-pointer hover:bg-zinc-800 text-sm text-zinc-300 hover:text-white transition-colors group"
                  >
                    <File size={12} />
                    <span className="flex-1 truncate" onClick={() => handleFileClick(file)}>
                      {getFileName(file)}
                    </span>
                    <button
                      onClick={() => toggleBookmark(file)}
                      className="opacity-0 group-hover:opacity-100 text-yellow-400 hover:text-yellow-300 transition-opacity"
                    >
                      <StarOff size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RECENT FILES SECTION */}
          {recentFiles.length > 0 && (
            <div className="mb-4 border-b border-zinc-700/50 pb-4">
              <h3 className="text-xs font-semibold text-zinc-400 mb-2 uppercase tracking-wider flex items-center gap-1">
                <Clock size={12} /> Recent Files
              </h3>
              <div className="space-y-1">
                {recentFiles.slice(0, 5).map((file) => (
                  <div
                    key={file}
                    className="flex items-center gap-2 py-1 px-2 rounded cursor-pointer hover:bg-zinc-800 text-sm text-zinc-300 hover:text-white transition-colors group"
                  >
                    <File size={12} />
                    <span className="flex-1 truncate" onClick={() => handleFileClick(file)}>
                      {getFileName(file)}
                    </span>
                    <button
                      onClick={() => toggleBookmark(file)}
                      className={`opacity-0 group-hover:opacity-100 transition-opacity ${bookmarks.includes(file) ? 'text-yellow-400' : 'text-zinc-500 hover:text-yellow-400'
                        }`}
                    >
                      <Star size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* APPEARANCE SECTION */}
          <div className="mb-4 border-b border-zinc-700/50 pb-4">
            <h3 className="text-xs font-semibold text-zinc-400 mb-3 uppercase tracking-wider">Appearance</h3>

            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-zinc-300">Theme</span>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`text-xs px-3 py-1 rounded-full border transition-colors ${darkMode ? 'bg-zinc-800 border-zinc-600 text-white' : 'bg-white border-zinc-300 text-black'}`}
              >
                {darkMode ? 'Dark Mode' : 'Light Mode'}
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-300">Dot Color</span>
              <input
                type="color"
                value={dotColor}
                onChange={(e) => setDotColor(e.target.value)}
                className="w-8 h-8 rounded cursor-pointer bg-transparent border-none"
              />
            </div>

            <div className="flex items-center justify-between mt-3">
              <span className="text-sm text-zinc-300">Font Size</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFontSize(Math.max(8, fontSize - 1))}
                  className={`p-1 rounded transition-colors ${darkMode ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-zinc-200 hover:bg-zinc-300'}`}
                  title="Decrease font size"
                >
                  <Minus size={14} />
                </button>
                <span className="text-sm w-8 text-center">{fontSize}px</span>
                <button
                  onClick={() => setFontSize(Math.min(48, fontSize + 1))}
                  className={`p-1 rounded transition-colors ${darkMode ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-zinc-200 hover:bg-zinc-300'}`}
                  title="Increase font size"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>

            {/* Spacing Control */}
            <div className="flex items-center justify-between mt-3">
              <span className="text-sm text-zinc-300">Layout Spacing</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSpacing(Math.max(2, spacing - 4))}
                  className={`p-1 rounded transition-colors ${darkMode ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-zinc-200 hover:bg-zinc-300'}`}
                  title="Decrease spacing"
                >
                  <Minus size={14} />
                </button>
                <span className="text-sm w-8 text-center">{spacing}</span>
                <button
                  onClick={() => setSpacing(Math.min(100, spacing + 4))}
                  className={`p-1 rounded transition-colors ${darkMode ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-zinc-200 hover:bg-zinc-300'}`}
                  title="Increase spacing"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>
          </div>


          {/* SETTINGS SECTION */}
          <div className="mb-4 border-b border-zinc-700/50 pb-4">
            <h3 className="text-xs font-semibold text-zinc-400 mb-3 uppercase tracking-wider">Settings</h3>
            <button
              onClick={handleClearCache}
              className="w-full text-left text-sm text-red-400 hover:text-red-300 transition-colors flex items-center gap-2 py-1 hover:bg-zinc-800 rounded px-2"
            >
              <Trash2 size={14} /> Clear History & Cache
            </button>
          </div>

          {/* FILE TREE */}
          {rootNode && (
            <div className="space-y-1">
              <h3 className="text-xs font-semibold text-zinc-400 mb-2 uppercase tracking-wider">Files</h3>
              <FileTreeNode
                node={rootNode}
                onFileSelect={handleFileClick}
                bookmarks={bookmarks}
                onToggleBookmark={toggleBookmark}
              />
            </div>
          )}
        </motion.div>
      )
      }
    </AnimatePresence >
  );
}

interface FileTreeNodeProps {
  node: FileNode;
  onFileSelect: (path: string) => void;
  bookmarks: string[];
  onToggleBookmark: (path: string) => void;
}

function FileTreeNode({ node, onFileSelect, bookmarks, onToggleBookmark }: FileTreeNodeProps) {
  const [expanded, setExpanded] = useState(false);
  const isFolder = node.type === "folder";
  const isBookmarked = bookmarks.includes(node.path);

  return (
    <div className="pl-3 border-l border-zinc-800/50">
      <div
        className={clsx(
          "flex items-center gap-2 py-1 px-2 rounded cursor-pointer transition-colors text-sm group",
          isFolder ? "hover:bg-zinc-800 text-blue-300" : "hover:bg-zinc-800 text-zinc-300 hover:text-white"
        )}
      >
        {isFolder && (
          <span className="text-zinc-500" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        )}
        <span onClick={() => isFolder ? setExpanded(!expanded) : onFileSelect(node.path)} className="flex items-center gap-2 flex-1">
          {isFolder ? <Folder size={14} /> : <File size={14} />}
          <span className="truncate">{node.name}</span>
        </span>
        {!isFolder && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleBookmark(node.path);
            }}
            className={`opacity-0 group-hover:opacity-100 transition-opacity ${isBookmarked ? 'text-yellow-400' : 'text-zinc-500 hover:text-yellow-400'
              }`}
          >
            <Star size={12} fill={isBookmarked ? 'currentColor' : 'none'} />
          </button>
        )}
      </div>

      {isFolder && expanded && node.children && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
        >
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              onFileSelect={onFileSelect}
              bookmarks={bookmarks}
              onToggleBookmark={onToggleBookmark}
            />
          ))}
        </motion.div>
      )}
    </div>
  );
}
