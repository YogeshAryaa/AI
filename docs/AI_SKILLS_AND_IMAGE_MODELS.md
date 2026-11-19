# Engineering skill and Stable Diffusion integration

## Gravitas engineering skill

The application includes `backend/skills/gravitas/SKILL.md` and injects the six core engineering invariants into coding-task guidance. This improves instruction discipline, but it is not equivalent to Gravitas' native hooks, CLI, evidence ledger, or host-level write/stop enforcement. The current application does not yet expose a repository filesystem/terminal coding-agent toolset; those are a separate milestone.

Upstream: https://github.com/udaysharmadev/Gravitas (MIT). The local file is an adaptation of the public workflow principles, not a copy of the full upstream runtime.

## CompVis Stable Diffusion

The app already uses Hugging Face Diffusers for local text-to-image generation. You can select the CompVis Stable Diffusion v1.4 checkpoint without installing the legacy CompVis repository into the main FastAPI environment.

In `backend/.env`:

```env
IMAGE_PROVIDER=local,pollinations
IMAGE_LOCAL_MODEL=CompVis/stable-diffusion-v1-4
IMAGE_LOCAL_STEPS=30
IMAGE_LOCAL_GUIDANCE=7.5
IMAGE_LOCAL_SIZE=512
```

The first model load downloads weights from Hugging Face. The CompVis checkpoint may require logging into Hugging Face and accepting its model terms before download. The model weights are not included in this source ZIP. CPU inference is supported but slow; a compatible NVIDIA GPU is recommended.

For the existing fast default, use:

```env
IMAGE_LOCAL_MODEL=stabilityai/sd-turbo
IMAGE_LOCAL_STEPS=2
IMAGE_LOCAL_GUIDANCE=0
```

The code automatically bounds sampling settings and uses different defaults for Turbo and classic Stable Diffusion. Check the CompVis model card and CreativeML OpenRAIL-M licence before commercial or public deployment; implement suitable safety controls for any public-facing image-generation service.

Upstream code/model: https://github.com/CompVis/stable-diffusion. This integration uses the Diffusers-compatible Hugging Face checkpoint through the existing Diffusers dependency; it does not vendor the full legacy CompVis training repository or include its weights.
