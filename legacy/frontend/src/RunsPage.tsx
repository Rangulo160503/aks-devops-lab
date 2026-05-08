import { useCallback, useEffect, useState } from "react";
import { createRun, deleteRun, listRuns, Run } from "./api";

export function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

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
    if (!confirm("Ejecutar pipeline con merge_all=true? Puede tardar varios minutos."))
      return;
    setCreating(true);
    setError(null);
    try {
      await createRun({ merge_all: true });
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const onDelete = async (runId: string) => {
    if (!confirm(`¿Eliminar run ${runId}? Se borrarán sus artefactos.`)) return;
    try {
      await deleteRun(runId);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <section className="dashboard">
      <header className="dashboard__header">
        <h1>Runs Dashboard</h1>
        <div className="dashboard__actions">
          <button onClick={refresh} disabled={loading}>
            {loading ? "Cargando…" : "Refrescar"}
          </button>
          <button onClick={onCreate} disabled={creating} className="primary">
            {creating ? "Ejecutando…" : "Nueva ejecución (merge_all)"}
          </button>
        </div>
      </header>

      {error && <div className="alert-error">{error}</div>}

      <table className="runs-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Fecha</th>
            <th>Modelo</th>
            <th>WRMSE</th>
            <th>Dataset</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {runs.length === 0 && !loading && (
            <tr>
              <td colSpan={6} className="empty">
                No hay ejecuciones registradas.
              </td>
            </tr>
          )}
          {runs.map((r) => (
            <tr key={r.run_id}>
              <td>
                <strong>{r.nombre}</strong>
                <div className="muted">{r.run_id}</div>
              </td>
              <td>{r.fecha}</td>
              <td>{r.best_model ?? "—"}</td>
              <td>{r.wrmse !== null ? r.wrmse.toFixed(2) : "—"}</td>
              <td className="muted">{r.dataset}</td>
              <td>
                <button onClick={() => onDelete(r.run_id)} className="danger">
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
