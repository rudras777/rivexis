# Operations

Built-in Cloudflare observability is enabled with query-string redaction. Supabase provides project health, logs and advisors; Brevo provides delivery logs. These facilities are not an independently staffed monitoring service, automatic alert guarantee or institutional SLA. Continuous DeFi risk email remains disabled; browser monitoring is explicitly bounded.

Record incident time/timezone, affected route and deployment, request correlation ID when supplied, status, provider and reproducible symptoms. Do not record cookies, tokens, password/verification links, private keys or unnecessary financial details. Correlation identifiers and monitoring coverage are not uniform across every retained service; that remains an improvement item.

Severity: **critical** means suspected credential compromise, unauthorized data access or materially wrong financial output; **high** means core/auth unavailability; **medium** means a supported workflow degraded with an honest failure state; **low** means isolated noncritical usability/documentation defects. Do not conceal unknown outcomes or call unsupported data healthy.

| Incident | Diagnose | Mitigate / recover | Verify |
|---|---|---|---|
| Application unavailable | DNS/TLS, gateway status, Worker deployment/errors | Restore compatible accepted Worker/gateway version | Both hosts, exact SHA, assets, private routes |
| Failed deployment | Provider build log, source identity, generated manifest | Stop promotion; correct build or restore accepted version | Full relevant checks and actual public identity |
| Database unavailable | Supabase health/logs, pool limits, quota acknowledgment | Withhold analysis; investigate provider; never invent local quota approval | Health plus owner-scoped read/write and fresh evidence |
| Authentication failure | Origin/callback/session configuration and sanitized status | Preserve identities; check current templates and canonical URLs | Approved test-account sign-in/session/logout |
| Verification email failure | Supabase Auth response and actual Brevo delivery event | Check sender/quota/SMTP configuration; no blind resend loop or reset | Real delivery and token verification, not API acceptance alone |
| Market-data outage | Provider timestamps/source identity, poll/reconnect state | Display unavailable/stale; retain provenance without interpolation | Genuine new observations and freshness transition |
| RPC outage | Chain/block/source errors and quota service | Fail closed; no fabricated model, hidden paid upgrade or unverified fallback | Supported fresh pinned snapshot and reconciliation |
| Unexpected calculation | Raw integer evidence, model identity, block and assumptions | Withhold affected results; reproduce with immutable fixtures | Independent reference and regression, then controlled release |
| Suspected credential compromise | Identify exposed credential/dependencies privately | Escalate; scoped approved rotation and dependent updates | Old credential revoked, dependent services recovered, no secret in report |

## Recovery scope

Git preserves source; provider version history supports application rollback. The 20 October protected database/Auth/Vault capture was restored and reconciled locally; its encrypted copy was round-tripped through the existing owner-only Drive folder on 23 October. The separate key was not uploaded. These are dated results, not a current backup, independent key custody, storage-object backup, second-machine/full-service reconstruction or proven RPO/RTO.

Do not read, upload, move or enumerate protected recovery contents while preparing ordinary source artifacts. Inventory storage objects/configuration independently before claiming a complete backup. Current restore freshness and founder-independent key access are outstanding. Treat RPO/RTO as **not yet validated**, rather than inventing targets that have not been tested.

Manual provider procedures and incident records should retain symptoms, diagnosis, mitigation, recovery and verification. See [deployment/rollback](DEPLOYMENT.md), [recovery evidence](docs/FRESH_RECOVERY_DRILL_20261020.md) and [supported-beta runbook](docs/SUPPORTED_BETA_OPERATIONS_20261020.md).
