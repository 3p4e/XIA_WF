# Implementation Plan: AI-Artwork Watch Face (Open Design + OpenAI Image)

> Status: **DRAFT — awaiting human review/approval** (PLAN phase)
> Spec: `docs/specs/ai-artwork-dial.md` (approved as-is)
> Author: Agent Zero (developer profile)
> Date: 2026-10-13

---

## Overview

Produce 3 distinct AI-generated dial backgrounds through **Open Design** using the
**OpenAI Image** provider, post-process them to watch-safe sprites (464×464, circular
mask, ≤256 colors), and author one full-face `wfDef.json` (analog hands + digital time +
date/weekday + health widgets + AOD). Build, patch, and unpack-verify to an installable
`deliverables/AiArt.bin`.

## Architecture Decisions

1. **Open Design integration — media endpoint first.** Use Open Design's media route
   (`POST /api/projects/:projectId/media/generate` or the tool-token variant) rather than
   hand-calling OpenAI's API. This keeps Open Design "in the loop" as the orchestrator and
   routes through its configured OpenAI Image credentials. (Verified live: provider
   `openai` is `configured: true`, `source: env`, `apiKeyTail ...OisA`, base
   `https://api.openai.com/v1`.)
   - **Fallback:** if the media route's same-origin/project-auth gate blocks a remote
     CLI/agent caller, drive the Open Design agent via `POST /api/runs` instructing it to
     run `od media generate --surface image --model gpt-image-2 --prompt "..."`, which is
     the supported agent loop path.
   - **Last resort (recorded, not preferred):** direct OpenAI Images API using the key
     already present in `od-deploy/.env` — only if Open Design cannot be driven headlessly.
2. **Single face, three concepts.** Generate 3 art concepts but build/adjust the layout as
   one face; swap only the background sprite to produce 3 previews, then build the
   human-selected concept to `.bin` (matches spec: "pick ONE to build now" default).
3. **Art build pipeline mirrors `Mono`.** Reuse the exact `wfDef.json` authoring style and
   the `pack → patch_header 1 4 1 → unpack & verify` build order. The AI background
   replaces the programmatic background only; widgets/pointers follow device-verified
   geometry from `project/mono`.
4. **Quantization is a hard invariant.** Every generated PNG is quantized to ≤256 colors
   using an adaptive palette; this is enforced in the generator, not a manual step.

## Task List

### Phase 1: Foundation — prove Open Design image generation works

- [ ] **Task 1: Live integration probe (fail-fast)**
  - **Description:** Confirm the exact request body and response shape for OpenAI Image
    generation through the live instance. Test `POST /api/projects/:id/media/generate`
    (and, if gated, `POST /api/tools/media/generate` / the `/api/runs` agent path). Record
    the working verbatim request, how the generated file is returned/placed, and the
    `projectId` + auth headers required.
  - **Acceptance:** One OpenAI Image is generated and downloaded to `project/ai-art/raw/`
    as a high-res PNG; the working invocation is captured in a script `od_generate.sh`.
  - **Verify:** `file` reports PNG; dimensions/image validity checked with Pillow; script
    recorded in repo.
  - **Files:** `scripts/od_generate.sh`, `docs/plans/ai-artwork-dial.md` (working notes)
  - **Estimated scope:** M

- [ ] **Task 2: Post-processing + preview generator**
  - **Description:** Write `project/ai-art/gen_assets.py` with a `--background <png>` mode:
    crop-to-square 464×464, circular mask, adaptive ≤256-color quantization; render
    `preview.png` (with overlaid placeholder layout) so art can be reviewed before full
    authoring.
  - **Acceptance:** Any input image → 464×464 masked PNG ≤256 colors + a readable preview
    with all widget positions marked.
  - **Verify:** script-level assert (colors ≤256, exact 464×464, non-empty alpha ring).
  - **Files:** `project/ai-art/gen_assets.py`
  - **Estimated scope:** M

### Checkpoint: Foundation
- [ ] Open Design generates images programmatically end-to-end
- [ ] Post-processing deterministically produces watch-safe backgrounds
- [ ] Human reviews the 3 art previews (decides styles to keep)

### Phase 2: Core — face authoring + build

- [ ] **Task 3: Generate 3 art concepts**
  - **Description:** Run 3 curated prompts (photoreal scenery, minimal abstract, themed
    illustration) through Open Design into `project/ai-art/raw/`, then post-process each
    to a preview for human selection.
  - **Acceptance:** 3 distinct raw PNGs + 3 post-processed previews exist.
  - **Verify:** visual inspection (assistant via `vision_load`) + script assertions pass.
  - **Files:** `project/ai-art/raw/*`, previews
  - **Estimated scope:** S

- [ ] **Task 4: Author full face `wfDef.json` + generator**
  - **Description:** Extend `gen_assets.py` to emit the complete widget set — analog
    pointers (hour/minute/smooth second), digital HH:MM with 1 Hz colon blink,
    date/weekday, steps/HR/calories/battery — over the AI background, plus an AOD variant
    (dimmed/grayscale), matching device-verified element types and geometry from `Mono`.
  - **Acceptance:** `gen_assets.py <bg>` produces `images/` + `images_aod/` + `wfDef.json`;
    previews show no clipped glyphs/overlaps.
  - **Verify:** visual preview inspection; `wfDef.json` parses; element count/ids sane.
  - **Files:** `project/ai-art/gen_assets.py`
  - **Estimated scope:** L (may split if >5 files)

- [ ] **Task 5: Build, patch, unpack-verify**
  - **Description:** Run the `Mono`-equivalent build for the selected concept:
    pack → `patch_header.py 1 4 1` → unpack → byte-level header validation.
  - **Acceptance:** `deliverables/AiArt.bin` produced; header magic `5A A5 34 12`, smooth
    byte `1`, AOD face-record flags, `faceCount=2` verified.
  - **Verify:** build log + byte checks; preview images regenerated for final confirmation.
  - **Files:** `build/`, `deliverables/AiArt.bin`
  - **Estimated scope:** S

### Checkpoint: Core Features
- [ ] One complete face builds and verifies cleanly end-to-end
- [ ] Human reviews final `preview.png` + `preview_aod.png` (approve art + layout)

### Phase 3: Ship

- [ ] **Task 6: Documentation + commit**
  - **Description:** Update `README.md` + `docs/BUILDING.md` with the AI-art face, prompt
    sourcing, and Open Design integration notes; commit spec, plan, source, and deliverable.
  - **Acceptance:** Docs accurate; `deliverables/AiArt.bin` committed; no secrets/artifacts
    tracked.
  - **Verify:** `git status` clean of `build/`/`.class`/secrets; docs link check.
  - **Files:** `README.md`, `docs/BUILDING.md`, `docs/specs/`, `docs/plans/`
  - **Estimated scope:** S

### Checkpoint: Complete
- [ ] Spec + plan + implementation + docs committed and pushed
- [ ] Ready for on-device install (human, final acceptance)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Media route same-origin/auth gate blocks remote call | High | Fallback to `/api/runs` agent path; last resort direct OpenAI API |
| AI art far exceeds 256 colors → firmware reboot | High | Mandatory adaptive quantization enforced in generator (hard invariant) |
| Dense widgets illegible over busy art | Med | 3 distinct styles; add scrim/dim behind readout zones in post-process |
| OpenAI Image returns non-square/odd sizes | Low | Crop-to-square 464×464 in post-process; validate with Pillow |
| Provider cost/limit | Low | 3 generations only; model `gpt-image-1`/`gpt-image-2` selected per config |
| Pointer geometry differs from digital-face templates | Med | Reuse device-verified `prop7`/pointer layout from upstream reference (same source as `Mono`) |

## Open Questions

1. **Exact media-route authorization** — confirm whether the remote container can drive
   `POST /api/projects/:id/media/generate` directly or must use the agent/tool path
   (resolved in Task 1, before any build work).
2. **AOD treatment** (from spec Q3, still open): dim the art vs flat black/minimal AOD.
   Default planned: flat black background + grayscale readouts for power/readability.
3. **Health set** (spec Q2): default steps · HR · calories · battery; weather/temp optional.
4. **Final concept selection** — after 3 previews, which ONE to build as `AiArt.bin`
   (or build all three as `AiArt-<style>.bin`).

## Rollback

- All generated/built artifacts are additive under `project/ai-art/` and `deliverables/`;
  `Mono.bin` and its source remain untouched. Reverting is `git checkout` of the ai-art
  paths; no shared toolchain/vendor changes are required.
