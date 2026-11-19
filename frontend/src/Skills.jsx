import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";

const short = (id) => id.replace(/^community\//, "");

function TryIt() {
  const [q, setQ] = useState("");
  const [profile, setProfile] = useState("coding");
  const [tier, setTier] = useState("local");
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  async function run(e) {
    e.preventDefault();
    setErr("");
    try { setRes(await api.skillPlan(q, profile, tier)); } catch (e2) { setErr(e2.message); setRes(null); }
  }
  return (
    <form className="add" onSubmit={run}>
      <h2>Try a question</h2>
      <p className="hint">See which skills would guide the answer, and which connected skills come along. Nothing is sent to an AI.</p>
      <label>Question<input value={q} onChange={(e) => setQ(e.target.value)} required placeholder="e.g. integrate Stripe payments webhooks" /></label>
      <div className="grid2">
        <label>Kind of task
          <select value={profile} onChange={(e) => setProfile(e.target.value)}>
            <option value="coding">Coding</option><option value="reasoning">Reasoning</option><option value="creative">Creative</option><option value="general">General</option>
          </select>
        </label>
        <label>Model
          <select value={tier} onChange={(e) => setTier(e.target.value)}>
            <option value="local">Local (Ollama): short prompt</option><option value="cloud">Hosted: fuller prompt</option>
          </select>
        </label>
      </div>
      <button className="btn small">Check</button>
      {err && <p className="error">{err}</p>}
      {res && (
        <div className="plan">
          {res.primary.length === 0 ? <p className="muted">No skill matches this question, so no skill text is added.</p> : (
            <>
              <p><b>Used:</b> {res.primary.map((s) => <span key={s.id} className="chip on">{short(s.id)}</span>)}</p>
              {res.linked.length > 0 && <p><b>Connected:</b> {res.linked.map((s) => <span key={s.id} className="chip" title={s.why}>{short(s.id)}</span>)}</p>}
              <p className="muted small">Adds about {res.prompt_chars.toLocaleString()} characters (≈ {Math.round(res.prompt_chars / 4).toLocaleString()} tokens) to the prompt.</p>
            </>
          )}
        </div>
      )}
    </form>
  );
}

function Install({ onDone }) {
  const [mode, setMode] = useState("paste");
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const [file, setFile] = useState(null);
  const [replace, setReplace] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  async function submit(e) {
    e.preventDefault();
    setBusy(true); setMsg(null);
    try {
      const r = await api.installSkill({ file: mode === "upload" ? file : null, name, content: mode === "paste" ? content : "", replace });
      setMsg({ ok: `Installed “${r.name}” (${r.files} file${r.files === 1 ? "" : "s"}). It is active now.` });
      setName(""); setContent(""); setFile(null); onDone();
    } catch (e2) { setMsg({ err: e2.message }); }
    setBusy(false);
  }
  return (
    <form className="add" onSubmit={submit}>
      <h2>Add a skill</h2>
      <div className="tabs" role="tablist">
        <button type="button" role="tab" aria-selected={mode === "paste"} className={mode === "paste" ? "tab active" : "tab"} onClick={() => setMode("paste")}>Paste SKILL.md</button>
        <button type="button" role="tab" aria-selected={mode === "upload"} className={mode === "upload" ? "tab active" : "tab"} onClick={() => setMode("upload")}>Upload .zip or SKILL.md</button>
      </div>
      <label>Name (optional, taken from the skill if empty)<input value={name} onChange={(e) => setName(e.target.value)} maxLength={60} placeholder="my-reports" /></label>
      {mode === "paste" ? (
        <label>SKILL.md text<textarea className="mono" rows={9} value={content} onChange={(e) => setContent(e.target.value)} required
          placeholder={"---\nname: my-reports\ndescription: Writes our weekly report in the company format.\n---\n\n# Weekly report\n..."} /></label>
      ) : (
        <label>File<input type="file" accept=".zip,.md" required onChange={(e) => setFile(e.target.files[0] || null)} /></label>
      )}
      <label className="check"><input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} />Replace a skill with the same name</label>
      <p className="hint">A skill is reference text for the AI. Nothing inside it is ever run. Zip files are checked for unsafe paths and limited to 8 MB.</p>
      <button className="btn" disabled={busy}>{busy ? "Installing…" : "Install"}</button>
      {msg?.ok && <p className="okc">{msg.ok}</p>}
      {msg?.err && <p className="error">{msg.err}</p>}
    </form>
  );
}

function Switch({ on, onChange, label }) {
  return <button type="button" role="switch" aria-checked={on} aria-label={label} className={on ? "switch on" : "switch"} onClick={() => onChange(!on)}><i /></button>;
}

function Installed({ data, reload }) {
  const [filter, setFilter] = useState("");
  const [open, setOpen] = useState({});
  const [err, setErr] = useState("");
  const groups = useMemo(() => {
    const m = new Map();
    for (const s of data.installed) {
      if (filter && !(s.id + s.description).toLowerCase().includes(filter.toLowerCase())) continue;
      if (!m.has(s.group)) m.set(s.group, []);
      m.get(s.group).push(s);
    }
    return [...m.entries()];
  }, [data, filter]);

  const flip = async (id, enabled) => { try { await api.setSkillState(id, enabled); reload(); } catch (e) { setErr(e.message); } };
  const remove = async (id) => {
    if (!window.confirm(`Remove “${short(id)}”? Its files are deleted from the server.`)) return;
    try { await api.removeSkill(id); reload(); } catch (e) { setErr(e.message); }
  };
  const used = (s) => s.usage?.used || 0;

  return (
    <>
      <div className="row between"><h2>Installed skills ({data.installed_count})</h2>
        <input className="filter" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search skills…" aria-label="Search skills" /></div>
      {err && <p className="error">{err}</p>}
      <ul className="docs skills">
        {groups.map(([group, items]) => {
          const bundle = items.length > 1 || items[0].id.split("/").length >= 3;
          if (!bundle) {
            const s = items[0];
            return (
              <li key={s.id} className={s.enabled ? "" : "off"}>
                <div><strong>{short(s.id)}</strong>{used(s) > 0 && <span className="tag">used {used(s)}×</span>}
                  <div className="muted small">{s.description.slice(0, 160)}</div></div>
                <div className="app-actions">
                  <Switch on={s.enabled} onChange={(v) => flip(s.id, v)} label={`Use ${s.name}`} />
                  {s.removable && <button className="link" onClick={() => remove(s.id)}>Remove</button>}
                </div>
              </li>
            );
          }
          const on = items.every((s) => s.enabled);
          return (
            <li key={group} className={`bundle ${on ? "" : "off"}`}>
              <div style={{ flex: 1 }}>
                <button className="link" onClick={() => setOpen((o) => ({ ...o, [group]: !o[group] }))} aria-expanded={!!open[group]}>
                  {open[group] ? "▾" : "▸"} <strong>{short(group)}</strong> <span className="tag">bundle · {items.length} skills</span>
                </button>
                {open[group] && (
                  <ul className="sub">
                    {items.map((s) => <li key={s.id}><b>{s.id.split("/").pop()}</b> <span className="muted small">{s.description.slice(0, 110)}</span>{used(s) > 0 && <span className="tag">used {used(s)}×</span>}</li>)}
                  </ul>
                )}
              </div>
              <div className="app-actions">
                <Switch on={on} onChange={(v) => flip(group, v)} label={`Use ${short(group)}`} />
                {items[0].removable && <button className="link" onClick={() => remove(group)}>Remove bundle</button>}
              </div>
            </li>
          );
        })}
      </ul>
    </>
  );
}

function Connections({ data, reload }) {
  const [graph, setGraph] = useState(null);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [why, setWhy] = useState("");
  const [err, setErr] = useState("");
  const options = useMemo(() => {
    const seen = new Map();
    for (const s of data.installed) if (!seen.has(s.group)) seen.set(s.group, s);
    return [...seen.values()].filter((s) => s.id.split("/").length < 3);
  }, [data]);
  useEffect(() => { api.skillGraph().then(setGraph).catch(() => setGraph(null)); }, [data]);

  async function add(e) {
    e.preventDefault();
    setErr("");
    try { await api.addSkillLink({ a, b, why }); setWhy(""); reload(); } catch (e2) { setErr(e2.message); }
  }
  const mine = new Set(data.links.map(([x, y]) => [x, y].sort().join("|")));
  return (
    <>
      <h2>Connections</h2>
      <p className="hint">When a question uses one skill, the skills linked to it come along as short companions. Links you add here come first.</p>
      <form className="add" onSubmit={add}>
        <div className="grid2">
          <label>Skill<select value={a} onChange={(e) => setA(e.target.value)} required><option value="">Choose…</option>{options.map((s) => <option key={s.id} value={s.id}>{short(s.id)}</option>)}</select></label>
          <label>Works together with<select value={b} onChange={(e) => setB(e.target.value)} required><option value="">Choose…</option>{options.filter((s) => s.id !== a).map((s) => <option key={s.id} value={s.id}>{short(s.id)}</option>)}</select></label>
        </div>
        <label>Why (shown to the AI)<input value={why} onChange={(e) => setWhy(e.target.value)} maxLength={160} placeholder="e.g. every report needs a chart" /></label>
        <button className="btn small">Connect skills</button>
        {err && <p className="error">{err}</p>}
      </form>
      {data.links.length > 0 && (
        <ul className="docs">
          {data.links.map(([x, y, w]) => (
            <li key={x + y}><div><strong>{short(x)}</strong> ↔ <strong>{short(y)}</strong><div className="muted small">{w}</div></div>
              <button className="link" onClick={() => api.deleteSkillLink(x, y).then(reload)}>Remove</button></li>
          ))}
        </ul>
      )}
      {graph && (
        <details className="graph">
          <summary>Built-in connections ({graph.links.filter((l) => !mine.has([l.from[0], l.to[0]].sort().join("|"))).length})</summary>
          <ul className="sub">
            {graph.links.map((l, i) => (
              <li key={i}><b>{short(l.from.length > 1 ? l.from[0].split("/").slice(0, 2).join("/") : l.from[0])}</b> ↔ <b>{short(l.to.length > 1 ? l.to[0].split("/").slice(0, 2).join("/") : l.to[0])}</b> <span className="muted small">{l.why}</span></li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}

export default function Skills() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const reload = () => api.skills().then(setData).catch((e) => setErr(e.message));
  useEffect(() => { reload(); }, []);
  return (
    <div className="page">
      <h1>Skills</h1>
      <p className="lead">Skills teach the AI how to do specific jobs well (payments, testing, databases, design, voice…). Matching skills are added to AI answers automatically, together with the skills connected to them.</p>
      {err && <p className="error">{err}</p>}
      <TryIt />
      {data && <Installed data={data} reload={reload} />}
      {data && <Connections data={data} reload={reload} />}
      <Install onDone={reload} />
    </div>
  );
}
