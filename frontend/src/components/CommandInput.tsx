'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Loader2, Zap } from 'lucide-react';

const EXAMPLES = [
  'Open https://example.com and take a screenshot',
  'Go to Google Drive and list the most recent files',
  'Open https://colab.new and create a notebook called "Data Analysis"',
  'Navigate to Gmail and extract the subject of the latest unread email',
];

interface Props {
  onSubmit: (command: string) => void;
  isRunning: boolean;
}

export function CommandInput({ onSubmit, isRunning }: Props) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const cmd = value.trim();
    if (!cmd || isRunning) return;
    onSubmit(cmd);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => { setValue(e.target.value); autoResize(); }}
            onKeyDown={onKeyDown}
            disabled={isRunning}
            placeholder="Describe what you want the browser to do… (Shift+Enter for newline)"
            rows={1}
            className="w-full resize-none rounded-lg border border-slate-600 bg-slate-800 px-4 py-2.5
              text-sm text-slate-100 placeholder-slate-500 outline-none
              focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40
              disabled:opacity-50 disabled:cursor-not-allowed transition-colors
              font-mono leading-relaxed"
          />
        </div>
        <button
          onClick={submit}
          disabled={isRunning || !value.trim()}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500
            disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium
            transition-colors shrink-0"
        >
          {isRunning
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Send className="w-4 h-4" />}
          {isRunning ? 'Running…' : 'Run'}
        </button>
      </div>

      {/* Quick-pick examples */}
      {!isRunning && !value && (
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setValue(ex)}
              className="flex items-center gap-1 px-2 py-1 rounded-md bg-slate-700/60
                text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700
                transition-colors border border-slate-600/40"
            >
              <Zap className="w-3 h-3 text-blue-400" />
              <span className="truncate max-w-[28ch]">{ex}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
