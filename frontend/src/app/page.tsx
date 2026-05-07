'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { CommandInput } from '@/components/CommandInput';
import { ExecutionLog } from '@/components/ExecutionLog';
import { BrowserPreview } from '@/components/BrowserPreview';
import { WorkflowHistory } from '@/components/WorkflowHistory';
import { SavedAutomations } from '@/components/SavedAutomations';
import { StatusBadge } from '@/components/StatusBadge';
import { startExecution, getExecution, streamExecution, listExecutions } from '@/lib/api';
import type { Execution, StreamEvent } from '@/types';
import { Bot, Activity, History, Bookmark } from 'lucide-react';

type Tab = 'log' | 'history' | 'saved';

export default function Dashboard() {
  const [activeExecution, setActiveExecution] = useState<Execution | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [latestScreenshot, setLatestScreenshot] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [tab, setTab] = useState<Tab>('log');
  const [recentExecutions, setRecentExecutions] = useState<Execution[]>([]);
  const cleanupRef = useRef<(() => void) | null>(null);

  const loadHistory = useCallback(async () => {
    try {
      const execs = await listExecutions(10);
      setRecentExecutions(execs);
    } catch {
      // non-critical
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleCommand = useCallback(async (command: string) => {
    if (isRunning) return;

    // Clean up any previous stream
    cleanupRef.current?.();
    setEvents([]);
    setLatestScreenshot(null);
    setIsRunning(true);
    setTab('log');

    try {
      const execution = await startExecution(command);
      setActiveExecution(execution);

      const cleanup = streamExecution(
        execution.id,
        (event) => {
          setEvents((prev) => [...prev, event]);

          if (event.screenshot) {
            setLatestScreenshot(event.screenshot);
          }

          if (event.type === 'execution_complete') {
            setIsRunning(false);
            // Refresh execution record with final state
            getExecution(execution.id)
              .then(setActiveExecution)
              .catch(() => null);
            loadHistory();
          }
        },
        () => setIsRunning(false),
      );

      cleanupRef.current = cleanup;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to start execution';
      setEvents([{
        type: 'error',
        execution_id: 0,
        error: msg,
        timestamp: new Date().toISOString(),
      }]);
      setIsRunning(false);
    }
  }, [isRunning, loadHistory]);

  const handleSelectExecution = useCallback((exec: Execution) => {
    setActiveExecution(exec);
    setTab('log');
    setEvents([]);
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-700/50 bg-slate-900/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100 leading-none">AI Browser Agent</h1>
            <p className="text-xs text-slate-400 mt-0.5">Natural language → browser actions</p>
          </div>
        </div>

        {activeExecution && (
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-400">
              Execution <span className="text-slate-200 font-mono">#{activeExecution.id}</span>
            </span>
            <StatusBadge status={activeExecution.status} />
            {activeExecution.total_steps > 0 && (
              <span className="text-slate-400">
                {activeExecution.steps_completed}/{activeExecution.total_steps} steps
              </span>
            )}
          </div>
        )}
      </header>

      {/* Command bar */}
      <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/40">
        <CommandInput onSubmit={handleCommand} isRunning={isRunning} />
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — logs / history / saved */}
        <div className="flex flex-col w-1/2 border-r border-slate-700/50 overflow-hidden">
          {/* Tab bar */}
          <div className="flex items-center gap-1 px-4 py-2 border-b border-slate-700/50">
            {([
              { id: 'log' as Tab, label: 'Execution Log', icon: Activity },
              { id: 'history' as Tab, label: 'History', icon: History },
              { id: 'saved' as Tab, label: 'Saved', icon: Bookmark },
            ] as const).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  tab === id
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden">
            {tab === 'log' && (
              <ExecutionLog
                execution={activeExecution}
                events={events}
                isRunning={isRunning}
              />
            )}
            {tab === 'history' && (
              <WorkflowHistory
                executions={recentExecutions}
                onSelect={handleSelectExecution}
              />
            )}
            {tab === 'saved' && (
              <SavedAutomations onRun={handleCommand} />
            )}
          </div>
        </div>

        {/* Right panel — browser preview */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <BrowserPreview
            screenshotPath={latestScreenshot}
            execution={activeExecution}
            isRunning={isRunning}
          />
        </div>
      </div>
    </div>
  );
}
