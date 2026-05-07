import type { ExecutionStatus } from '@/types';
import clsx from 'clsx';

const MAP: Record<ExecutionStatus, { label: string; cls: string; dot: string }> = {
  pending:   { label: 'Pending',   cls: 'bg-slate-700 text-slate-300',  dot: 'bg-slate-400' },
  running:   { label: 'Running',   cls: 'bg-blue-900/60 text-blue-300', dot: 'bg-blue-400 blink' },
  completed: { label: 'Completed', cls: 'bg-green-900/60 text-green-300', dot: 'bg-green-400' },
  failed:    { label: 'Failed',    cls: 'bg-red-900/60 text-red-300',   dot: 'bg-red-400' },
};

export function StatusBadge({ status }: { status: ExecutionStatus }) {
  const { label, cls, dot } = MAP[status] ?? MAP.pending;
  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium', cls)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', dot)} />
      {label}
    </span>
  );
}
