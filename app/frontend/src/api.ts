import { API_BASE } from "./config";

export interface Run {
  run_id: string;
  nombre: string;
  best_model: string;
  wrmse: number;
  source_mode: string;
  source_file: string;
  created_at: string | null;
}

export interface ApiEnvelope<T> {
  ok: boolean;
  error?: string;
  run?: T;
  runs?: T[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${msg}`);
  }
  return res.json() as Promise<T>;
}

export async function listRuns(): Promise<Run[]> {
  const res = await fetch(`${API_BASE}/v1/runs`, {
    headers: { Accept: "application/json" },
  });
  const data = await handle<ApiEnvelope<Run>>(res);
  return data.runs ?? [];
}

export async function createRun(body: {
  nombre?: string;
  source_mode?: string;
  source_file?: string;
}): Promise<Run> {
  const res = await fetch(`${API_BASE}/v1/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await handle<ApiEnvelope<Run>>(res);
  if (!data.run) throw new Error("API did not return a run");
  return data.run;
}

export async function deleteRun(runId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE}/v1/runs/${encodeURIComponent(runId)}`,
    { method: "DELETE" }
  );
  await handle<ApiEnvelope<Run>>(res);
}

export async function getServiceMeta(): Promise<{
  service: string;
  version: string;
  env: string;
  color: string;
}> {
  const res = await fetch(API_BASE.replace(/\/api$/, "") || "/", {
    headers: { Accept: "application/json" },
  });
  return handle(res);
}
