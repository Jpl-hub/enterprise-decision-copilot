# Frontend / Backend Handoff

## 1. Project positioning

This project is not a generic chat app and not a dashboard-only demo.

The target product is:

> An agent-centered enterprise operations analysis and decision support system for the pharmaceutical/biotech domain, using real financial disclosures, research reports, and macro data to support intelligent querying, company diagnosis, peer comparison, risk insight, and structured report export.

Three system pillars are already established and should remain aligned:

1. Traditional application + Agent
2. AI / deep learning / multimodal extraction
3. Big-data-oriented lakehouse and scalable compute

The current implementation already has real backend services, real data pipelines, multimodal evidence, and authenticated workflow. The problem is not "lack of functionality". The problem is that the frontend product layer is still inconsistent, visually weak, and not yet at competition-grade polish.

## 2. Current stack and runtime

### Backend

- Framework: FastAPI
- Entry: [app/main.py](/D:/code/my-agent/app/main.py)
- Static asset mount:
  - `/static`
  - `/cache-assets` for multimodal page images and cached artifacts
- Auth: token-based, enforced at router layer

### Frontend

- Framework: Vue 3 + TypeScript + Pinia + Vue Router + Vite
- Router: [frontend/src/router/index.ts](/D:/code/my-agent/frontend/src/router/index.ts)
- API client: [frontend/src/api/client.ts](/D:/code/my-agent/frontend/src/api/client.ts)

## 3. Current page map

Current routes:

- `/` overview / analysis entry
- `/workbench/:companyCode?` company analysis page
- `/compare` company comparison page
- `/quality` data trust / governance page
- `/competition/:companyCode?` export page
- `/threads` thread history
- `/audit` audit log

Important note:

- User-facing UI should not contain "competition", "contest", "defense", or similar wording.
- Internal route `/competition` still exists because it is currently wired as the export page. This should be renamed later at the product layer, even if the backend contract remains unchanged temporarily.

## 4. Backend API contracts already in use

These are the main contracts the frontend is consuming now.

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### Core product

- `GET /api/dashboard`
  - overview payload, target company pool, rankings, macro and research summary

- `GET /api/company/{company_code}/report`
  - single-company report page payload
  - route implementation: [app/api/routes/reports.py](/D:/code/my-agent/app/api/routes/reports.py)

- `GET /api/company/compare?company_codes=...&company_codes=...`
  - compare payload
  - includes `comparison_rows`, `dimensions`, `evidence.companies`, `evidence.freshness`
  - route implementation: [app/api/routes/reports.py](/D:/code/my-agent/app/api/routes/reports.py)

- `GET /api/company/{company_code}/decision-brief?question=...`
  - decision brief
  - route implementation: [app/api/routes/briefs.py](/D:/code/my-agent/app/api/routes/briefs.py)

- `GET /api/company/{company_code}/risk-forecast`
  - risk forecast

- `GET /api/company/{company_code}/competition-package?question=...&persist=true`
  - currently used as export material generation API

### Agent

- `POST /api/agent/query`
- `GET /api/agent/threads`
- `GET /api/agent/threads/{thread_id}`

### Data trust / governance

- `GET /api/quality/summary`
- `GET /api/quality/foundation`
- `GET /api/quality/preparation`
- `GET /api/quality/governance`
- `POST /api/quality/reviews`
- `POST /api/quality/reviews/auto`

### Supporting pages

- `GET /api/ai/stack`
- `GET /api/risk/model-summary`
- `GET /api/universe/summary`
- `GET /api/universe/promotion-plan`
- `GET /api/warehouse/summary`
- `GET /api/warehouse/overview`
- `GET /api/audit/logs`

## 5. Data and evidence specifics that affect frontend design

This product is evidence-based. The frontend should assume the following real artifact types exist and should be surfaced cleanly:

1. Structured company financial metrics
2. Stock research digests
3. Industry research digests
4. Macro indicators
5. Official disclosure freshness metadata
6. Multimodal financial-report extraction results
7. Cached official page images under `/cache-assets/...`

The compare and workbench pages already expose clickable multimodal evidence anchors such as:

- `PAGE 21`
- `PAGE 53`
- `PAGE 144`

These should be treated as first-class evidence interactions, not as secondary utility links.

## 6. Honest assessment of current frontend state

This section is intentionally blunt.

### What is already working

1. There is now only one primary ask area on the homepage.
2. Thread continuation and task-mode restoration are wired.
3. Overview, workbench, compare, quality, export, and governance flows all have real backend data behind them.
4. Compare and workbench pages already expose evidence, freshness, and multimodal anchors.
5. Core navigation is functional and authenticated.

### What is still weak

1. Visual language is inconsistent.
   - Some pages are cockpit-like, some are plain admin panels, some still feel like internal tooling.

2. Hierarchy is still not strong enough.
   - Important decisions, evidence, and actions are not consistently separated into primary / secondary / supporting layers.

3. Typography and spacing are not premium.
   - The current interface still reads as assembled-by-iteration rather than intentionally art-directed.

4. There is still too much explanatory filler text.
   - Several cards still say what the system is doing instead of helping the user decide what to do next.

5. Naming is not fully productized.
   - Some labels still sound like internal system language.

6. Export page is functional but visually weak.
   - It still looks like a utility screen, not a polished output workspace.

7. The system has too many page-level card patterns.
   - This is making the product feel heavier and less coherent than it should.

### Core diagnosis

The frontend currently behaves like a technically capable internal prototype with partial product polish. It is not yet a finished competition-grade product experience.

## 7. Product principles the frontend should now follow

These should be treated as hard constraints.

1. One page, one primary job.
   - Home: ask and route
   - Workbench: understand one company
   - Compare: decide between companies
   - Quality: prove trust and coverage
   - Export: package results

2. Do not duplicate the ask interaction across pages.
   - Embedded deep-follow-up inside workbench is acceptable only if it clearly belongs to the single-company context.
   - No second homepage-like chat zone elsewhere.

3. Evidence is not appendix content.
   - Evidence anchors should be part of the main decision flow.

4. No contest wording in UI.
   - The product must look like a real enterprise-grade system, not a hackathon artifact.

5. Reduce low-value gray helper text.
   - Replace explanation with action, status, evidence, or decision structure.

6. Reduce card count.
   - More sections should be composed as deliberate layouts, not endless isolated tiles.

7. Buttons and action rows must align perfectly.
   - This has already been a visible issue and needs strict cleanup.

## 8. Recommended frontend redesign direction

The right direction is not "more futuristic dashboard".
The right direction is:

- Apple-level restraint in spacing and typography
- enterprise-grade clarity in information hierarchy
- selective high-impact data visualization where it adds decision value

Suggested aesthetic direction:

1. Cleaner layout rhythm
   - larger whitespace blocks
   - fewer borders
   - stronger contrast between page header, primary content, and supporting rail

2. More intentional typography
   - avoid default "admin system" tone
   - use clearer title scales and fewer muted paragraphs

3. Fewer but stronger action groups
   - one clearly primary button
   - secondary actions grouped and visually quieter

4. Evidence panels should feel premium
   - page anchors, report links, latest titles, and provenance need a cleaner component pattern

5. Charts should be used surgically
   - not to decorate
   - only where comparison, trend, confidence, or coverage becomes easier to read

## 9. Recommended page responsibilities for the frontend lead

### Homepage

Keep:

- company focus
- single main ask area
- route cards into analysis / compare / quality / export

Need redesign:

- make the main ask area the unquestioned visual center
- make the support panels quieter
- remove residual "system talking to itself" feel

### Workbench

Keep:

- management judgment
- operating analysis
- risk judgment
- evidence backtrace
- reasoning chain

Need redesign:

- stronger headline summary
- better action bar
- evidence and reasoning should feel integrated, not appended

### Compare

Keep:

- winner verdict
- score spread
- dimension board
- evidence stream
- multimodal anchors

Need redesign:

- stronger "decision first" layout
- clearer challenger/winner narrative
- cleaner secondary rail

### Quality

Keep:

- governance tables
- preparation summary
- foundation summary
- AI stack summary

Need redesign:

- turn from "ops dashboard" into "trust center"
- clearer story from sources -> coverage -> field quality -> evidence mapping

### Export page

Needs the most product work.

Current function is valid, but presentation is not.
It should become a proper report packaging workspace, not a text dump page.

## 10. Frontend/backend coordination rules

These are the boundaries I suggest keeping stable.

### Backend responsibilities

1. Return domain-ready payloads
   - winner, freshness digest, evidence digest, multimodal digest, governance summary

2. Keep provenance explicit
   - source URL, report date, institution, page anchor, disclosure date

3. Keep export/report APIs deterministic
   - frontend should not compose business semantics from scratch

4. Keep auth and role semantics in backend
   - frontend should only adapt presentation

### Frontend responsibilities

1. Own layout, information hierarchy, and interaction quality
2. Normalize empty / loading / stale / error states
3. Avoid inventing business interpretation not returned by the backend
4. Use backend evidence artifacts as first-class visual objects

### Coordination preference

Frontend should request backend changes only when:

1. the current payload shape causes duplicated client heuristics
2. the UI needs a stable provenance field that is currently inferred
3. a page needs a dedicated summary block to avoid overfetching and recomputation in the client

## 11. Backend improvements I expect the frontend lead may request

These would be reasonable requests, not scope drift.

1. A dedicated export-page summary payload
   - lighter than the full package
   - separate metadata, sections, citations, and downloadable assets

2. A cleaner company-page summary block
   - one object for hero verdict, one for evidence counts, one for freshness

3. A cleaner compare-page "decision summary"
   - one compact backend object for winner, challenger, rationale, freshness, evidence totals

4. Optional explicit stale-state markers
   - whether certain metrics are annual-only, quarterly, or estimated from latest available disclosures

## 12. Short-term priorities for the frontend lead

If the frontend lead only has time for the highest-value work, I suggest this order:

1. Redesign homepage visual system and spacing
2. Redesign export page into a true output workspace
3. Unify workbench and compare visual language
4. Create a shared evidence component system
5. Standardize loading / empty / error states

## 13. Questions to relay back if the frontend lead wants alignment

Please relay these questions back if needed:

1. Should `/competition` be renamed at the router level now, or only re-labeled in UI first?
2. Does the frontend redesign want a full visual-system refactor, or a surgical polish pass over existing components?
3. Which page should become the visual reference page first:
   - homepage
   - workbench
   - compare
   - export
4. Does he want me to stabilize payload contracts first before he starts large-scale UI restructuring?

## 14. Final note to the frontend lead

The backend and data side are already strong enough to support a much better product surface.

The bottleneck is no longer "missing features". The bottleneck is product clarity, interaction quality, and visual system maturity.

If we align on a sharper front-end system now, this project can move from a capable engineering prototype to a credible high-end competition product.
