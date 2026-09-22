# Data Provenance

Every significant metric or finding should carry evidence metadata sufficient to answer: where did this value come from, when was it observed, what block/state did it refer to, how was it normalized/calculated, and how confident/fresh is it?

`EvidenceRecord` includes evidence ID, provider, source type, provider endpoint/request ID, observed/retrieved times, optional block/chain/asset/protocol references, raw reference, normalized value, calculation and engine versions, confidence, freshness and license classification.

Provider-specific labels and external risk conclusions retain attribution. An unlabeled address remains UNKNOWN ADDRESS; Rivexis does not invent entity identity.
