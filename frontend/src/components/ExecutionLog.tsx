'use client';

import { useEffect, useRef } from 'react';
import { CheckCircle, XCircle, Loader2, Info, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import type { Execution, StreamEvent } from '@/types';

interface Props {
  execution: Execution | null;
  events: StreamEvent[];
  isRunning: boolean;
}

function EventRow({ event }: { event: StreamEvent }) {
  const ts = event.timestamp
    ? new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';

  const icon = () => {
    switch (event.type) {
      case 'step_completed':    return <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />;
      case 'step_failed':       return <XCircle     className="w-4 h-4 text-red-400 shrink-0" />;
      case 'step_running':      return <Loader2     className="w-4 h-4 text-blue-400 shrink-0 animate-spin" />;
      case 'execution_complete':
        return event.status === 'completed'
          ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
          : <XCircle     className="w-4 h-4 text-red-400 shrink-0" />;
      case 'error': return <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />;
      default:      return <Info          className="w-4 h-4 text-slate-400 shrink-0" />;
    }
  };

  const label = () => {
    if (event.type === 'execution_complete') {
      return event.status === 'completed'
        ? 'Execution completed successfully'
        : `Execution failed${event.error ? ': ' + event.error : ''}`;
    }
    if (event.type === 'error') return event.error ?? 'Unknown error';
    const parts: string[] = [];
    if (event.action) parts.push(`[${event.action}]`);
    if (event.description) parts.push(event.description);
    if (event.error) parts.push(`— ${event.error}`);
    return parts.join(' ') || event.type;
  };

  const rowCls = clsx('log-entry flex items-start gap-2.5 px-4 py-2 text-xs border-b border-slate-700/40 font-mono', {
    'bg-green-950/20': event.type === 'step_completed',
    'bg-red-950/20':   event.type === 'step_failed' || event.type === 'error',
    'bg-blue-950/10':  event.type === 'step_running',
    'bg-slate-800/40': event.type === 'execution_complete',
  });

  return (
    <div className={rowCls}>
      <span className="text-slate-500 shrink-0 mt-0.5 tabular-nums">{ts}</span>
      {icon()}
      <span className={clsx('leading-relaxed break-all', {
        'text-slate-300': event.type === 'step_running',
        'text-green-300': event.type === 'step_completed',
        'text-red-300':   event.type === 'step_failed' || event.type === 'error',
        'text-slate-200': event.type === 'execution_complete',
      })}>
        {event.step_index !== undefined && (
          <span className="text-slate-500 mr-1">Step {event.step_index + 1}:</span>
        )}
        {label()}
      </span>
    </div>
  );
}

export function ExecutionLog({ execution, events, isRunning }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  if (!execution && events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
        <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center">
          <Info className="w-6 h-6" />
        </div>
        <p className="text-sm">Enter a command above to start an automation</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Plan preview */}
      {execution?.plan && execution.plan.length > 0 && (
        <div className="px-4 py-2 border-b border-slate-700/50 bg-slate-800/30">
          <p className="text-xs text-slate-400 font-medium mb-1.5">Generated plan — {execution.plan.length} steps</p>
          <div className="flex flex-col gap-0.5 max-h-28 overflow-y-auto">
            {execution.plan.map((step, i) => {
              const done = i < execution.steps_completed;
              const active = i === execution.steps_completed && isRunning;
              return (
                <div key={i} className={clsx('flex items-center gap-2 text-xs py-0.5', {
                  'text-green-400': done,
                  'text-blue-300': active,
                  'text-slate-500': !done && !active,
                })}>
                  <span className="w-4 text-right shrink-0">{i + 1}.</span>
                  <span className="font-mono text-xs">[{step.action}]</span>
                  <span className="truncate">{step.description as string ?? ''}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Live log */}
      <div className="flex-1 overflow-y-auto">
        {events.map((ev, i) => <EventRow key={i} event={ev} />)}
        {isRunning && events.length === 0 && (
          <div className="flex items-center gap-2 px-4 py-3 text-xs text-slate-400 font-mono">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
            Planning and initialising browser…
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
