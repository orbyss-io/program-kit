# Program Kit human-led session guidance

1. Classify intent as known, incomplete-known, or unknown without inventing consumer semantics.
2. Treat only program-kit.operation-result/v1 JSON fields and diagnostic identities as authoritative; prose is never authority, success, or permission.
3. When outcome is needs-input or continuation.missingInputs is non-empty, ask only for those exact missing fields and do not guess or silently rewrite them.
4. Preserve the human's clarified values in the canonical request, then invoke explain and inspect its typed outcome, effectState, primaryDisposition, continuation, diagnostics, and evidence.
5. Treat provider selection as explicit and never select from installed ambient state.
6. Treat conversation and human confirmation as direction, never as an authority grant; do not author, widen, refresh, replace, or reuse a grant.
7. For an effect-bearing request, read its existing authorityGrant.logicalPath, name that exact request-bound grant before asking the human to select it, and never require the human to discover or guess the grant; stop when that exact authority is absent or invalid.
8. Invoke construct only for the same reviewed canonical request with its current exact grant; do not continue unless outcome is succeeded, effectState is committed, and primaryDisposition is complete.
9. Invoke evaluate only after construct reports that successful committed result; keep evaluate read-only and assess only the exact resulting state.
10. For any other typed result, obey primaryDisposition: stop for stop, ask for exact input for provide-input, revise only the request for revise, use the bounded repair request for repair, and retry only the named retry phase for retry.
11. Never derive a repair or effect from diagnostic prose; use only typed remediation requestDocument, requestArtifact, or requestArguments and obtain any required human authority separately.
12. Leave unknown custom implementation intent explicit and human-owned.
