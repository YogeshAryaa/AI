# Word, Excel, data analysis, connected apps and skills in the frontend (v2.6)

## 1. Word and Excel files in the chat

Ask in the chat, in English or Hinglish:

- “make a Word file on our leave policy” / “leave policy word mein bana do”
- “candidates by city ka Excel bana do”, “export our open jobs to Excel”
- after any answer: “iska Excel bana do”, “make this a Word file”

The answer is written from your database (or the AI if allowed), then saved as a file card in the chat.
Every Markdown table becomes its own Excel sheet (header row, filter, frozen header; numbers, percentages and dates are
stored as real numbers and dates, while IDs and phone numbers stay text). Word files keep headings, lists, bold, code and
tables, and Hindi text works. PDF requests work as before.

Safety: text that starts with “=” is stored as text, never as an Excel formula.

## 2. Analyze data (tab “Analyze data”)

Upload an Excel / CSV / JSON file, or pick one of your MongoDB collections (the app's own collections are never offered).
You get, calculated on your server without AI:

- rows, columns, duplicate rows, empty cells; column types (number, date, text, ID);
- totals, average, median, min, max, unusual and extreme values; most common values; date range and monthly trend;
- totals by the most useful category (bar chart), strong correlations, and plain-language findings;
- reports as **Excel** (Summary, Columns, Numbers, chart sheets, and your data), **Word** and **PDF**.

Optional “AI commentary” sends only the measured profile (totals, top values), never your rows, and follows
“Send my data to external AI”. It is off by default because it is slower on a local model.

API: `POST /analyze/file` (multipart: file, formats, ai, question) and `POST /analyze/collection` (admin).
Nested MongoDB fields become `a.b` columns; very large tables are analysed on the first 100,000 rows (the Data sheet keeps 50,000).

## 3. Send to apps (tab “Send to apps”)

Connect Slack, Discord, Telegram, email (SMTP) or any webhook (Zapier, n8n, Make, your own system). Afterwards every
PDF / Word / Excel file card shows **Send to an app…**.

| App | What is sent |
|---|---|
| Webhook | JSON `{text, file:{name, mime, size, base64?}}`, optional `X-Webhook-Secret` header |
| Slack | text with the file name and size (Slack webhooks cannot carry files) |
| Discord | text and the file attached (up to 8 MB) |
| Telegram | the file as a document with your text as caption |
| Email | text and the file attached (up to 10 MB) |

Secrets (webhook addresses, bot tokens, passwords) are stored encrypted and are never sent back to the browser.
The server makes the outgoing call, so it refuses `http://`, addresses with a password inside, redirects, and names that
resolve to private, local or cloud-metadata addresses (SSRF protection). To connect a tool on your own network (for
example n8n at `http://192.168.1.20:5678`) set `ALLOW_PRIVATE_APP_URLS=true`. A hostname that changes its DNS answer
between the check and the call is a known limit of any such check; keep this setting off unless you need it.

## 4. Skills tab

- **Try a question**: shows which skills and connected skills a question uses and how much prompt text they add.
- **Switch skills on/off** (also a whole bundle such as `api-skill`).
- **Add a skill**: paste a SKILL.md or upload a .zip. It is active immediately. Checks: name, 200 KB text limit,
  8 MB / 300 files per zip, no unsafe paths or symlinks. Skills are reference text; nothing in them is ever run.
- **Remove** skills you installed (they live in `backend/skills/community`).
- **Connections**: link two skills with a reason. Your links come first; the built-in ones are listed below.
  Switches and links are stored in MongoDB (`settings` → `skills`) and apply within about 5 seconds.

## Tested

61 automated tests, plus a browser run (Chromium) of the real built frontend against the real backend with an
in-memory database: Excel upload, collection analysis, downloading the three reports and opening them, connecting a
webhook, sending a real workbook to it, switching / installing / linking / removing skills. 28 of 28 checks passed.
Not tested here: real Slack / Discord / Telegram / SMTP accounts and your live MongoDB and Ollama.
