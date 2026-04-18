import { RunsPage } from "./RunsPage";

export default function App() {
  return (
    <main className="app-shell">
      <RunsPage />
      <footer className="app-footer">
        Proyecto ML · Frontend React/TS · API{" "}
        <code>/api/v1/runs</code>
      </footer>
    </main>
  );
}
