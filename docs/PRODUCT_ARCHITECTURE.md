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

The frontend is Next.js, with Cloudflare Workers as the intended deployment target after adapter validation. The API is FastAPI/Pydantic/SQLAlchemy. Supabase PostgreSQL is the production database target. Production currently requires Redis for distributed provider controls and authentication throttling; a tested approved-stack replacement is needed before removing that requirement. Docker is used for reproducible deployment. The current runnable local persistence uses SQLite by default for zero-friction MVP validation.
