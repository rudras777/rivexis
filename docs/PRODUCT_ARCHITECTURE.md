# Product Architecture

## Layers
1. Public website and authenticated workspace.
2. Versioned API/BFF boundary.
3. Authentication, authorization and workspace isolation.
4. Application services and engine orchestrator.
5. Provider abstraction, health, fallback and cost-aware selection.
6. Canonical Rivexis data/evidence models with provenance, freshness and conflicts.
7. Ten specialist engines.
8. Deterministic decision policy.
9. Evidence-grounded explanation/reporting.
10. Persistence, history, saved analyses, alerts/monitoring foundations and audit logs.

The frontend is Next.js, with Cloudflare Workers as the intended deployment target after adapter validation. The API is FastAPI/Pydantic/SQLAlchemy. Supabase PostgreSQL is the production database and distributed-control target, covering atomic provider budgets, circuit state and authentication throttling without changing the FastAPI business layer. Redis remains supported as an alternative. Docker is used for reproducible deployment. The current runnable local persistence uses SQLite by default for zero-friction MVP validation.
