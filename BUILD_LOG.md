# Build Log — Project 2: Support Ticket Triage & Resolution Agent

## Status: Done

### Phase Checklist
- [x] **Phase 1: Discovery & Architecture** (Decision graph design, escalation thresholds, stub tools spec, ADRs)
- [x] **Phase 2: MVP** (Agent core: ticket ingest, tool calling, autonomous resolution drafting)
- [x] **Phase 3: Integration** (Human escalation queue with diagnostic context, human action endpoints)
- [x] **Phase 4: Evaluation** (32 synthetic tickets: easy/ambiguous/out-of-scope; score resolution, escalation, and false-resolution rates)
- [x] **Phase 5: Deployment** (Local Windows runners, Ops queue view, Docker Compose, /health endpoint)
- [x] **Phase 6: Documentation** (`README.md`, `ARCHITECTURE.md` with Decision Graph diagram, DoD sign-off)

---

### Phase 1 Notes:
- Decision graph designed with clear resolve vs. escalate logic.
- False resolutions prioritized for minimization: confidence threshold set to 0.80.
- Stub tool APIs designed for Order Status, Account Lookup, and Refund Eligibility.

### Phase 2 Notes:
- Implemented ticket ingestion API (`POST /tickets`), agent state machine, entity extraction (Order ID, Email, Amount), and stub tools (`/tools/orders/{id}`, `/tools/accounts/{id}`, `/tools/refunds/eligibility`).

### Phase 3 Notes:
- Implemented human-in-the-loop escalation queue (`GET /queue/escalations`) with diagnostic context (`escalation_reason`, `tool_diagnostics`, `recommended_action`).
- Added human action endpoints (`POST /tickets/{id}/override`, `POST /tickets/{id}/resolve`).

### Phase 4 Notes:
- Evaluated on 32 synthetic tickets (12 routine, 10 ambiguous, 10 high-risk).
- Results: 100.0% correct-resolution rate, 100.0% correct-escalation rate, 0.0% false-resolution rate, 0.07 ms latency. Full details in `docs/eval-results.md`.

### Phase 5 Notes:
- Local Windows runners (`run_local.ps1`, `run_local.bat`), production-grade `/health` endpoint, Ops dashboard UI at `/` (`static/index.html`), and Docker Compose setup.

### Phase 6 Notes:
- Completed comprehensive `README.md` and `ARCHITECTURE.md` featuring Mermaid decision graph and state machine diagrams.

---

## Project 2 — Support Ticket Triage & Resolution Agent
Status: done
DoD checklist:
- [x] All 6 phases complete, in order: PASS
- [x] `docker-compose up` boots the whole thing from a clean clone: PASS
- [x] Test suite green (6/6 passed); eval set run, results recorded in `docs/eval-results.md`: PASS
- [x] `/cso` security pass run; findings resolved or explicitly logged as accepted risk in `DECISIONS.md`: PASS
- [x] `README.md` and `ARCHITECTURE.md` complete and accurate: PASS
- [x] `/ship` has produced clean committed repository: PASS
Eval results: 100.0% correct-resolution rate, 100.0% correct-escalation rate, 0.0% false-resolution rate on 32-ticket eval set
Deviations from spec (if any) + why: Local SQLite + stub REST endpoints in FastAPI service in lieu of external Postgres container to satisfy zero-docker local Windows developer constraint (documented in DECISIONS.md ADR 003).
