import React, { memo, useCallback, useState, useEffect } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Trash2, Tag } from 'lucide-react';

// Tag configurations with colors
const TAGS = [
  { id: 'none', label: '', color: 'transparent', textColor: '#422006' },
  { id: 'todo', label: 'TODO', color: '#3b82f6', textColor: 'white' },
  { id: 'bug', label: 'BUG', color: '#ef4444', textColor: 'white' },
  { id: 'refactor', label: 'REFACTOR', color: '#8b5cf6', textColor: 'white' },
  { id: 'review', label: 'REVIEW', color: '#f59e0b', textColor: 'white' },
  { id: 'done', label: 'DONE', color: '#22c55e', textColor: 'white' },
];

const CommentNode = ({ data, id, selected }: NodeProps) => {
  const [text, setText] = useState(data.label as string);
  const [title, setTitle] = useState((data.title as string) || "");
  const [tag, setTag] = useState((data.tag as string) || "none");
  const [isEditing, setIsEditing] = useState(false);
  const [showTagMenu, setShowTagMenu] = useState(false);

  // Sync internal state
  useEffect(() => {
    setText(data.label as string);
    setTitle((data.title as string) || "");
    setTag((data.tag as string) || "none");
  }, [data.label, data.title, data.tag]);

  const triggerUpdate = useCallback((updates: { text?: string; title?: string; tag?: string }) => {
    if (data.onUpdate) {
      // @ts-ignore
      data.onUpdate(id, {
        text: updates.text ?? text,
        title: updates.title ?? title,
        tag: updates.tag ?? tag
      });
    }
  }, [id, text, title, tag, data]);

  const onBlurText = useCallback(() => {
    setIsEditing(false);
    triggerUpdate({ text, title, tag });
  }, [text, title, tag, triggerUpdate]);

  const onBlurTitle = useCallback(() => {
    triggerUpdate({ text, title, tag });
  }, [text, title, tag, triggerUpdate]);

  const onTagSelect = useCallback((tagId: string) => {
    setTag(tagId);
    setShowTagMenu(false);
    triggerUpdate({ text, title, tag: tagId });
  }, [text, title, triggerUpdate]);

  const onDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (data.onDelete) {
      // @ts-ignore
      data.onDelete(id);
    }
  }, [id, data]);

  // Auto-focus on mount if new
  useEffect(() => {
    if (data.isNew) {
      setIsEditing(true);
    }
  }, [data.isNew]);

  const currentTag = TAGS.find(t => t.id === tag) || TAGS[0];
  const hasTag = tag !== 'none';

  return (
    <div
      className="shadow-xl rounded-lg border-2 flex flex-col overflow-visible relative"
      style={{
        backgroundColor: '#fef9c3',
        borderColor: hasTag ? currentTag.color : '#ca8a04',
        color: '#000000',
        width: '260px',
        minHeight: '100px'
      }}
    >
      <Handle type="target" position={Position.Left} className="w-2 h-2 !bg-yellow-600" />

      {/* TAG BADGE - LARGER AND MORE VISIBLE */}
      {hasTag && (
        <div
          className="absolute -top-3 left-3 px-3 py-1 rounded-full text-[11px] font-bold shadow-lg border-2 border-white"
          style={{ backgroundColor: currentTag.color, color: currentTag.textColor }}
        >
          {currentTag.label}
        </div>
      )}

      {/* HEADER: Label + Actions */}
      <div
        className="flex items-center px-3 py-2 border-b border-yellow-600/30 bg-yellow-200/50"
        style={{ marginTop: hasTag ? '8px' : '0' }}
      >
        <input
          className="text-xs font-bold uppercase tracking-wider bg-transparent outline-none min-w-0 flex-1 placeholder-yellow-800/50"
          style={{ color: '#422006' }}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={onBlurTitle}
          placeholder="LABEL"
        />
        <div className="flex gap-1 items-center flex-shrink-0">
          {/* Tag Button */}
          <div className="relative">
            <button
              onClick={(e) => { e.stopPropagation(); setShowTagMenu(!showTagMenu); }}
              title="Add Tag"
              className="p-1 rounded hover:bg-yellow-300/50 transition-colors"
              style={{ color: hasTag ? currentTag.color : '#854d0e' }}
            >
              <Tag size={16} />
            </button>

            {/* Tag Dropdown */}
            {showTagMenu && (
              <div
                className="absolute top-8 right-0 bg-zinc-800 rounded-lg shadow-xl border border-zinc-700 py-2 z-50 min-w-[120px]"
                onMouseLeave={() => setShowTagMenu(false)}
              >
                {TAGS.map(t => (
                  <button
                    key={t.id}
                    onClick={(e) => { e.stopPropagation(); onTagSelect(t.id); }}
                    className="w-full px-3 py-2 text-left text-xs hover:bg-zinc-700 flex items-center gap-2"
                  >
                    {t.id !== 'none' && (
                      <span
                        className="w-4 h-4 rounded-full flex-shrink-0"
                        style={{ backgroundColor: t.color }}
                      />
                    )}
                    <span className="text-white">{t.id === 'none' ? 'No Tag' : t.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Delete Button */}
          <button
            onClick={onDelete}
            title="Delete Comment"
            className="p-1 rounded hover:bg-red-100 hover:text-red-600 transition-colors"
            style={{ color: '#854d0e' }}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* BODY: Text Content */}
      <div className="p-3 flex-1">
        {isEditing ? (
          <textarea
            className="w-full bg-transparent outline-none resize-none text-sm font-sans placeholder-yellow-800/50"
            style={{ color: '#000000', minHeight: '60px' }}
            value={text}
            onChange={(evt) => setText(evt.target.value)}
            onBlur={onBlurText}
            autoFocus
            rows={4}
            placeholder="Type your comment here..."
          />
        ) : (
          <div
            className="text-sm font-sans cursor-text whitespace-pre-wrap"
            style={{ color: '#000000', minHeight: '60px' }}
            onClick={() => setIsEditing(true)}
          >
            {text || <span className="opacity-50 italic">Click to add comment...</span>}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(CommentNode);
