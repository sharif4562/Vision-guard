# VisionGuard Tutor

> **Zero-Guessing Scientific Diagram Explanation Assistant** — two-stage Visual Auditor (`gemini-2.5-flash`) + Deterministic Guardrail Lock + Grounded Tutor & Blank-Label Practice Mode.

## Quick Start (Under 5 Commands)

```bash
cp .env.example .env
cd backend && uv venv --python 3.11 && source .venv/bin/activate && uv pip install -e ".[dev]" && alembic upgrade head && uvicorn app.main:app --reload
# In a second terminal:
cd frontend && npm install && npm run dev
```

Or with Docker Compose:

```bash
cp .env.example .env && docker compose up --build
```

Open `http://localhost:5173`. Leave `GEMINI_API_KEY` empty in `.env` to run in instant offline Demo Mode (`plant_cell`, `human_heart`, `water_cycle`) and OpenCV fallback mode.

## Hackathon Demo Script (2 Minutes)

1. **Landing & 360° 3D Audit (`/`):** Drag the 3D Audit Slab and switch between Plant Cell, Human Heart, and Water Cycle in the **360° Interactive Diagram Inspector** — green pins mark `VERIFIED` labels; Mango Yellow marks `UNVERIFIED` blurred corners.
2. **Instant Demo Analysis (`/analyze` -> `/workspace/:jobId`):** Click **Run Demo Audit** on Plant Cell with a reference answer. Watch the 4-stage pipeline (`Preprocess` -> `Visual Audit` -> `Guardrail Lock` -> `Grounded Tutor`), toggle **360° 3D View** vs **2D Zoom Canvas**, click any step to zoom onto its bounding box, and inspect the **Rubric Comparison Card**.
3. **Zero-Guessing Proof:** Upload a blurry photo in `/analyze` — OpenCV reports `blur_score < 45` (`fail`), and the Guardrail Lock blocks all blurry regions as `UNVERIFIED` so the tutor refuses to fabricate explanations.
4. **Blank-Label Practice Mode (`/practice/:jobId`):** Flip between the original and masked diagram, solve verified blanks across Type / Drag Word Bank / MCQ / Timed modes (note `B6` UNVERIFIED is excluded), update SM-2 intervals, and export the printable PDF worksheet.

## Running Tests

```bash
# Backend (pytest + httpx)
cd backend && source .venv/bin/activate && pytest -v

# Frontend unit (Vitest) & E2E (Playwright)
cd frontend && npm test && npx playwright test
```
