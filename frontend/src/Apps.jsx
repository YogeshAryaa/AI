import { useEffect, useState } from "react";
import { api } from "./api.js";
import { refreshApps } from "./Files.jsx";

function Fields({ spec, values, onChange, editing }) {
  return spec.fields.map((f) => {
    const v = values[f.key];
    if (f.kind === "bool") {
      return <label key={f.key} className="check"><input type="checkbox" checked={!!v} onChange={(e) => onChange(f.key, e.target.checked)} />{f.label}</label>;
    }
    if (f.kind === "select") {
      return (
        <label key={f.key}>{f.label}
          <select value={v ?? f.options[0]} onChange={(e) => onChange(f.key, e.target.value)}>{f.options.map((o) => <option key={o}>{o}</option>)}</select>
        </label>
      );
    }
    return (
      <label key={f.key}>{f.label}{f.optional ? " (optional)" : ""}
        <input type={f.secret ? "password" : "text"} value={v ?? ""} autoComplete="off" required={!f.optional && !(editing && f.secret)}
          placeholder={editing && f.secret ? "Leave empty to keep the saved value" : ""} onChange={(e) => onChange(f.key, e.target.value)} />
      </label>
    );
  });
}

function AddForm({ types, onAdded }) {
  const [type, setType] = useState(types[0]?.type || "webhook");
  const [name, setName] = useState("");
  const [values, setValues] = useState({});
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const spec = types.find((t) => t.type === type);
  async function submit(e) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await api.addApp({ name: name || spec.label.split(" (")[0], type, config: values });
      setName(""); setValues({}); refreshApps(); onAdded();
    } catch (e2) { setErr(e2.message); }
    setBusy(false);
  }
  return (
    <form className="add" onSubmit={submit}>
      <h2>Connect an app</h2>
      <div className="grid2">
        <label>App
          <select value={type} onChange={(e) => { setType(e.target.value); setValues({}); }}>
            {types.map((t) => <option key={t.type} value={t.type}>{t.label}</option>)}
          </select>
        </label>
        <label>Name (shown in “Send to…”)<input value={name} onChange={(e) => setName(e.target.value)} maxLength={60} placeholder={spec.label.split(" (")[0]} /></label>
      </div>
      <p className="hint">{spec.help}</p>
      <Fields spec={spec} values={values} onChange={(k, v) => setValues((s) => ({ ...s, [k]: v }))} />
      <button className="btn" disabled={busy}>{busy ? "Saving…" : "Connect"}</button>
      {err && <p className="error">{err}</p>}
    </form>
  );
}

function AppRow({ a, spec, reload }) {
  const [edit, setEdit] = useState(false);
  const [values, setValues] = useState({});
  const [state, setState] = useState(null);

  async function act(fn, okText) {
    setState({ busy: true });
    try { await fn(); setState(okText ? { ok: okText } : null); reload(); } catch (e) { setState({ err: e.message }); }
  }
  async function save(e) {
    e.preventDefault();
    await act(() => api.patchApp(a.id, { config: { ...a.config, ...values } }), "Saved");
    refreshApps(); setEdit(false); setValues({});
  }
  return (
    <li className={a.enabled ? "app-row" : "app-row off"}>
      <div className="app-main">
        <strong>{a.name}</strong> <span className="tag">{spec?.label.split(" (")[0] || a.type}</span>
        {!a.enabled && <span className="muted small"> · switched off</span>}
        <div className="muted small">
          {Object.entries(a.secrets).map(([k, v]) => `${k}: ${v}`).join(" · ")}
          {Object.entries(a.config).filter(([, v]) => v !== false && v !== "").map(([k, v]) => ` · ${k}: ${v === true ? "yes" : v}`).join("")}
        </div>
        {a.last_error && <div className="error small">Last problem: {a.last_error}</div>}
        {state?.ok && <div className="okc small">{state.ok}</div>}
        {state?.err && <div className="error small">{state.err}</div>}
        {edit && spec && (
          <form className="stack edit-form" onSubmit={save}>
            <Fields spec={spec} values={{ ...a.config, ...values }} editing onChange={(k, v) => setValues((s) => ({ ...s, [k]: v }))} />
            <div className="row"><button className="btn small">Save</button><button type="button" className="link" onClick={() => setEdit(false)}>Cancel</button></div>
          </form>
        )}
      </div>
      <div className="app-actions">
        <button className="btn small ghost" onClick={() => act(() => api.testApp(a.id), "Test message sent")} disabled={state?.busy || !a.enabled}>Send test</button>
        <button className="link" onClick={() => setEdit(!edit)}>Edit</button>
        <button className="link" onClick={() => act(() => api.patchApp(a.id, { enabled: !a.enabled }).then(refreshApps))}>{a.enabled ? "Switch off" : "Switch on"}</button>
        <button className="link" onClick={() => window.confirm(`Remove “${a.name}”?`) && act(() => api.deleteApp(a.id).then(refreshApps))}>Remove</button>
      </div>
    </li>
  );
}

export default function Apps() {
  const [types, setTypes] = useState(null);
  const [list, setList] = useState([]);
  const [err, setErr] = useState("");
  const reload = () => api.apps().then((r) => setList(r.apps)).catch((e) => setErr(e.message));
  useEffect(() => { api.appTypes().then((r) => setTypes(r.types)).catch((e) => setErr(e.message)); reload(); }, []);
  return (
    <div className="page">
      <h1>Send to apps</h1>
      <p className="lead">Connect Slack, Discord, Telegram, email or any webhook (Zapier, n8n, Make). Then every PDF, Word and Excel file shows a “Send to an app…” link, and you can send reports without downloading them first.</p>
      {err && <p className="error">{err}</p>}
      {list.length === 0 ? <p className="empty-note">No apps connected yet.</p> : (
        <ul className="docs apps">{list.map((a) => <AppRow key={a.id} a={a} spec={types?.find((t) => t.type === a.type)} reload={reload} />)}</ul>
      )}
      {types && <AddForm types={types} onAdded={reload} />}
      <p className="hint">Secrets (webhook addresses, tokens, passwords) are stored encrypted and never shown again. Addresses that point to private or local networks are refused unless the server setting ALLOW_PRIVATE_APP_URLS is on.</p>
    </div>
  );
}
