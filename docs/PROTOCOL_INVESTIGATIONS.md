# Protocol Investigations — P11

Protocol investigations are persistent workspace-scoped analyst cases built on Rivexis report artifacts. A case captures a normalized protocol event timeline at creation and can link one or more persisted protocol configuration reviews from the same workspace.

Case lifecycle: `open` → `in_review` → `closed`. Closing requires an analyst disposition. Notes, disposition, status changes, linked-review changes, and creation are auditable. Cases render as JSON, HTML, or PDF. Closure is an analyst workflow assertion and is not a certification that a protocol is safe.

Core surfaces:
- `POST /api/v1/protocol-investigations`
- `GET /api/v1/protocol-investigations`
- `GET /api/v1/protocol-investigations/{case_id}`
- `PATCH /api/v1/protocol-investigations/{case_id}`
- `POST /api/v1/protocol-investigations/{case_id}/reviews/{review_id}`
- `GET /api/v1/protocol-investigations/{case_id}/render`

The workspace UI is available at `/workspace/investigations`.
