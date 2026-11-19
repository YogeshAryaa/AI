# Intelligence upgrade notes (v2.2)

## What changed

- Added `backend/app/intelligence.py` for task classification, task-specific answer guidance, and task-aware provider ranking.
- Coding requests prefer configured coding-capable model families; complex analysis prefers reasoning-oriented model families; short internal rewrites and small-talk prefer fast models.
- Existing provider priority remains the tie-breaker when model-family scores are equal.
- Existing cooldowns, request limits, trusted/local-only filtering, and failover remain in place.
- Grounded RAG prompts now treat retrieved passages as untrusted data, require citations for factual claims, and ask the model to disclose conflicting sources.
- Cache entries are versioned. Old answers created under earlier prompts are ignored so they cannot override the upgraded behavior.
- Application version is now 2.2.0.

## Important limitation

This upgrade improves orchestration and prompts. It does not modify model weights, create new capabilities in a weak model, or provide the same intelligence as a frontier model. The router uses model-name heuristics, not a benchmark of the provider's real model quality. Confirm each model ID with its provider and evaluate it on representative prompts.

This package does not yet include autonomous local project editing, terminal execution, agent planning, or LoRA/QLoRA fine-tuning. Those should be implemented as a separate, permissioned coding-agent layer.

## Apply the upgrade

1. Extract this archive.
2. Copy your original `backend/.env` into the new `backend/` directory. The updated archive intentionally excludes `.env` to avoid redistributing secrets.
3. Install backend dependencies in your existing virtual environment:
   `pip install -r backend/requirements.txt`
4. Run the backend tests:
   `cd backend && python -m unittest discover -s tests -v`
5. Restart the backend.

Your MongoDB database and provider configuration are not migrated or reset by these code changes.

## Credential safety

The uploaded original archive contained `backend/.env`. If it contains real admin tokens, application secrets, or other credentials, rotate them. Never commit or share `.env`; keep `environment.example` as the template.


## Version 2.3.0 additions

### Gravitas engineering skill
The coding profile now injects `backend/skills/gravitas/SKILL.md`, covering read-before-write, declared scope, risk-scaled planning, fresh verification evidence, diagnosis before retry, acceptance criteria, and honest reporting. The current product remains a RAG/chat assistant; it does not yet have filesystem/terminal tools or Gravitas native hooks, so this is skill guidance rather than enforced execution policy.

### CompVis Stable Diffusion
The app already had Diffusers-based local image generation. You can now select `CompVis/stable-diffusion-v1-4` using `IMAGE_LOCAL_MODEL`, with classic-model sampling defaults (30 steps, guidance 7.5). SD-Turbo remains the default (2 steps, guidance 0). The checkpoint is downloaded from Hugging Face on first use and is not included in this ZIP. Accept any required Hugging Face model terms before downloading.
See `docs/AI_SKILLS_AND_IMAGE_MODELS.md`.
