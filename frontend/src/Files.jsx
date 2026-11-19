import { useEffect, useState } from "react";
import { api, fileUrl } from "./api.js";

export const kb = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

const ICON = { pdf: "PDF", docx: "DOC", xlsx: "XLS" };

// Connected apps (Slack, email, ...) the user can send a file to. Fetched once; only the admin token can list them.
let appsCache = null;
export const refreshApps = () => { appsCache = null; };
export function useApps() {
  const [list, setList] = useState([]);
  useEffect(() => {
    let alive = true;
    if (!appsCache) appsCache = api.apps().then((r) => r.apps.filter((a) => a.enabled)).catch(() => []);
    appsCache.then((a) => alive && setList(a));
    return () => { alive = false; };
  }, []);
  return list;
}

function SendTo({ f, apps }) {
  const [open, setOpen] = useState(false);
  const [id, setId] = useState(apps[0]?.id || "");
  const [text, setText] = useState("");
  const [state, setState] = useState(null);
  if (!apps.length) return null;
  async function send() {
    setState({ busy: true });
    try {
      await api.sendApp(id || apps[0].id, { file_id: f.id, text });
      setState({ ok: `Sent to ${apps.find((a) => a.id === (id || apps[0].id))?.name}` });
    } catch (e) {
      setState({ err: e.message });
    }
  }
  return (
    <div className="send-row">
      {!open ? (
        <button type="button" className="link" onClick={() => setOpen(true)}>Send to an app…</button>
      ) : (
        <div className="send-box">
          <div className="row">
            <select value={id || apps[0].id} onChange={(e) => setId(e.target.value)} aria-label="App">
              {apps.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.type})</option>)}
            </select>
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Message (optional)" aria-label="Message" />
            <button type="button" className="btn small" onClick={send} disabled={state?.busy}>{state?.busy ? "Sending…" : "Send"}</button>
            <button type="button" className="link" onClick={() => { setOpen(false); setState(null); }}>Close</button>
          </div>
          {state?.ok && <p className="okc small">{state.ok}</p>}
          {state?.err && <p className="error">{state.err}</p>}
        </div>
      )}
    </div>
  );
}

// A file the backend made (PDF / Word / Excel / image). Fetched with the auth header and shown through a blob URL.
// preview: also show a PDF inline.
export function FileCard({ f, preview = false, onDelete = null }) {
  const [url, setUrl] = useState(null);
  const [err, setErr] = useState(null);
  const apps = useApps();
  useEffect(() => {
    let u = null, alive = true;
    setUrl(null);
    fileUrl(f.url).then((x) => { u = x; if (alive) setUrl(x); else URL.revokeObjectURL(x); }).catch((e) => alive && setErr(e.message));
    return () => { alive = false; if (u) URL.revokeObjectURL(u); };
  }, [f.url]);
  const isImage = f.kind === "image";
  const isVideo = f.kind === "video";
  const canOpen = f.kind === "pdf" || isVideo;
  return (
    <div className={`file-card ${f.kind} ${preview ? "wide" : ""}`}>
      {isImage && (url ? <a href={url} target="_blank" rel="noreferrer"><img src={url} alt={f.name} /></a>
        : !err && <div className="img-wait" aria-label="Loading image" />)}
      {isVideo && url && <video className="video-preview" src={url} controls preload="metadata" aria-label={f.name} />}
      {f.kind === "pdf" && preview && url && <iframe className="pdf-view" src={url} title={f.name} />}
      <div className="file-row">
        {!isImage && <span className={`file-icon ${f.kind}`} aria-hidden="true">{ICON[f.kind] || "FILE"}</span>}
        <span className="file-name" title={f.name}>{f.label && <b className="file-label">{f.label}</b>}{f.name}<small>{kb(f.size)}</small></span>
        {url && canOpen && <a className="btn small ghost" href={url} target="_blank" rel="noreferrer">Open</a>}
        {url && <a className="btn small" href={url} download={f.name}>Download</a>}
        {onDelete && <button type="button" className="link" onClick={() => onDelete(f)} title="Delete this file">Delete</button>}
      </div>
      {!isImage && <SendTo f={f} apps={apps} />}
      {err && <p className="error">{err}</p>}
    </div>
  );
}
