# Connected skills, your database and Ollama

## What happens when someone asks a question

1. **Your database first (unchanged).** The question is answered from your MongoDB data when it matches.
2. **No match: AI answer, guided by skills.** For the AI fallback the app now does three things, in one fast step,
   with no extra database query and no extra AI call:
   - **Skills.** Only skills that clearly fit the question are loaded (a skill needs one of its name or trigger words
     in the question, so "leave policy" or "java developers list" load nothing).
   - **Connected skills.** The skills linked to the chosen one come along as short companions, e.g. Stripe brings
     API security, Postgres, pytest and differential review. The links are in `backend/skills/skill_links.json`.
   - **Your database records.** The closest records the search step already found are added as context
     ("YOUR DATABASE RECORDS"), so the skill advice is applied to your own data.
3. **Usage is counted in MongoDB** (`rag_skill_usage`) in the background; see it in `GET /agent-skills`.

## Why it is fast on Ollama

| | before | now (Ollama) |
|---|---|---|
| Skill files | read from disk on every question | parsed once, cached in memory (rebuilt only when a SKILL.md changes) |
| Prompt for a coding question | ~5,000 tokens, same for every model | ~1,300 tokens: 1 skill extract + short names of connected skills |
| Hindi/Hinglish rewrite AI call | also run for English coding questions | skipped when it cannot help |
| First question after start | waits for Ollama to load the model | model loaded at start-up (`OLLAMA_WARMUP=true`) |

The app detects a local model by its address (localhost / port 11434 / "ollama" in the name) and uses the short prompt;
hosted models (Gemini, Groq ...) get the fuller one.

**Settings on the Ollama side** (the OpenAI-compatible `/v1` API cannot set these per request):

- `OLLAMA_KEEP_ALIVE=-1` — keep the model in memory between questions (the single biggest win after the first question).
- `OLLAMA_FLASH_ATTENTION=1` — faster, lower memory (supported GPUs/CPUs).
- Context size: a 4k window is enough for this prompt. Create a Modelfile with `PARAMETER num_ctx 4096`
  (`ollama create qwen2.5-3b-4k -f Modelfile`) and use that model name in Providers.
- Use a small model for speed (`qwen2.5:3b`; for code `qwen2.5-coder:3b` or `:7b` if you have the RAM).

## Privacy

Records from your database now go to the AI together with skill-guided questions. They follow the existing
**"Send my data to external AI"** setting: when it is off, such questions go only to providers marked *trusted*
(for example Ollama). Questions with no matching records behave as before: only the question is sent.
To turn the database part off set `SKILLS_USE_DATABASE=false`; to turn skills off set `SKILLS_ENABLED=false`.

## See and tune it (admin token)

- `GET /agent-skills/plan?q=...&tier=local` — which skills and connected skills a question would use, and how many characters they add. Instant.
- `GET /agent-skills/graph` — which installed skills are linked.
- `GET /agent-skills` — installed skills with usage counts.
- Answers carry `skills`, `linked_skills`, `records_used` and `prompt_tier` in their meta event.

### Add or change connections

Edit `backend/skills/skill_links.json` (picked up within 30 seconds, no restart):

- `edges`: `["skill-a", "skill-b", "why they belong together"]`. A key is a folder name (`stripe-best-practices`),
  a path inside a bundle (`api-skill/api-security-patterns`) or a whole bundle (`api-skill/*`).
- `keywords`: extra trigger words for a skill. A question must contain a skill's name word or one of these before
  that skill can be chosen. Add words your team really uses (including Hinglish ones).

New skills installed with `scripts/install_agent_skill.py` work immediately; add them to the file to connect them.
