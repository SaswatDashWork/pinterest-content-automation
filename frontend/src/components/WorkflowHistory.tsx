'use client';

import { formatDistanceToNow } from 'date-fns';
import { Clock, CheckCircle, XCircle, Loader2, Circle } from 'lucide-react';
import clsx from 'clsx';
import type { Execution } from '@/types';
import { StatusBadge } from './StatusBadge';

interface Props {
  executions: Execution[];
  onSelect: (exec: Execution) => void;
}

function relativeTime(iso: string) {
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true });
  } catch {
    return iso;
  }
}

function StatusIcon({ status }: { status: Execution['status'] }) {
  switch (status) {
    case 'completed': return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'failed':    return <XCircle     className="w-4 h-4 text-red-400" />;
    case 'running':   return <Loader2     className="w-4 h-4 text-blue-400 animate-spin" />;
    default:          return <Circle      className="w-4 h-4 text-slate-500" />;
  }
}

export function WorkflowHistory({ executions, onSelect }: Props) {
  if (executions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
        <Clock className="w-8 h-8" />
        <p className="text-sm">No executions yet</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col overflow-y-auto h-full divide-y divide-slate-700/50">
      {executions.map((exec) => (
        <button
          key={exec.id}
          onClick={() => onSelect(exec)}
          className="flex items-start gap-3 px-4 py-3 text-left hover:bg-slate-700/30 transition-colors"
        >
          <StatusIcon status={exec.status} />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-200 truncate leading-snug">{exec.command}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-slate-500">
                {relativeTime(exec.created_at)}
              </span>
              {exec.total_steps > 0 && (
                <span className="text-xs text-slate-500">
                  · {exec.steps_completed}/{exec.total_steps} steps
                </span>
              )}
              {exec.error && (
                <span className="text-xs text-red-400 truncate max-w-[18ch]">{exec.error}</span>
              )}
            </div>
          </div>
          <StatusBadge status={exec.status} />
        </button>
      ))}
    </div>
  );
}
