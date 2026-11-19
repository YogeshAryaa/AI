# Version 2.6.0: Word and Excel files, data analysis, connected apps, skills in the frontend

- Chat makes Word (.docx) and Excel (.xlsx) files as well as PDF (“excel bana do”, “make a Word file”, “iska Excel bana do”).
- New tab **Analyze data**: upload Excel/CSV/JSON or pick a MongoDB collection; findings, charts and Excel / Word / PDF reports.
- New tab **Send to apps**: Slack, Discord, Telegram, email and webhooks (Zapier, n8n, Make); “Send to an app…” on every file.
- New tab **Skills**: try a question, switch skills on/off, install from pasted text or zip, remove, connect skills.
- The old “Connect apps” tab (API keys for other systems to call this app) is now called **API keys**.
- Fixes found by testing: MongoDB time-zone dates in Excel; singular/plural matching in skill selection (invoice/invoices);
  a single extreme value is now reported in the findings.
- New settings: `ALLOW_PRIVATE_APP_URLS`. No new Python packages. See `docs/FILES_AND_APPS.md`.

# Version 2.5.0: connected skills, your database, faster on Ollama

- Skills are connected: `backend/skills/skill_links.json` links related skills; a chosen skill brings its linked
  skills as short companions. Details in `docs/CONNECTED_SKILLS.md`.
- Your database: close records already found by the search step are added to skill-guided AI answers (no extra query).
  They respect "Send my data to external AI". Skill usage is stored in `rag_skill_usage`.
- Speed: skill index cached in memory; short prompt for local models (~1,300 instead of ~5,000 tokens for a coding
  question); the AI rewrite call is skipped for plain English coding questions; Ollama model loaded at start-up.
- Better matching: rare words count more than common ones, a skill needs a name/trigger word in the question, so
  business questions (HR, staffing) load no skills.
- New admin endpoints `/agent-skills/plan` and `/agent-skills/graph`; new settings `SKILLS_ENABLED`,
  `SKILLS_USE_DATABASE`, `OLLAMA_WARMUP`.

# Version 2.4.2: voicestudio skill added

- Installed the `voicestudio` skill (speech generation, cloning, transcription, dubbing via a local VoiceStudio backend) and listed it in the catalog. Only the skill document is included, not the app.

# Version 2.4.1: ten agent skills installed

- Installed 10 skills into `backend/skills/community/` (list in `backend/skills/awesome-agent-skills/README.md`).
- Skill loader: multi-line YAML descriptions (`description: >`) are now parsed correctly; name/description matches
  outrank body matches; a bundle such as `api-skill` fills at most one of the 3 prompt slots.
- `/agent-skills` now reports catalog entries as installed when their folder (or bundle) is present.

# Version 2.2: task-aware intelligence routing

- Added task classification for coding, reasoning, creative and general requests.
- Added task-aware model selection across configured providers; configured priority remains the tie-breaker.
- Fast internal rewrite/condense tasks prefer fast model families.
- Strengthened coding, analysis and creative answer instructions.
- Improved RAG prompt-injection resistance and citation/conflict handling.
- Versioned answer cache so responses generated under older prompts are not reused.
- No model weights are changed; this is orchestration/prompt engineering, not fine-tuning.

# Version 2.1: files, Studio and your own AI

**Files from the chat**
- Ask for a PDF in plain words: "green theme mein leave policy ki PDF bana do", "iski PDF bana do", "poori chat ki PDF".
  6 PDF designs (classic, banner, minimal, sidebar, boxed, elegant), 1 or 2 colours named in English, Hinglish or Hindi.
- Ask for an image: "cartoon style mein office ki image banao", "laal aur sunehre rang mein logo". 12 styles, colours,
  shapes (poster, banner, story).
- Not happy? "koi aur", "3 design dikhao", "laal aur neela rang mein karo", "boxed design mein karo" remakes the last
  file. Each file keeps a recipe (content, colours, design) for this. Several designs come back side by side.
- Files are stored in MongoDB (`rag_files`), private to the API key that made them (`GET /files/{id}`).

**Your own AI first, online only as a backup**
- Own image AI on the server (Stable Diffusion Turbo via diffusers, `IMAGE_PROVIDER=local,pollinations`).
  Say "online" in the chat or choose it in Studio to use an online service instead.
- Own text AI: Ollama (Qwen 2.5 3B) as the first provider; Gemini and others stay optional backups.

**Studio (no AI at all)**
- Scan & read: text from PDFs, Word files and photos (OCR, English + Hindi), add it to your data in one click.
- Resume builder: reads an old resume into a form, 2 designs, any colour, optional photo.
- Poster maker: 6 colour themes, 4 sizes, left or centred layout, photo and logo, "Show me 4 designs". PNG + PDF.
- AI image: style, up to 3 colours, size, 1-4 designs, own AI or online.

# Version 2.0

**Connect your other systems**
- API keys per system (Connect apps tab, `/keys`): scopes, data groups (namespaces), own rate limit, rotate, switch off.
  Only hashes are stored. The admin token is now only for this UI.
- Data groups keep each system's data apart: a marketing key never sees staffing records, not even through the cache.
- Push API `/records` for instant updates from any system, plus `/sync/sources/{name}/notify` for MongoDB sources.

**Accuracy**
- Default embedding model is now multilingual (`intfloat/multilingual-e5-small`): Hindi and Hinglish questions find
  English records. Changing the model re-embeds existing data automatically.
- Match level is measured from your data (no more slider guessing). Manual mode still exists.
- Exact matching of IDs, phone numbers and emails; Hindi/Hinglish misses retried with an English rewrite;
  optional cross-encoder re-ranker; answers in the user's language; partial answers instead of guesses.
- Saved-answer cache can no longer return one person's answer for another person's question.

**Never stops**
- Grounded answers now stream (the first words appear at once, also on slow local Ollama).
- If every AI is down, the best matching records are returned instead of an error.
- Per-provider timeout (Ollama preset: 300 s). Cool-downs and rate limits are stored in MongoDB, shared by all workers.

**Big data**
- Bulk upload: several files at once; CSV, Excel, JSON, JSONL become one record per row; Word and HTML supported.
  Re-uploading a file updates it. Progress bars, background jobs stored in MongoDB.
- Batched embedding, incremental in-memory vector index (no full reload after every import), compact binary vectors,
  no 100k record cap.
- Sync: change streams (instant on Atlas/replica sets), `updated_field` incremental reads, other databases/servers,
  rare full scans only for deletions.

**History & security**
- Chat history saved per system and per end user (`user_id`); history sidebar in the UI.
- Safe MongoDB filters (allow-list of operators), secret-looking fields never indexed, upload size limit,
  security headers, brute-force blocking, `/docs` can be hidden, internal collections prefixed `rag_`.

**Deploy**
- `Dockerfile` + `docker-compose.yml` (UI + API + MongoDB replica set). The backend serves the built UI.

Upgrading from 1.x: your data, providers and settings are kept. If your `.env` still says
`EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`, nothing is re-embedded; change it to `intfloat/multilingual-e5-small`
for Hindi/Hinglish and the app re-embeds in the background.


## 2.3.0 — Gravitas skill + CompVis Stable Diffusion option

- Added `backend/skills/gravitas/SKILL.md`, adapted from the six public Gravitas engineering invariants.
- Coding-task guidance now loads and injects the bundled skill into the model prompt. This is behavioral guidance, not OS-level enforcement or an autonomous filesystem/terminal agent.
- Added configurable classic Stable Diffusion sampling for `CompVis/stable-diffusion-v1-4` through the existing Diffusers integration.
- Kept SD-Turbo as the fast default; model-aware step/guidance settings now distinguish Turbo from classic SD.
- Added studio options reporting for the configured local image model and sampling settings.
- Added tests for Gravitas prompt injection and image sampling configuration.

## 2.4.0 — VoltAgent Awesome Agent Skills integration

- Added a local searchable catalog referencing selected skills from VoltAgent's Awesome Agent Skills directory (the upstream project is an index of independently maintained skills, not a single bundled skill package).
- Added a skill registry that discovers installed `SKILL.md` packages, ranks them against each request, and injects at most three relevant skills within a prompt-size budget.
- Preserved the Gravitas engineering skill for coding tasks.
- Added admin endpoints `GET /agent-skills` and `GET /agent-skills/installed`.
- Added a GitHub-only skill installer. It accepts HTTPS GitHub repositories, installs one selected skill directory, rejects symlinks, skips common secret files, and enforces file/size limits. Skill scripts are never executed by the application.
- Third-party skills remain disabled until individually installed; review their instructions and licenses before use.
