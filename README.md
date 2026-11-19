---
title: Ask My Data
sdk: docker
app_port: 8000
---

# Ask my data: your own free AI over your company data

Answers questions (English, Hindi, Hinglish) from **your data first**: MongoDB collections, files, and records your
other systems push in. If the answer is not there, a chain of **free AI APIs** (Groq, Gemini, OpenRouter, Ollama...)
takes over with automatic failover. Each of your systems (staffing, marketing, ...) connects with its own API key.

```
rag-app/
  backend/    FastAPI + MongoDB + local multilingual embeddings + provider failover router
  frontend/   React UI: chat with history, data import, AI providers, API keys
  docs/INTEGRATION.md   how your other systems call the API
```

## Run on your PC (development)

Needs: Python 3.10+, Node 18+, a MongoDB (local, or a free Atlas cluster).

```bash
./run-backend.sh          # Windows: run-backend.bat   (first run creates backend/.env and stops)
```
Edit `backend/.env`: `MONGODB_URI`, `ADMIN_TOKEN` and `APP_SECRET_KEY` (two different long random strings:
`python -c "import secrets; print(secrets.token_urlsafe(32))"`). Run it again; the first start downloads the
embedding model (~470 MB).

```bash
./run-frontend.sh         # Windows: run-frontend.bat   -> http://localhost:5173
```
In the app: *Backend connection* → `http://localhost:8000` + your `ADMIN_TOKEN` → Connect.

## Ready-made knowledge base (works without any AI)

`backend/seed_data/*.json` holds ~100 ready answers for staffing, recruitment, marketing, sales, HR and the app
itself. Load them (backend running): `cd backend && .venv\Scripts\python seed_data.py`. Edit the answers (especially
`hr_policies.json` and the company templates in `general.json`) or add new files with the same shape, then run it
again: items have fixed ids, so changes update instead of duplicating.

Without any AI provider the app still replies: greetings are answered instantly, questions that clearly match your
data get the stored answer, anything else gets a polite "not in my data" reply. With providers added, they are
tried in order (top first); one that errors or hits its limit is paused and the next is used automatically.

## Deploy on a server (one command)

```bash
cp backend/.env.example backend/.env    # set ADMIN_TOKEN, APP_SECRET_KEY, DOCS_ENABLED=false
docker compose up -d --build            # UI + API on port 8000, MongoDB with live sync included
```
Put HTTPS in front (e.g. Caddy: `ai.yourcompany.com { reverse_proxy localhost:8000 }`). Without Docker:
`cd frontend && npm run build`, then run uvicorn as in `run-backend.sh` (without `--reload`, with `--workers 2`);
the backend serves the built UI itself.

A 2 vCPU / 4 GB RAM VPS handles a few hundred thousand records comfortably. For millions, use MongoDB Atlas and
`VECTOR_BACKEND=atlas`.

## First steps in the app

1. **AI providers**: add free APIs. Put a fast one first (Groq or Gemini), Ollama last as a private backup.
2. **My data**: choose a data group (e.g. `staffing`), then upload files (CSV/Excel for bulk), or connect a MongoDB collection.
3. **Connect apps**: create one API key per system. Copy-paste code is shown. See `docs/INTEGRATION.md`.
4. **Ask**.

## Good to know

- **Privacy**: provider keys are encrypted; app keys are stored only as hashes. Passages from your data go to the
  AI provider that writes the answer. To keep them on your own machine, use Ollama (marked "local") and tick
  *Keep my data on local providers only* in My data → Settings. The general-AI fallback only receives the question.
- **Local Ollama is slow on CPU**: use a small model (`qwen2.5:3b` is good at Hindi), set `OLLAMA_KEEP_ALIVE=24h`
  so it stays loaded, and keep a free cloud provider above it. Answers stream word by word either way.
- **Changing the embedding model** re-embeds everything in the background by itself (progress in My data → Settings).
- More: `backend/README.md` (how answers are chosen, all endpoints), `CHANGES.md`.


## Intelligence upgrade (v2.4)

The chat backend now classifies general-AI requests into `coding`, `reasoning`, `creative`, and
`general` task profiles. The provider router uses the profile to prefer suitable configured model
names (for example, coding-specialized models for code tasks and reasoning-oriented models for
analysis), while preserving the existing provider priority as a tie-breaker and retaining the
existing cooldown/rate-limit failover behavior.

This is **application-level routing and prompt engineering**, not model training. It does not turn
a small Ollama model into a frontier model. The quality ceiling is still determined by the actual
model and the API access attached to each provider. Model-name matching is a heuristic; verify
the provider's actual model ID and benchmark it on your own tasks.

Other improvements:
- Stronger task-specific instructions for coding, analysis and creative requests.
- Grounded RAG answers treat retrieved passages as untrusted data, cite claims, and explain conflicting sources.
- Old cached AI answers are ignored after the prompt upgrade so stale responses do not mask the new behavior.
- Short internal tasks such as query rewriting and conversation condensation prefer fast models.
- Trusted/local-only mode continues to exclude external providers.

### Configure model order

Add the real model IDs exposed by each provider in **AI providers**. The router recognizes common
model-family naming patterns, but unknown names fall back to your configured priority. Keep at least
one capable fallback enabled. For private data, retain the **trusted/local-only** setting.

### What this upgrade does not yet provide

This release does not add autonomous project-file editing, shell execution, multi-agent coding,
LoRA/QLoRA training, or hidden chain-of-thought access. Those are separate features. The next
engineering milestone for a true coding agent is a permissioned workspace tool layer (read/search/
patch files, run tests in a sandbox, inspect diffs, and require approval for destructive actions).

## Agent Skills (v2.4)

The app can load Agent Skills stored as `SKILL.md` packages under `backend/skills/`. It keeps the Gravitas engineering skill active for coding requests and can select up to three additional relevant skills per request. Skill text is treated as reference guidance; the application does not execute scripts shipped inside skills.

The `backend/skills/awesome-agent-skills/` folder contains a searchable starter catalog for [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills). The upstream project is a directory of 1,000+ independently maintained skills, not the full source for every skill. Install a specific skill from its source GitHub repository:

```bash
python backend/scripts/install_agent_skill.py --repo https://github.com/OWNER/REPOSITORY.git --path path/to/skill --name local-skill-name
```

Admin API: `GET /agent-skills` lists the catalog and installed packages; `GET /agent-skills/installed` lists packages currently discoverable by the prompt loader. Review each third-party skill's content and license before installing it.

## Connected skills (v2.5)

Installed skills are linked to each other, use records from your database and keep prompts short for Ollama. See `docs/CONNECTED_SKILLS.md`.

## Files, analysis, apps (v2.6)

Word/Excel/PDF from the chat, an Analyze data page, sending files to Slack/Discord/Telegram/email/webhooks, and skill management in the UI. See `docs/FILES_AND_APPS.md`.

## Local media generation

Studio supports local ComfyUI workflows for image and video generation, with Ollama prompt enhancement. See [`docs/COMFYUI.md`](docs/COMFYUI.md) for setup.
