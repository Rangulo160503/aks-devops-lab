import { useCallback, useEffect, useState } from "react";
import { createRun, deleteRun, listRuns, Run } from "./api";
import { APP_VERSION } from "./config";

export default function App() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRuns(await listRuns());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      await createRun({});
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const onDelete = async (runId: string) => {
    setError(null);
    try {
      await deleteRun(runId);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <main className="shell">
      <header className="topbar">
        <h1>Proyecto ML — DevOps Lab</h1>
        <div className="actions">
          <button onClick={refresh} disabled={loading}>
            {loading ? "Loading…" : "Refresh"}
          </button>
          <button onClick={onCreate} disabled={creating} className="primary">
            {creating ? "Running…" : "New run"}
          </button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <table className="runs">
        <thead>
          <tr>
            <th>Name</th>
            <th>Created</th>
            <th>Model</th>
            <th>WRMSE</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {runs.length === 0 && !loading && (
            <tr>
              <td colSpan={5} className="empty">
                No runs yet. Click "New run" to invoke the stub pipeline.
              </td>
            </tr>
          )}
          {runs.map((r) => (
            <tr key={r.run_id}>
              <td>
                <strong>{r.nombre}</strong>
                <div className="muted">{r.run_id}</div>
              </td>
              <td>{r.created_at?.replace("T", " ").slice(0, 19) ?? "—"}</td>
              <td>{r.best_model}</td>
              <td>{r.wrmse.toFixed(2)}</td>
              <td>
                <button onClick={() => onDelete(r.run_id)} className="danger">
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <footer className="foot">
        SPA <code>v{APP_VERSION}</code> · API <code>/api/v1/runs</code>
      </footer>
    </main>
  );
}
