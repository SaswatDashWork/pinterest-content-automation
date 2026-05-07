export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Execution {
  id: number;
  workflow_id: number | null;
  command: string;
  status: ExecutionStatus;
  plan: Step[] | null;
  steps_completed: number;
  total_steps: number;
  current_step: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  screenshots: string[];
  logs: string[];
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface Step {
  action: string;
  description?: string;
  [key: string]: unknown;
}

export interface ExecutionStep {
  id: number;
  execution_id: number;
  step_index: number;
  action: string;
  params: Record<string, unknown> | null;
  status: ExecutionStatus;
  result: Record<string, unknown> | null;
  error: string | null;
  screenshot: string | null;
  duration_ms: number | null;
}

export interface Workflow {
  id: number;
  name: string;
  description: string | null;
  command: string;
  plan: Step[] | null;
  created_at: string;
}

export interface SavedAutomation {
  id: number;
  name: string;
  description: string | null;
  command_template: string;
  tags: string[];
  use_count: number;
  success_rate: number;
  created_at: string;
}

export interface StreamEvent {
  type:
    | 'step_running'
    | 'step_completed'
    | 'step_failed'
    | 'execution_complete'
    | 'error';
  execution_id: number;
  step_index?: number;
  action?: string;
  description?: string;
  status?: string;
  result?: Record<string, unknown>;
  error?: string;
  screenshot?: string;
  progress?: number;
  timestamp?: string;
}
