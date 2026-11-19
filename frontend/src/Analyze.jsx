import { useEffect, useState } from "react";
import { api } from "./api.js";
import { FileCard } from "./Files.jsx";

const FORMATS = [["xlsx", "Excel (summary, charts, data)"], ["docx", "Word report"], ["pdf", "PDF report"]];
const fmt = (x) => (x === null || x === undefined ? "" : Math.abs(x) >= 1000 ? Math.round(x).toLocaleString() : String(Math.round(x * 100) / 100));

function Bars({ rows, valueKey, label }) {
  const max = Math.max(...rows.map((r) => r[valueKey] || 0), 1);
  return (
    <ul className="bars" aria-label={label}>
      {rows.map((r) => (
        <li key={r.key}>
          <span className="bar-label" title={r.key}>{r.key}</span>
          <span className="bar-track"><i style={{ width: `${Math.max(2, ((r[valueKey] || 0) / max) * 100)}%` }} /></span>
          <span className="bar-val">{fmt(r[valueKey])}</span>
        </li>
      ))}
    </ul>
  );
}

function Result({ r }) {
  const p = r.profile;
  const g = p.group;
  const nums = p.columns.filter((c) => c.stats);
  return (
    <div className="stack analyze-result">
      <h2>{r.title}</h2>
      <div className="stat-grid">
        <div><b>{p.rows.toLocaleString()}</b><span>rows</span></div>
        <div><b>{p.column_count}</b><span>columns</span></div>
        <div><b>{p.duplicates.toLocaleString()}</b><span>duplicate rows</span></div>
        <div><b>{p.missing_pct}%</b><span>empty cells</span></div>
      </div>
      <h3>Key findings</h3>
      <ul className="findings">{p.insights.map((t, i) => <li key={i}>{t}</li>)}</ul>
      {r.ai && <><h3>AI commentary</h3><div className="ai-note text">{r.ai}</div></>}
      {r.ai_error && <p className="warn small">{r.ai_error}</p>}
      {g && g.rows.length > 0 && (
        <>
          <h3>{g.value ? `Total ${g.value}` : "Rows"} by {g.by}</h3>
          <Bars rows={g.rows} valueKey={g.value ? "sum" : "count"} label={`By ${g.by}`} />
        </>
      )}
      {nums.length > 0 && (
        <>
          <h3>Numbers</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Column</th><th>Sum</th><th>Average</th><th>Median</th><th>Min</th><th>Max</th><th>Unusual</th></tr></thead>
              <tbody>
                {nums.map((c) => (
                  <tr key={c.name}><td>{c.name}</td><td>{fmt(c.stats.sum)}</td><td>{fmt(c.stats.mean)}</td><td>{fmt(c.stats.median)}</td><td>{fmt(c.stats.min)}</td><td>{fmt(c.stats.max)}</td><td>{c.stats.outliers}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      <h3>Columns</h3>
      <div className="table-wrap">
        <table className="data-table">
          <thead><tr><th>Column</th><th>Type</th><th>Filled</th><th>Empty %</th><th>Unique</th><th>Most common</th></tr></thead>
          <tbody>
            {p.columns.map((c) => (
              <tr key={c.name}>
                <td>{c.name}</td><td>{c.type}</td><td>{c.filled.toLocaleString()}</td>
                <td className={c.missing_pct >= 5 ? "warn" : ""}>{c.missing_pct}</td><td>{c.unique.toLocaleString()}</td>
                <td>{(c.top || []).slice(0, 3).map((t) => `${t.value} (${t.pct}%)`).join(", ")}{c.range ? `${c.range.from} → ${c.range.to}` : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {r.files.length > 0 && <h3>Your reports</h3>}
      <div className="stack">{r.files.map((f) => <FileCard key={f.id} f={f} />)}</div>
    </div>
  );
}

export default function Analyze() {
  const [source, setSource] = useState("file");
  const [file, setFile] = useState(null);
  const [over, setOver] = useState(false);
  const [dbs, setDbs] = useState(null);
  const [database, setDatabase] = useState("");
  const [cols, setCols] = useState([]);
  const [col, setCol] = useState("");
  const [formats, setFormats] = useState(["xlsx", "docx"]);
  const [ai, setAi] = useState(false);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (source !== "collection" || dbs) return;
    api.databases().then((d) => { setDbs(d); setDatabase(d.default); }).catch((e) => setErr(e.message));
  }, [source, dbs]);
  useEffect(() => {
    if (!database) return;
    setCol("");
    api.collections(database).then(setCols).catch((e) => setErr(e.message));
  }, [database]);

  const toggle = (f) => setFormats((s) => (s.includes(f) ? s.filter((x) => x !== f) : [...s, f]));
  const ready = source === "file" ? !!file : !!col;

  async function run(e) {
    e.preventDefault();
    setBusy(true); setErr(""); setResult(null);
    try {
      const opts = { formats, ai, question };
      setResult(source === "file"
        ? await api.analyzeFile(file, opts)
        : await api.analyzeCollection({ collection: col, database: dbs && database !== dbs.default ? database : undefined, ...opts }));
    } catch (e2) {
      setErr(e2.message);
    }
    setBusy(false);
  }

  return (
    <div className="page wide">
      <h1>Analyze data</h1>
      <p className="lead">Upload an Excel or CSV file, or pick one of your MongoDB collections. You get the findings here and ready-made Excel, Word or PDF reports. The numbers are calculated on your server.</p>
      <form className="add" onSubmit={run}>
        <div className="tabs" role="tablist">
          <button type="button" role="tab" aria-selected={source === "file"} className={source === "file" ? "tab active" : "tab"} onClick={() => setSource("file")}>Excel / CSV file</button>
          <button type="button" role="tab" aria-selected={source === "collection"} className={source === "collection" ? "tab active" : "tab"} onClick={() => setSource("collection")}>My database</button>
        </div>
        {source === "file" ? (
          <label className={`drop ${over ? "over" : ""}`} onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); setFile(e.dataTransfer.files[0] || null); }}>
            <strong>{file ? file.name : "Drop a file here, or click to choose"}</strong>
            <span className="hint">.xlsx, .csv, .tsv, .json or .jsonl · the first row holds the column names</span>
            <input type="file" accept=".xlsx,.csv,.tsv,.json,.jsonl,.ndjson" hidden onChange={(e) => setFile(e.target.files[0] || null)} />
          </label>
        ) : (
          <div className="grid2">
            <label>Database
              <select value={database} onChange={(e) => setDatabase(e.target.value)}>
                {(dbs?.databases || []).map((d) => <option key={d}>{d}</option>)}
              </select>
            </label>
            <label>Collection
              <select value={col} onChange={(e) => setCol(e.target.value)}>
                <option value="">Choose…</option>
                {cols.map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
          </div>
        )}
        <fieldset className="formats">
          <legend>Make these reports</legend>
          {FORMATS.map(([k, label]) => (
            <label key={k} className="check"><input type="checkbox" checked={formats.includes(k)} onChange={() => toggle(k)} />{label}</label>
          ))}
        </fieldset>
        <label className="check"><input type="checkbox" checked={ai} onChange={(e) => setAi(e.target.checked)} />Add AI commentary (slower; the AI sees only the totals and top values, never your rows)</label>
        {ai && <label>Question for the AI (optional)<input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g. Which city should we hire in?" maxLength={500} /></label>}
        <button className="btn" disabled={busy || !ready}>{busy ? "Analyzing…" : "Analyze"}</button>
        {err && <p className="error">{err}</p>}
      </form>
      {result && <Result r={result} />}
    </div>
  );
}
