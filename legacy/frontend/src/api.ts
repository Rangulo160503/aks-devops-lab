export interface Run {
  id: string;
  run_id: string;
  nombre: string;
  timestamp: string;
  fecha: string;
  best_model: string | null;
  wrmse: number | null;
  source_mode: string;
  source_file: string;
  dataset: string;
  is_active: boolean;
}

export interface ApiEnvelope<T> {
  ok: boolean;
  error?: string;
  runs?: Run[];
  [k: string]: unknown;
  data?: T;
}

const BASE = "/api/v1/runs";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${msg}`);
  }
  return res.json() as Promise<T>;
}

export async function listRuns(): Promise<Run[]> {
  const res = await fetch(BASE, { headers: { Accept: "application/json" } });
  const data = await handle<{ ok: boolean; runs: Run[] }>(res);
  return data.runs ?? [];
}

export async function createRun(
  body: { merge_all?: boolean; dataset?: string; nombre?: string }
): Promise<ApiEnvelope<unknown>> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handle<ApiEnvelope<unknown>>(res);
}

export async function deleteRun(runId: string): Promise<ApiEnvelope<unknown>> {
  const res = await fetch(`${BASE}/${encodeURIComponent(runId)}`, {
    method: "DELETE",
  });
  return handle<ApiEnvelope<unknown>>(res);
}

export async function renameRun(
  runId: string,
  nombre: string
): Promise<ApiEnvelope<unknown>> {
  const res = await fetch(`${BASE}/${encodeURIComponent(runId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre }),
  });
  return handle<ApiEnvelope<unknown>>(res);
}
