import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { listDirectory } from "@/lib/api";
import { Folder, File, ChevronUp, X, Check, Loader2 } from "lucide-react";

interface FolderPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (path: string) => void;
  initialPath?: string;
}

export default function FolderPickerModal({
  isOpen,
  onClose,
  onSelect,
  initialPath = ""
}: FolderPickerModalProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [folders, setFolders] = useState<string[]>([]);
  const [files, setFiles] = useState<string[]>([]);
  const [parentPath, setParentPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadDirectory(initialPath);
    }
  }, [isOpen, initialPath]);

  const loadDirectory = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await listDirectory(path);
      setCurrentPath(result.path);
      setParentPath(result.parent);
      setFolders(result.folders);
      setFiles(result.files);
    } catch (err) {
      setError("Failed to load directory. " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (folderName: string) => {
    const newPath = currentPath === "/" 
      ? `/${folderName}`
      : `${currentPath}/${folderName}`;
    loadDirectory(newPath);
  };

  const handleGoUp = () => {
    loadDirectory(parentPath);
  };

  const handleManualPathChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentPath(e.target.value);
  };

  const handleManualPathSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadDirectory(currentPath);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-zinc-900 border border-zinc-700 rounded-lg shadow-2xl w-full max-w-2xl flex flex-col max-h-[80vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-zinc-700">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Folder className="text-blue-400" size={20} />
                Select Folder
              </h2>
              <button
                onClick={onClose}
                className="text-zinc-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Path Bar */}
            <div className="p-4 border-b border-zinc-700 bg-zinc-800/50">
              <form onSubmit={handleManualPathSubmit} className="flex gap-2">
                <button
                  type="button"
                  onClick={handleGoUp}
                  disabled={!parentPath || loading}
                  className="p-2 bg-zinc-700 hover:bg-zinc-600 rounded disabled:opacity-50 text-zinc-300"
                  title="Go Up"
                >
                  <ChevronUp size={18} />
                </button>
                <input
                  type="text"
                  value={currentPath}
                  onChange={handleManualPathChange}
                  className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-3 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
                  placeholder="/path/to/folder"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-3 bg-blue-600 hover:bg-blue-700 rounded text-white text-sm font-medium disabled:opacity-50"
                >
                  Go
                </button>
              </form>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-2 min-h-[300px]">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-full text-zinc-500 gap-2">
                  <Loader2 size={32} className="animate-spin" />
                  <span>Loading directory...</span>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-full text-red-400 gap-2 p-4 text-center">
                  <p>{error}</p>
                  <button 
                    onClick={() => loadDirectory(parentPath || "/")}
                    className="mt-2 text-blue-400 hover:underline"
                  >
                    Go back
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {folders.map((folder) => (
                    <div
                      key={folder}
                      onClick={() => handleNavigate(folder)}
                      className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors group"
                    >
                      <Folder size={18} className="text-blue-400 group-hover:text-blue-300" />
                      <span className="truncate flex-1">{folder}</span>
                    </div>
                  ))}
                  
                  {files.length > 0 && (
                    <>
                      <div className="col-span-1 md:col-span-2 my-2 border-t border-zinc-700/50"></div>
                      {files.map((file) => (
                        <div
                          key={file}
                          className="flex items-center gap-2 p-2 rounded text-zinc-500 cursor-default"
                        >
                          <File size={16} />
                          <span className="truncate flex-1">{file}</span>
                        </div>
                      ))}
                    </>
                  )}
                  
                  {folders.length === 0 && files.length === 0 && (
                     <div className="col-span-1 md:col-span-2 text-center text-zinc-500 py-8">
                       Empty directory
                     </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-zinc-700 flex justify-end gap-2 bg-zinc-800/50">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onSelect(currentPath);
                  onClose();
                }}
                disabled={loading || !currentPath}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white text-sm font-medium transition-colors disabled:opacity-50"
              >
                <Check size={16} />
                Select This Folder
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
