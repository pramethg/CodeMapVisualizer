import React, { useCallback, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Node,
  Edge,
  BackgroundVariant
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import { Search, X, Copy, Check, Download, ChevronUp, ChevronDown, LayoutGrid } from "lucide-react";
import CommentNode from "./CommentNode";

interface MindMapProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  darkMode: boolean;
  dotColor: string;
  fontSize?: number;
  onAddComment: (nodeLabel: string, comment: string) => void;
  onSaveComments?: (comments: { nodeLabel: string; text: string; title?: string; tag?: string }[]) => void;
  cleanWorkspaceRef?: React.MutableRefObject<(() => void) | null>;
}

const nodeTypes = {
  commentNode: CommentNode
};

// Inner component that uses ReactFlow hooks
function MindMapInner({ initialNodes, initialEdges, darkMode, dotColor, fontSize = 18, onAddComment, onSaveComments, cleanWorkspaceRef }: MindMapProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [activeSignature, setActiveSignature] = React.useState<string | null>(null);
  const [activeSignatureType, setActiveSignatureType] = React.useState<string>("function");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [searchFocused, setSearchFocused] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const [currentMatchIndex, setCurrentMatchIndex] = React.useState(0);
  const [highlightedNodeIds, setHighlightedNodeIds] = React.useState<Set<string>>(new Set());

  // Triple-click detection state
  const [showSourceModal, setShowSourceModal] = React.useState(false);
  const [activeSourceCode, setActiveSourceCode] = React.useState<string | null>(null);
  const [activeSourceLabel, setActiveSourceLabel] = React.useState<string>("");
  const clickCountRef = useRef(0);
  const clickTimerRef = useRef<NodeJS.Timeout | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const { fitView, setCenter, getZoom } = useReactFlow();

  // --- HANDLERS ---
  const handleUpdateComment = useCallback((nodeId: string, content: { text: string; title: string; tag?: string }) => {
    setNodes((nds) => {
      const updatedNodes = nds.map(n => {
        if (n.id === nodeId) {
          return { ...n, data: { ...n.data, label: content.text, title: content.title, tag: content.tag || n.data.tag || "none" } };
        }
        return n;
      });

      if (onSaveComments) {
        const allComments = updatedNodes
          .filter(n => n.type === 'commentNode')
          .map(n => ({
            nodeLabel: n.data.parentLabel as string || "Unknown",
            text: n.data.label as string,
            title: n.data.title as string,
            tag: n.data.tag as string || "none"
          }));
        onSaveComments(allComments);
      }
      return updatedNodes;
    });
  }, [setNodes, onSaveComments]);

  const handleDeleteComment = useCallback((nodeId: string) => {
    let remainingNodes: Node[] = [];
    setNodes((nds) => {
      remainingNodes = nds.filter((n) => n.id !== nodeId);

      if (onSaveComments) {
        const allComments = remainingNodes
          .filter(n => n.type === 'commentNode')
          .map(n => ({
            nodeLabel: n.data.parentLabel as string || "Unknown",
            text: n.data.label as string,
            title: n.data.title as string,
            tag: n.data.tag as string || "none"
          }));
        onSaveComments(allComments);
      }
      return remainingNodes;
    });
    setEdges((eds) => eds.filter((e) => e.target !== nodeId && e.source !== nodeId));
  }, [setNodes, setEdges, onSaveComments]);

  const getConnectedNodes = useCallback((nodeId: string) => {
    const connected = new Set<string>();
    connected.add(nodeId);
    edges.forEach(e => {
      if (e.source === nodeId) connected.add(e.target);
      if (e.target === nodeId) connected.add(e.source);
    });
    return connected;
  }, [edges]);

  // Helper to apply consistent styling
  const getStyledNode = useCallback((node: Node, size: number) => {
    const isComment = node.type === 'commentNode';
    const baseStyle = {
      ...node.style,
      fontSize: size,
      width: 'fit-content',
      minWidth: 'min-content',
      maxWidth: '600px', // Prevent extremely wide nodes
      height: 'auto',
      padding: '0.25em 0.8em', // Compact vertical padding
    };

    if (isComment) {
      return {
        ...node,
        style: baseStyle,
        data: {
          ...node.data,
          onUpdate: handleUpdateComment,
          onDelete: handleDeleteComment
        }
      };
    }

    return {
      ...node,
      style: baseStyle
    };
  }, [handleUpdateComment, handleDeleteComment]);

  // Sync with initial props
  useEffect(() => {
    const nodesWithHandlers = initialNodes.map(node => getStyledNode(node, fontSize));
    setNodes(nodesWithHandlers);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges, getStyledNode, fontSize]);

  // Update font size for existing nodes
  useEffect(() => {
    setNodes((nds) => nds.map(node => getStyledNode(node, fontSize)));
  }, [fontSize, setNodes, getStyledNode]);

  // --- KEYBOARD SHORTCUTS ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + F to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
      // Escape to clear search and close modals
      if (e.key === 'Escape') {
        setSearchQuery("");
        setActiveSignature(null);
        setHighlightedNodeIds(new Set());
        setShowSourceModal(false);
        searchInputRef.current?.blur();
      }
      // Arrow keys to navigate matches
      if (searchQuery && matchedNodeIds.size > 0) {
        const matchArray = Array.from(matchedNodeIds);
        if (e.key === 'ArrowDown' || e.key === 'Enter') {
          e.preventDefault();
          const nextIndex = (currentMatchIndex + 1) % matchArray.length;
          setCurrentMatchIndex(nextIndex);
          zoomToNode(matchArray[nextIndex]);
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          const prevIndex = (currentMatchIndex - 1 + matchArray.length) % matchArray.length;
          setCurrentMatchIndex(prevIndex);
          zoomToNode(matchArray[prevIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [searchQuery, currentMatchIndex]);

  // --- ZOOM TO NODE ---
  const zoomToNode = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      const x = node.position.x + (node.width || 100) / 2;
      const y = node.position.y + (node.height || 50) / 2;
      setCenter(x, y, { zoom: 1.5, duration: 500 });
    }
  }, [nodes, setCenter]);

  // --- COPY SIGNATURE ---
  const copySignature = useCallback(() => {
    if (activeSignature) {
      navigator.clipboard.writeText(activeSignature);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [activeSignature]);

  // --- CLEAN WORKSPACE / AUTO-LAYOUT ---
  const cleanWorkspace = useCallback(() => {
    const g = new dagre.graphlib.Graph();
    g.setGraph({
      rankdir: "LR",
      nodesep: 40,
      ranksep: 100,
      marginx: 20,
      marginy: 20
    });
    g.setDefaultEdgeLabel(() => ({}));

    // Add all nodes to the graph
    nodes.forEach((node) => {
      g.setNode(node.id, {
        width: node.width || (node.type === 'commentNode' ? 220 : 150),
        height: node.height || (node.type === 'commentNode' ? 80 : 40)
      });
    });

    // Add all edges to the graph
    edges.forEach((edge) => {
      g.setEdge(edge.source, edge.target);
    });

    // Run dagre layout
    dagre.layout(g);

    // Apply new positions to nodes
    const layoutedNodes = nodes.map((node) => {
      const nodeWithPosition = g.node(node.id);
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - (nodeWithPosition.width || 0) / 2,
          y: nodeWithPosition.y - (nodeWithPosition.height || 0) / 2,
        },
      };
    });

    setNodes(layoutedNodes);

    // Fit view after layout
    setTimeout(() => fitView({ padding: 0.2, duration: 500 }), 50);
  }, [nodes, edges, setNodes, fitView]);

  // Expose cleanWorkspace to parent via ref
  useEffect(() => {
    if (cleanWorkspaceRef) {
      cleanWorkspaceRef.current = cleanWorkspace;
    }
  }, [cleanWorkspace, cleanWorkspaceRef]);

  // --- HANDLERS ---

  // --- END HANDLERS ---

  // --- SEARCH LOGIC ---

  const matchedNodeIds = useMemo(() => {
    if (!searchQuery.trim()) return new Set<string>();
    const query = searchQuery.toLowerCase();
    const matches = new Set<string>();
    nodes.forEach(node => {
      const label = (node.data.label as string || "").toLowerCase();
      if (label.includes(query)) {
        matches.add(node.id);
      }
    });
    return matches;
  }, [searchQuery, nodes]);

  // Reset match index when search changes
  useEffect(() => {
    setCurrentMatchIndex(0);
  }, [searchQuery]);

  const filteredNodes = useMemo(() => {
    // 1. Highlight Connected Nodes (Priority)
    if (highlightedNodeIds.size > 0) {
      return nodes.map(node => {
        if (highlightedNodeIds.has(node.id)) {
          return {
            ...node,
            style: {
              ...node.style,
              opacity: 1,
              border: '3px solid #8b5cf6', // Violet
              boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)',
              zIndex: 100
            }
          };
        }
        return {
          ...node,
          style: {
            ...node.style,
            opacity: 0.1
          }
        };
      });
    }

    if (!searchQuery.trim()) return nodes;
    const matchArray = Array.from(matchedNodeIds);
    const currentMatchId = matchArray[currentMatchIndex];

    return nodes.map(node => {
      if (node.id === currentMatchId) {
        // Current match - extra highlight
        return {
          ...node,
          style: {
            ...node.style,
            boxShadow: '0 0 30px 10px rgba(34, 197, 94, 0.7)', // Green glow for current
            border: '3px solid #22c55e',
            zIndex: 200
          }
        };
      } else if (matchedNodeIds.has(node.id)) {
        return {
          ...node,
          style: {
            ...node.style,
            boxShadow: '0 0 20px 5px rgba(59, 130, 246, 0.6)',
            border: '2px solid #3b82f6',
            zIndex: 100
          }
        };
      } else {
        return {
          ...node,
          style: {
            ...node.style,
            opacity: 0.3
          }
        };
      }
    });
  }, [nodes, searchQuery, matchedNodeIds, currentMatchIndex, highlightedNodeIds]);

  const onPaneClick = useCallback(() => {
    setActiveSignature(null);
    setHighlightedNodeIds(new Set());
  }, []);

  // Store last clicked node for multi-click reference
  const lastClickedNodeRef = useRef<Node | null>(null);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // Store the node for reference in timeout
      lastClickedNodeRef.current = node;

      // Multi-click detection
      clickCountRef.current += 1;

      if (clickTimerRef.current) {
        clearTimeout(clickTimerRef.current);
      }

      clickTimerRef.current = setTimeout(() => {
        const clickedNode = lastClickedNodeRef.current;

        // Handle based on click count
        if (clickCountRef.current >= 3 && clickedNode) {
          // Triple-click: Highlight connected nodes
          const connected = getConnectedNodes(clickedNode.id);
          setHighlightedNodeIds(connected);
        } else if (clickCountRef.current === 2 && clickedNode) {
          // Double-click: show source code modal
          if (clickedNode.data.sourceCode) {
            setActiveSourceCode(clickedNode.data.sourceCode as string);
            setActiveSourceLabel(clickedNode.data.label as string);
            setShowSourceModal(true);
          }
        } else if (clickCountRef.current === 1 && clickedNode) {
          // Single click: show signature
          if (clickedNode.data.signature) {
            setActiveSignature(clickedNode.data.signature as string);
            setActiveSignatureType(clickedNode.data.type as string || "function");
          } else {
            setActiveSignature(null);
          }
        }
        // Reset click count
        clickCountRef.current = 0;
      }, 350);
    },
    [zoomToNode]
  );

  // Disable React Flow's built-in double-click handler since we handle it ourselves
  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, _node: Node) => {
      // Do nothing - handled by our custom click detection above
    },
    []
  );

  const onNodeContextMenu = useCallback(
    (e: React.MouseEvent, node: Node) => {
      e.preventDefault();
      if (node.type === 'commentNode') return;

      const parentId = node.id;
      const label = node.data.label as string;

      const newCommentId = `comment-${Date.now()}`;
      const newCommentNode: Node = {
        id: newCommentId,
        type: 'commentNode',
        position: {
          x: node.position.x + (node.width || 100) + 50,
          y: node.position.y
        },
        data: {
          label: "",
          title: "",
          isNew: true,
          parentId: parentId,
          parentLabel: label,
          onUpdate: handleUpdateComment,
          onDelete: handleDeleteComment
        },
        style: { width: 220 }
      };

      const newEdge: Edge = {
        id: `${parentId}-${newCommentId}`,
        source: parentId,
        target: newCommentId,
        animated: false,
        style: { stroke: '#d97706', strokeWidth: 1.5 }
      };

      setNodes((nds) => [...nds, newCommentNode]);
      setEdges((eds) => [...eds, newEdge]);
    },
    [setNodes, setEdges, handleUpdateComment, handleDeleteComment]
  );

  return (
    <div className={`w-full h-full relative ${darkMode ? "bg-zinc-950" : "bg-white"}`}>
      {/* SEARCH BAR */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg border transition-all duration-200 ${searchFocused
            ? (darkMode ? "bg-zinc-800 border-blue-500 w-80" : "bg-white border-blue-500 w-80")
            : (darkMode ? "bg-zinc-800/80 border-zinc-700 w-64" : "bg-white/80 border-gray-200 w-64")
            }`}
        >
          <Search size={16} className={darkMode ? "text-zinc-400" : "text-gray-400"} />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            placeholder="Search (⌘F)"
            className={`flex-1 bg-transparent outline-none text-sm ${darkMode ? "text-white placeholder-zinc-500" : "text-zinc-900 placeholder-gray-400"
              }`}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className={`p-1 rounded-full hover:bg-zinc-700/50 transition-colors ${darkMode ? "text-zinc-400 hover:text-white" : "text-gray-400 hover:text-gray-600"
                }`}
            >
              <X size={14} />
            </button>
          )}
        </div>
        {/* Match navigation */}
        {searchQuery && matchedNodeIds.size > 0 && (
          <div className={`flex items-center justify-center gap-2 mt-2 ${darkMode ? "text-zinc-400" : "text-gray-500"}`}>
            <button
              onClick={() => {
                const matchArray = Array.from(matchedNodeIds);
                const prevIndex = (currentMatchIndex - 1 + matchArray.length) % matchArray.length;
                setCurrentMatchIndex(prevIndex);
                zoomToNode(matchArray[prevIndex]);
              }}
              className="p-1 rounded hover:bg-zinc-700/50"
            >
              <ChevronUp size={14} />
            </button>
            <span className="text-xs">
              <span className="font-bold text-green-500">{currentMatchIndex + 1}</span>
              <span className="opacity-50"> / {matchedNodeIds.size}</span>
            </span>
            <button
              onClick={() => {
                const matchArray = Array.from(matchedNodeIds);
                const nextIndex = (currentMatchIndex + 1) % matchArray.length;
                setCurrentMatchIndex(nextIndex);
                zoomToNode(matchArray[nextIndex]);
              }}
              className="p-1 rounded hover:bg-zinc-700/50"
            >
              <ChevronDown size={14} />
            </button>
          </div>
        )}
      </div>

      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        onNodeContextMenu={onNodeContextMenu}
        onPaneClick={onPaneClick}
        fitView
        className={darkMode ? "bg-zinc-950" : "bg-white"}
      >
        <Background color={dotColor} variant={BackgroundVariant.Dots} gap={20} />
        <Controls
          className={
            darkMode
              ? "bg-zinc-800 border-zinc-700 [&>button]:!bg-zinc-800 [&>button]:!border-zinc-700 [&>button]:!fill-zinc-200 [&>button:hover]:!bg-zinc-700"
              : "bg-white border-gray-200 fill-gray-500"
          }
        />
        {/* MINI-MAP */}
        <MiniMap
          nodeColor={(node) => {
            if (node.type === 'commentNode') return '#fbbf24';
            if (node.data.type === 'file') return '#3b82f6';
            if (node.data.type === 'class') return '#8b5cf6';
            if (node.data.type === 'function') return '#22c55e';
            return darkMode ? '#52525b' : '#a1a1aa';
          }}
          maskColor={darkMode ? "rgba(0,0,0,0.8)" : "rgba(255,255,255,0.8)"}
          className={darkMode ? "bg-zinc-900 border-zinc-700" : "bg-gray-100 border-gray-200"}
          pannable
          zoomable
        />
      </ReactFlow>

      {/* Function Info Panel with Copy Button */}
      <AnimatePresence>
        {activeSignature && (
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 50, opacity: 0 }}
            className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-50"
          >
            <div className={`px-6 py-3 rounded-lg shadow-xl border ${darkMode ? "bg-zinc-800 border-zinc-700 text-zinc-100" : "bg-white border-zinc-200 text-zinc-800"}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs uppercase tracking-wider opacity-50">
                  {activeSignatureType === 'property' ? 'Property Signature' : 'Function Signature'}
                </div>
                <button
                  onClick={copySignature}
                  className={`p-1 rounded transition-colors pointer-events-auto ${copied
                    ? "text-green-500"
                    : (darkMode ? "text-zinc-400 hover:text-white" : "text-gray-400 hover:text-gray-600")
                    }`}
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
              <code className="font-mono text-sm block whitespace-pre max-w-[80vw] overflow-hidden text-ellipsis">
                {activeSignature}
              </code>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Source Code Modal (Triple-Click) */}
      <AnimatePresence>
        {showSourceModal && activeSourceCode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowSourceModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className={`relative max-w-4xl max-h-[80vh] w-full mx-4 rounded-xl shadow-2xl border overflow-hidden ${darkMode ? "bg-zinc-900 border-zinc-700" : "bg-white border-gray-200"
                }`}
            >
              {/* Modal Header */}
              <div className={`flex items-center justify-between px-6 py-4 border-b ${darkMode ? "border-zinc-700 bg-zinc-800" : "border-gray-200 bg-gray-50"
                }`}>
                <div>
                  <div className="text-xs uppercase tracking-wider opacity-50 mb-1">Function Definition</div>
                  <div className={`font-semibold ${darkMode ? "text-white" : "text-gray-900"}`}>
                    {activeSourceLabel}
                  </div>
                </div>
                <button
                  onClick={() => setShowSourceModal(false)}
                  className={`p-2 rounded-lg transition-colors ${darkMode ? "hover:bg-zinc-700 text-zinc-400 hover:text-white" : "hover:bg-gray-200 text-gray-500 hover:text-gray-700"
                    }`}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Code Content */}
              <div className="overflow-auto max-h-[calc(80vh-80px)] p-6">
                <pre className={`font-mono text-sm leading-relaxed ${darkMode ? "text-green-400" : "text-gray-800"
                  }`}>
                  <code>{activeSourceCode}</code>
                </pre>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Wrapper component that provides ReactFlow context
export default function MindMap(props: MindMapProps) {
  return (
    <ReactFlowProvider>
      <MindMapInner {...props} />
    </ReactFlowProvider>
  );
}
