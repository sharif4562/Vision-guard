# VisionGuard Tutor — Technical & Product Audit (`AUDIT.md`)

**Date:** 2026-11-25  
**Scope:** Existing codebase under `/Users/gopalamghanashyam/.gemini/antigravity/scratch/visionguard-tutor-web` (`frontend/` React 18 + Vite + Three.js, `backend/` FastAPI + OpenCV + Gemini 2.5 Flash)  
**Status:** Audit complete. **No application code was modified during this audit.**

---

## 1. Evidence Collected

All findings below were verified against live running servers (`http://localhost:5173` and `http://127.0.0.1:8000`), SQLite inspection (`backend/visionguard.db`), and a read-only Playwright diagnostic probe (`probe_report.json`):

1. **Database Record of Real User Upload (`backend/visionguard.db`)**:
   - `diagram_uploads`: `('a9f1b2eb-6153-4d74-9724-8204507ac52b', '21704-heart-inside.jpg', width=800, height=892, blur_score=4725.49, contrast_score=100.0, quality_status='pass')`
   - `analysis_jobs`: `('0abdaca8-c97c-4b12-bb50-617a2723240e', title='21704-Heart-Inside', demo_slug=None, upload_id='a9f1b2eb-...', used_fallback=1, status='done')`
   - `analysis_results.agent1_json`:
     - `B1`: `"Detected Structure 1"`, `bbox_1000: [107, 167, 892, 823]`, `bbox_px: [134, 95, 658, 796]`, `status: "VERIFIED"`, `confidence: 0.82`
     - `B2`: `"Detected Structure 2"`, `bbox_1000: [233, 202, 476, 330]`, `bbox_px: [162, 208, 264, 425]`, `status: "VERIFIED"`, `confidence: 0.82`
   - `analysis_results.agent2_json`: `steps` contain `"Verified geometric structure B1 located at [107, 167, 892, 823]. Add a GEMINI_API_KEY in .env for live multimodal OCR on custom uploads."`
2. **Network & Console Logs (`probe_report.json`)**:
   - `GET http://localhost:5173/api/v1/uploads/c0f0b972-800a-4de0-b472-574e2129d8d0/image` → **`403 Forbidden`**
   - Console error: `"Failed to load resource: the server responded with a status of 403 (Forbidden)"`
   - Plant Cell Demo Rubric text observed: `"4/ 10"` alongside 5 `"high"` confidence steps
   - Header bounding box at `1060×768`: `Try Demo` button `x = 1119` (clipped off the right edge of the `1060px` viewport), `0 XP` badge wrapped onto two lines (`height = 36px`, `"0"` above `"XP"`).
3. **Captured Evidence Screenshots** (under `<appDataDir>/brain/d092e4af-366d-4274-aca6-397ca72feefc/audit_evidence/`):
   - `audit-a1-plant-cell-demo.png` — Plant Cell demo showing boxes around text pills, clipped edge labels, and `4/10` vs `high` confidence contradiction
   - `audit-a2-a3-a5-custom-upload.png` — Custom upload showing blank beige/grey canvas (from 403), `"21704-Heart-Inside"` raw title, and `"Offline CV Mode"` / `"Detected Structure 1"` dishonest explanation
   - `audit-a4-upload-card.png` — Upload card without preview or Replace/Remove actions + crude heart/water-cycle demo thumbnails
   - `audit-a6-header-1060.png` — Wrapped `"0 XP"` pill and `"Try Demo"` pushed off-screen at `1060px` width

---

## 2. Part A Root-Cause Analysis

### A1. Demo Data Is Misleading, Clipped, Contradictory, and Scientifically Crude
- **Root Causes**:
  1. **Boxes target label pills instead of structures**: In `backend/app/services/demo_data.py` (`_DEMO_SPECS`, lines 163–210), all `bbox_1000` tuples wrap the rectangular white label text pills (`[188, 25, 255, 175]` for `"Cell Wall"`, `[310, 25, 378, 192]` for `"Chloroplast"`, etc.) instead of the actual organelles inside the cell.
  2. **Clipped edge labels**: In `ensure_demo_image()` (`demo_data.py` lines 97–103), `Central Vacuole` starts at `x=960, w=215` (`1175/1200`), `Nucleus` at `x=980, w=180` (`1160/1200`), and `Golgi Smudge` (`B6`) at `x=965, w=230` (`1195/1200`), pressing directly against the canvas right border. When `DiagramCanvas.tsx` zooms `1.65x` on `B1`, the right side and heading are clipped (`audit-a1-plant-cell-demo.png`).
  3. **Rubric vs. Step Confidence contradiction**: `LandingPage.tsx` line 86 submits a hardcoded 1-sentence partial `reference_answer: 'Cell wall and chloroplast are verified.'` to `POST /api/v1/analyses`. `_score_reference()` (`demo_data.py` lines 255–279) matches 2 of 5 labels (`4/10`, `Missing: Mitochondria, Central Vacuole, Nucleus`), while all 5 steps display `"high"` confidence badges with no visual separation between **Diagram Reading Confidence** and **Reference Match Score**.
  4. **Crude artwork**: `ensure_demo_image()` draws `human_heart` as 4 Pillow rounded rectangles + 1 orange arc, and `water_cycle` as a green polygon triangle + blue rectangle (`audit-a4-upload-card.png`).
- **Fix Plan (Step 3)**: Replace PIL primitive art with 8 curated, scientifically accurate SVGs (with anatomical left/right heart orientation) authored with one semantic `<g id="...">` per structure; compute exact `bbox_1000` programmatically via SVG `getBBox` at build time; separate label pills from structure target regions with leader lines; clearly label demo preloaded answers as `"Sample reference answer"` and separate Reading Confidence from Reference Match Score.

### A2. Custom Upload Shows Blank Grey Canvas, Misplaced Box, and Clipped Badge
- **Root Causes (all verified)**:
  1. **HTTP 403 Forbidden on image fetch (`DiagramCanvas.tsx` + `uploads.py`)**: `DiagramCanvas.tsx` lines 38–44 loads the image via `img.src = imageUrl` (`/api/v1/uploads/{id}/image`). Browser `<img>` requests do **not** send the `Authorization: Bearer <token>` header. `uploads.py` lines 63–74 calls `get_optional_user`, which inspects **only** the `Authorization` header (`deps.py` lines 34–47), so it returns **`403 Forbidden`** (`probe_report.json`). Because `DiagramCanvas.tsx` has no `onerror` handler, `imgLoaded` stays `false`, and lines 94–96 fill the entire canvas with solid `#E9DFC8` (`audit-a2-a3-a5-custom-upload.png`). The exact same 403 bug affects `Diagram360Viewer.tsx`, `PracticePage.tsx`, `LibraryPage.tsx`, and `DashboardPage.tsx` for custom uploads!
  2. **Canvas sizing, DPR, aspect ratio & pan bugs (`DiagramCanvas.tsx`)**:
     - Lines 216–218 hardcode `width={900} height={600}` (ignoring `window.devicePixelRatio` and ignoring uploaded aspect ratios such as `800×892`, causing distortion rather than `contain` letterboxing).
     - Lines 167–168 add raw CSS screen pixels (`dx, dy`) directly to internal canvas coordinates (`cam.targetTx += dx`).
     - Line 133 places tag pills at `Math.max(4, y - 24)` without clamping `x` or keeping labels inside the viewport when zoomed (`1.65x`), causing badge clipping.
  3. **Inaccurate `bbox_1000` vs `bbox_px` & contour noise (`demo_data.py` + `box_math.py`)**:
     - Note: `bbox_1000_to_pixels` in `box_math.py` converts `[ymin, xmin, ymax, xmax]` to `[x1, y1, x2, y2]` (`[134, 95, 658, 796]` for `800×892`), which is valid; however, in `build_offline_upload_audit()` (`demo_data.py` lines 371–400), `cv2.findContours(adaptiveThreshold)` treats the outer frame `[107, 167, 892, 823]` and an arbitrary contour `[233, 202, 476, 330]` as `"Detected Structure 1"` and `"Detected Structure 2"`.
  4. **EXIF & storage observations**: `storage.py` line 64 correctly applies `ImageOps.exif_transpose(img)` before stripping EXIF, so orientation is preserved; however, files live on local relative `./storage/uploads` with no S3/R2 storage abstraction, no `/api/v1/images/{id}` endpoint, and no thumbnails.
- **Fix Plan (Step 2)**:
  - Write failing tests first (image serving auth, `contain` coordinate utility round-trip, EXIF orientation preservation).
  - Add unified `GET /api/v1/images/{id}` (plus `?variant=thumb|normalized|blank`) authenticating via Bearer token, httpOnly session/image token or signed short-lived URL, with proper `Content-Type`, `Cache-Control`, and ownership checks, plus a frontend authenticated `useAuthenticatedImage` / Blob loader (or signed image URL) so `<canvas>`, `<img>`, and Three.js `TextureLoader` never hit 403 and cleanly revoke Object URLs only on unmount/change.
  - Build one shared `coords.ts` utility (`normalised 0–1000 <-> image px <-> letterboxed canvas <-> screen`) with `devicePixelRatio` scaling, `"contain"` padding, box/badge clamping, and full unit tests.
  - Add S3-compatible / local storage abstraction (`storage_backend`).

### A3. Fallback Mode Is Dishonest ("Offline CV Mode" / "Detected Structure 1")
- **Root Causes**:
  - `demo_data.py` lines 390–476 (`build_offline_upload_audit`) marks arbitrary OpenCV contours as `status="VERIFIED"` (`confidence=0.82`), invents labels `"Detected Structure 1"` / `"Detected Structure 2"`, fabricates step text `"Verified geometric structure B1 located at [...]. Add a GEMINI_API_KEY..."`, and creates Practice Mode distractors `["Mitochondria", "Nucleus", "Aorta"]` for unknown uploaded diagrams!
  - `AnalysisWorkspacePage.tsx` line 154 displays `"Offline CV Mode"` with a green `"1 Verified"` badge.
- **Fix Plan (Step 3 & Part E)**:
  - Rename to **`Limited Mode`** with an explicit warning banner explaining what it can and cannot do (local OCR + OpenCV quality checks only; no AI explanation).
  - Run local OCR (`RapidOCR` / `EasyOCR` / `Tesseract`) + OpenCV legibility gates: mark **only** OCR-confirmed readable labels as `VERIFIED`, generate **zero** fabricated explanation steps (`steps = []` with honest notice), and keep Practice Mode operational strictly on OCR-confirmed labels.

### A4. Upload Card Lacks Preview, File Metadata, and Replace/Remove Actions
- **Root Cause**: `NewAnalysisPage.tsx` lines 210–285 renders only a static dashed `<label>` dropzone and a small quality metrics box after upload—no local `URL.createObjectURL` thumbnail preview, no file name/size/dimensions chip, no `Replace` or `Remove` buttons, and leaves a large empty gap beneath the card.
- **Fix Plan (Step 2)**: Show instant local preview (`URL.createObjectURL`, revoked cleanly on replace/unmount), file metadata (name, size in KB/MB, `W × H` px), live OpenCV quality report (`blur`, `contrast`, `resolution`), and explicit **Replace** / **Remove** buttons.

### A5. Raw Filenames Used as Diagram Titles
- **Root Cause**: `backend/app/api/v1/analyses.py` line 116 derives `title` directly from `upload.original_filename.rsplit(".", 1)[0].replace("_", " ").title()`, producing `"21704-Heart-Inside"`.
- **Fix Plan (Step 7, or earlier with A4/E)**: Default uploaded diagram titles to `"Untitled diagram"` (or user-provided title during upload) and allow inline editing on the workspace/library (`PATCH /api/v1/library/{job_id}`).

### A6. Header Bugs ("Try Demo" & "148 XP" Wrapping / Overflow)
- **Root Cause**: `Navbar.tsx` lines 60–97 uses `flex items-center gap-2` without `whitespace-nowrap` or `shrink-0` on `<Badge>` / `<ClayButton>`, and keeps 6 nav links + LanguagePicker + ThemeToggle + XP badge + Profile button + Try Demo all inline down to `lg` (`1024px`). At `1060×768` (`audit-a6-header-1060.png`), `0 XP` wraps onto two lines and `Audit` + `Try Demo` overflow past the right edge (`x=1119 > 1060`).
- **Fix Plan (Step 7)**: Enforce `whitespace-nowrap shrink-0` on all header pills/buttons, collapse full nav links cleanly below `xl` (`1280px`) into the responsive menu, and verify zero wrapping/overflow at `1366×768`, `1920×1080`, `1060×768`, and `390×844`.

---

## 3. Architectural Gaps Across Parts B–H

| Area | Current State | Gap & Fix Summary |
|---|---|---|
| **B1–B2. Curated Library & Licences** | 3 Pillow-drawn demos; no textbook licences or attributions page | Author 8 clean SVGs across Biology, Physics, Chemistry, Earth Science; derive boxes programmatically from SVG `getBBox`; store OpenStax (CC BY 4.0) & Wikimedia Commons citations/licences; add `/attributions` page + visual QA render script + unit tests verifying every box encloses its structure. |
| **B3. Reference KB (RAG)** | None | Chunk OpenStax/curated passages into local vector index (`sqlite-vec` / `numpy` + embeddings); require Agent 2 passage IDs per sentence; run strict JSON verifier (`supported` / `partially` / `unsupported`) and strip/flag unsupported sentences. |
| **B4–B5. Dual Verification & Self-Consistency** | Single-pass Gemini or naive contour fallback; no OCR (`tesseract` not installed); no arrow-endpoint check | Install Python OCR (`rapidocr-onnxruntime` or `easyocr`), cross-check Gemini labels vs OCR; verify OpenCV leader-line/arrow endpoints hit structure regions (`"association uncertain"` otherwise); run Agent 1 twice and require label match + `IoU >= 0.5`. |
| **B6. Trust Score (0–100)** | No trust score; only step `"high"/"medium"` badge | Compute weighted Trust Score in config (`15%` quality, `25%` OCR agreement, `15%` box stability, `15%` association, `20%` textbook support, `10%` reference match redistributed when absent); bands `80+` Trusted, `60–79` Review suggested, `<60` Low trust; UI gauge, breakdown bars, "Why this score", citations. |
| **B7. Eval Harness (`/eval`)** | None | Build gold set (8 curated + public AI2D/TQA/ScienceQA via setup script respecting licences + 10 hand-labelled blurry/hand-drawn); compute label accuracy, `IoU>=0.5` P/R, unverified recall, step-grounding & unsupported rates; output `eval/report.md`, calibrate weights, expose **Model Reliability** page, run cached eval in CI. |
| **B8. Rubric Fix** | Substring match (`lbl.lower() in lower_ref`); runs on partial demo text without clear separation | Return `"N/A: no reference provided"` when empty; semantic matching (embeddings + strict judge) with quotes; clearly label `"Sample reference answer"`; visually separate **Diagram Reading Confidence** from **Reference Match Score**. |
| **C. Workspace** | Fixed `900×600` canvas, no leader lines, no legend table, no spotlight dim | Shared coordinate transform, `"contain"` with padding, numbered structure pins, leader lines, two-way hover/scroll linking, spotlight dimming, legend table, yellow hatched unverified overlay + reason tooltip. |
| **D. 2.5D Depth View & 3D Models** | Single flat plane texture in `Diagram360Viewer.tsx`; no depth layers or real 3D demo meshes | Server-side per-component alpha-masked WebP textures (`<=2048px`) ordered by containment hierarchy (+ optional Depth Anything V2 flag); **Illustrative depth view** with Explode/Assemble springs, billboard labels, dolly camera, flat yellow-shimmer unverified regions; procedural/GLB 3D models for built-in demos; WebGL context-loss + 2D fallback. |
| **E. Upload & Storage** | Local disk only, 403 on `<img>`, no thumbnails, dishonest fallback | `StorageBackend` (local dev / S3-R2 prod), `GET /api/v1/images/{id}` with thumbnails + caching + auth, `Limited Mode` OCR-only with clear banner, friendly retry UI. |
| **F. Practice Mode** | Uses unauthenticated image URLs (403 on custom uploads); no pixel-alignment test | Wire authenticated image URLs/blobs, add automated pixel-alignment overlay test on blank-label duplicates, enforce identical verified answer key. |
| **G. Typography** | Google Fonts (`Plus Jakarta Sans`/`Sora`/`Inter`), no self-hosted `woff2`, no Playfair Italic / Dancing Script | Self-host `woff2` subsets (`Playfair Display Italic` 600–700, `Dancing Script` 600 for `<=6`-word kickers `>=24px`, `Plus Jakarta Sans` upright with `tabular-nums`); verify zero clipping/overflow at `1366×768`, `1920×1080`, `390×844`. |
| **H. Deployment & Polish** | Root Dockerfiles, no CI, missing legal/attribution/error pages, no `demo:check` | Multi-stage non-root Dockerfiles with healthchecks, fail-fast env validation, Postgres/S3 prod support, CSP & `SameSite=None; Secure` guidance, GitHub Actions CI, `DEPLOY.md` + smoke test, About/Terms/Privacy/Attributions/500 pages, OG/PWA, and `npm run demo:check`. |

---

## 4. Prioritized Fix Plan (Exact Work Order)

1. **Step 1 (Complete):** `AUDIT.md` delivered with live evidence; awaiting user approval.
2. **Step 2 — Fix A2 / A4 / E (Storage, Image Serving, EXIF, Coordinates, Preview, Canvas):**
   - Write failing tests for authenticated image serving, `contain` + DPR coordinate math, and EXIF orientation.
   - Implement `StorageBackend` (local + S3-compatible), `GET /api/v1/images/{id}` (full, normalized, thumb, blank), and authenticated frontend image loading.
   - Build shared `coords.ts` utility + refactor `DiagramCanvas.tsx` (`contain`, DPR scaling, accurate zoom/pan, clamped badges).
   - Upgrade `NewAnalysisPage.tsx` upload card with instant local preview, metadata, live quality gate, and Replace/Remove controls.
   - Verify in browser with before/after screenshots.
3. **Step 3 — Fix A1 / A3 / B1 (Honest Limited Mode & Curated SVG Ground-Truth Library):**
   - Replace `"Offline CV Mode"` with honest **`Limited Mode`** (local OCR + OpenCV only; zero fake explanations).
   - Author 8 scientifically accurate SVG diagrams with programmatic `getBBox` JSON specs, textbook metadata/licences, visual QA PNG render script, and unit tests verifying box containment.
   - Verify in browser with before/after screenshots.
4. **Step 4 — B2–B8 (RAG, Dual OCR + Arrow Verification, 2-Run Self-Consistency, Trust Score, Rubric, `/eval`, Reliability Page):**
   - Build local vector RAG over OpenStax/curated passages + sentence-level verifier.
   - Add local OCR cross-check, OpenCV leader-line/arrow endpoint verification, and 2-run Agent 1 IoU stability check.
   - Implement configurable weighted `TrustScore` (`0–100`), semantic Rubric (`N/A` when unprovided), `/eval` harness (`eval/report.md`), `Attributions` and `Model Reliability` pages.
5. **Step 5 — Part C & Part F (Workspace & Practice Mode Upgrade):**
   - Upgrade Workspace with numbered structure pins, leader lines, two-way hover/scroll linking, spotlight dimming, legend table, and yellow hatched unverified overlays with reason tooltips.
   - Fix Practice Mode image auth and add blank-label pixel-alignment tests.
6. **Step 6 — Part D (2.5D Depth Layers & 3D Demo Models):**
   - Server-side GrabCut/threshold alpha-masked WebP component textures ordered by containment (+ optional Depth Anything V2 flag).
   - Three.js **Illustrative depth view** with Explode/Assemble springs, billboard labels, dolly camera, WebGL context-loss recovery, plus real procedural/GLB 3D models for the 8 curated demos.
7. **Step 7 — Part G & A5 / A6 (Typography & Header/Title Polish):**
   - Self-host `woff2` fonts (`Playfair Display Italic`, `Dancing Script`, `Plus Jakarta Sans` tabular-nums), editable `"Untitled diagram"` default title, header `nowrap`/`shrink-0` and `xl` collapse; verify at `1366×768`, `1920×1080`, and `390×844`.
8. **Step 8 — Part H (Deployment, CI, Legal Pages, `npm run demo:check`, Final QA):**
   - Multi-stage non-root Dockerfiles, fail-fast config, CSP headers, GitHub Actions CI, `DEPLOY.md` + smoke script, About/Terms/Privacy/500/OG/PWA, and `npm run demo:check` + Lighthouse 85+/90+ audit.
