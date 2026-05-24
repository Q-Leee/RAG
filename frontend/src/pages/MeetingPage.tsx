import { FormEvent, useState } from "react";
import { api } from "../api/client";
import LoadingPanel from "../components/LoadingPanel";

export default function MeetingPage() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [actions, setActions] = useState<{ task: string; owner: string | null; due: string | null }[]>(
    []
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file && !text.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.summarizeMeeting({
        file: file ?? undefined,
        text: text.trim() || undefined,
        useLlm: true,
      });
      setSummary(res.summary);
      setActions(res.action_items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Summarize failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <section className="card">
        <h2>Meeting summary + action items</h2>
        <p className="muted">
          Paste notes or upload PDF, Word (.docx), Excel (.xlsx), or .txt.
        </p>
        <form onSubmit={submit} className="stack">
          <label>
            File (optional)
            <input
              type="file"
              accept=".pdf,.docx,.xlsx,.txt"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <label>
            Or paste transcript
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              placeholder="Meeting notes…"
            />
          </label>
          <button type="submit" className="btn primary" disabled={busy}>
            {busy ? "Summarizing…" : "Summarize"}
          </button>
          {busy && (
            <LoadingPanel
              label="Summarizing meeting"
              sublabel="Extracting text and generating summary + action items…"
            />
          )}
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      {summary && (
        <section className="card highlight">
          <h3>Summary</h3>
          <p>{summary}</p>
        </section>
      )}

      {actions.length > 0 && (
        <section className="card">
          <h3>Action items</h3>
          <ul className="actions">
            {actions.map((a, i) => (
              <li key={i}>
                <strong>{a.task}</strong>
                {(a.owner || a.due) && (
                  <span className="muted">
                    {a.owner && ` · ${a.owner}`}
                    {a.due && ` · due ${a.due}`}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
