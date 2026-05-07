'use client';

import { useEffect, useState } from 'react';
import { Play, Bookmark, Tag, TrendingUp, Loader2, Plus } from 'lucide-react';
import { listAutomations, createAutomation } from '@/lib/api';
import type { SavedAutomation } from '@/types';

interface Props {
  onRun: (command: string) => void;
}

export function SavedAutomations({ onRun }: Props) {
  const [automations, setAutomations] = useState<SavedAutomation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listAutomations()
      .then(setAutomations)
      .catch(() => setAutomations([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!name.trim() || !template.trim()) return;
    setSaving(true);
    try {
      const saved = await createAutomation(name.trim(), template.trim());
      setAutomations((prev) => [saved, ...prev]);
      setName('');
      setTemplate('');
      setShowForm(false);
    } catch {
      // keep form open on error
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-5 h-5 animate-spin text-slate-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700/50">
        <span className="text-xs text-slate-400 font-medium">{automations.length} saved automation{automations.length !== 1 && 's'}</span>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> New
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/50 space-y-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Automation name"
            className="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-1.5
              text-sm text-slate-200 placeholder-slate-500 outline-none
              focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40"
          />
          <textarea
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            placeholder="Command template (e.g. Open {url} and take a screenshot)"
            rows={2}
            className="w-full resize-none bg-slate-700 border border-slate-600 rounded-md px-3 py-1.5
              text-sm text-slate-200 placeholder-slate-500 outline-none
              focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40 font-mono"
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1 text-xs text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !name.trim() || !template.trim()}
              className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-md
                disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-700/40">
        {automations.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2 py-12">
            <Bookmark className="w-8 h-8" />
            <p className="text-sm">No saved automations yet</p>
            <p className="text-xs text-slate-600">Click "New" to save a reusable command template</p>
          </div>
        )}

        {automations.map((a) => (
          <div key={a.id} className="px-4 py-3 hover:bg-slate-700/20 transition-colors group">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">{a.name}</p>
                {a.description && (
                  <p className="text-xs text-slate-500 mt-0.5 truncate">{a.description}</p>
                )}
                <p className="text-xs text-slate-400 font-mono mt-1 truncate">{a.command_template}</p>

                <div className="flex items-center gap-3 mt-2">
                  {a.tags.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      {a.tags.map((t) => (
                        <span key={t} className="flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded
                          bg-slate-700 text-slate-400">
                          <Tag className="w-2.5 h-2.5" />{t}
                        </span>
                      ))}
                    </div>
                  )}
                  <span className="flex items-center gap-1 text-xs text-slate-500">
                    <TrendingUp className="w-3 h-3" /> {a.use_count} runs
                  </span>
                  <span className="text-xs text-slate-500">{a.success_rate}% success</span>
                </div>
              </div>

              <button
                onClick={() => onRun(a.command_template)}
                className="flex items-center gap-1 px-2.5 py-1 rounded-md
                  bg-blue-600/0 group-hover:bg-blue-600 text-blue-400 group-hover:text-white
                  text-xs font-medium transition-all border border-blue-600/30 group-hover:border-transparent
                  shrink-0"
              >
                <Play className="w-3.5 h-3.5" /> Run
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
