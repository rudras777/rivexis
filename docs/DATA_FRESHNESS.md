# Data Freshness

Freshness is data-type-specific, not universal. A transaction-security signal may become stale within seconds; price/oracle observations may tolerate seconds/minutes; protocol fundamentals may tolerate hours; audit metadata changes much more slowly.

Statuses: LIVE, CURRENT, RECENT, STALE, EXPIRED, UNKNOWN. Data objects should carry observed_at, retrieved_at, block_number where applicable, provider, age and freshness status. Stale evidence must not be silently served as current, and material staleness can reduce confidence or change the final decision to WAIT/UNKNOWN.
