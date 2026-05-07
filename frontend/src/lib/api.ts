import axios from 'axios';
import type { Execution, ExecutionStep, Workflow, SavedAutomation, StreamEvent } from '@/types';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const http = axios.create({ baseURL: BASE, timeout: 30_000 });

// ─── Executions ───────────────────────────────────────────────────────────────────────

export async function startExecution(command: string, workflowId?: number): Promise<Execution> {
  const { data } = await http.post<Execution>('/api/executions/', {
    command,
    workflow_id: workflowId ?? null,
  });
  return data;
}

export async function listExecutions(limit = 20): Promise<Execution[]> {
  const { data } = await http.get<Execution[]>('/api/executions/', { params: { limit } });
  return data;
}

export async function getExecution(id: number): Promise<Execution> {
  const { data } = await http.get<Execution>(`/api/executions/${id}`);
  return data;
}

export async function getExecutionSteps(id: number): Promise<ExecutionStep[]> {
  const { data } = await http.get<ExecutionStep[]>(`/api/executions/${id}/steps`);
  return data;
}

// ─── Workflows ────────────────────────────────────────────────────────────────────────

export async function listWorkflows(): Promise<Workflow[]> {
  const { data } = await http.get<Workflow[]>('/api/workflows/');
  return data;
}

export async function createWorkflow(
  name: string,
  command: string,
  description?: string,
): Promise<Workflow> {
  const { data } = await http.post<Workflow>('/api/workflows/', { name, command, description });
  return data;
}

export async function deleteWorkflow(id: number): Promise<void> {
  await http.delete(`/api/workflows/${id}`);
}

// ─── Automations ────────────────────────────────────────────────────────────────────

export async function listAutomations(): Promise<SavedAutomation[]> {
  const { data } = await http.get<SavedAutomation[]>('/api/automations/');
  return data;
}

export async function createAutomation(
  name: string,
  commandTemplate: string,
  description?: string,
  tags?: string[],
): Promise<SavedAutomation> {
  const { data } = await http.post<SavedAutomation>('/api/automations/', {
    name,
    command_template: commandTemplate,
    description,
    tags: tags ?? [],
  });
  return data;
}

// ─── SSE stream ──────────────────────────────────────────────────────────────────────

export function streamExecution(
  executionId: number,
  onEvent: (event: StreamEvent) => void,
  onClose?: () => void,
): () => void {
  const url = `${BASE}/api/executions/${executionId}/stream`;
  const es = new EventSource(url);

  es.onmessage = (e) => {
    try {
      const event: StreamEvent = JSON.parse(e.data);
      onEvent(event);
      if (event.type === 'execution_complete') {
        es.close();
        onClose?.();
      }
    } catch {
      // ignore malformed SSE frames
    }
  };

  es.onerror = () => {
    es.close();
    onClose?.();
  };

  // Return cleanup function
  return () => es.close();
}
