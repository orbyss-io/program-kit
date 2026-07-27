# Orbyss.ProgramKit.Planning

Planning `1.0.0` and `2.0.0` remain registered and readable. Planning `3.0.0`
adds explicit static-conformance structure while preserving the existing plan
execution authority.

A v3 plan binds:

- one exact static-conformance disposition and its execution-routing state;
- an exact gate design and planned gate definition, selection lock, and
  activation evidence when applicable;
- every work unit as `gate-establishment`, `product`, or `closure`; and
- exact activation-matrix and verification-profile references for gated work.

Ordering is validated through explicit dependency paths, never inferred from
sequence numbers, names, paths, or allowed-edit text. Product and closure work
follow every gate-establishment unit, and closure follows every product unit.

The admission evaluator is pure classification for the existing executor. For
every state it first requires an observed disposition snapshot whose exact
identity, version, digest, and state match the plan. For create/extend it then
exposes only dependency-ready gate-establishment work until compatible
activation evidence exists. Reuse requires a compatible lock at preflight. An
exact accepted-empty disposition admits ungated dependency-ready work.
Blocked-unavailable admits nothing.

The v2-to-v3 migration requires one supplied classification for every exact
v2 work-unit ID and never fabricates a disposition or work-unit role.
