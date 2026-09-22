# Decision Engine

The Rivexis decision policy consumes normalized specialist-engine evidence. Third-party providers and individual engines do not directly choose the final product decision.

## Decision states
- **PROCEED**: manageable detected risk, adequate evidence/confidence, no critical blocker, policy compliant.
- **MODIFY**: material risk can reasonably be reduced by changing approval, size, collateral, leverage, route, protocol or concentration.
- **WAIT**: temporary risk, stale state, unresolved incident or material source conflict.
- **AVOID**: hard blocker or material risk exceeds policy limits.
- **UNKNOWN**: evidence is insufficient, unsupported or contradictory.

## Policy order
1. Validate applicable engine results.
2. Apply hard-blocker rules.
3. Determine applicable risk dimensions.
4. Aggregate material risk without blindly averaging unrelated dimensions.
5. Adjust confidence for data completeness, freshness and source conflicts.
6. Apply role/workspace policy and materiality when available.
7. Emit decision, confidence, reasons, failure modes, action and safer option.

Risk score and confidence are separate concepts. High-risk/high-confidence is valid; confidence must never be displayed as “percent safe.”
