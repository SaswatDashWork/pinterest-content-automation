'use client';

import { useState, useEffect } from 'react';
import { Monitor, Loader2, ImageOff, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import type { Execution } from '@/types';
import { StatusBadge } from './StatusBadge';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface Props {
  screenshotPath: string | null;
  execution: Execution | null;
  isRunning: boolean;
}

export function BrowserPreview({ screenshotPath, execution, isRunning }: Props) {
  const [imgError, setImgError] = useState(false);
  const [zoom, setZoom] = useState(false);

  // Reset error when screenshot changes
  useEffect(() => { setImgError(false); }, [screenshotPath]);

  // Derive a URL the browser can load
  const imgUrl = screenshotPath
    ? `${API}/screenshots/${screenshotPath.replace(/.*\/screenshots\//, '')}`
    : null;

  return (
    <div className="flex flex-col h-full bg-slate-900/30">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700/50">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Monitor className="w-4 h-4" />
          <span className="font-medium">Browser Preview</span>
          {isRunning && (
            <span className="flex items-center gap-1 text-blue-400">
              <Loader2 className="w-3 h-3 animate-spin" /> Live
            </span>
          )}
        </div>
        {execution && <StatusBadge status={execution.status} />}
      </div>

      {/* Progress bar */}
      {execution && execution.total_steps > 0 && (
        <div className="w-full h-0.5 bg-slate-700">
          <div
            className="h-0.5 bg-blue-500 transition-all duration-500"
            style={{ width: `${(execution.steps_completed / execution.total_steps) * 100}%` }}
          />
        </div>
      )}

      {/* Screenshot area */}
      <div
        className={clsx(
          'flex-1 flex items-center justify-center overflow-hidden bg-slate-950 relative',
          zoom && 'cursor-zoom-out',
          !zoom && imgUrl && 'cursor-zoom-in',
        )}
        onClick={() => imgUrl && setZoom((z) => !z)}
      >
        {isRunning && !imgUrl && (
          <div className="flex flex-col items-center gap-3 text-slate-500">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-2 border-slate-700" />
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 absolute inset-0 m-auto" />
            </div>
            <p className="text-sm">Browser is running…</p>
          </div>
        )}

        {imgUrl && !imgError && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imgUrl}
            alt="Latest browser screenshot"
            className={clsx(
              'object-contain transition-all duration-300',
              zoom ? 'w-full h-full' : 'max-w-full max-h-full',
            )}
            onError={() => setImgError(true)}
          />
        )}

        {imgError && (
          <div className="flex flex-col items-center gap-2 text-slate-500">
            <ImageOff className="w-8 h-8" />
            <p className="text-sm">Screenshot unavailable</p>
          </div>
        )}

        {!isRunning && !imgUrl && !execution && (
          <div className="flex flex-col items-center gap-3 text-slate-600">
            <Monitor className="w-16 h-16" />
            <p className="text-sm">No browser activity yet</p>
          </div>
        )}

        {/* Zoom hint */}
        {imgUrl && !imgError && (
          <div className="absolute bottom-2 right-2 text-xs text-slate-600 bg-slate-900/80 px-2 py-0.5 rounded">
            {zoom ? 'Click to fit' : 'Click to zoom'}
          </div>
        )}
      </div>

      {/* Current step footer */}
      {execution?.current_step && (
        <div className="px-4 py-2 border-t border-slate-700/50 text-xs text-slate-400 font-mono truncate">
          <span className="text-slate-500 mr-2">Current:</span>
          {execution.current_step}
        </div>
      )}
    </div>
  );
}
