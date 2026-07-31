# Program Kit C# source quality gate — release-binding extension

Policy ID: `pkid:policy:program-kit:csharp-source-quality-gate`

Policy version: `1.11.0`

State: prospective extension activated only for
`PKRB-W010` through `PKRB-W080`

Base policy:
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`

Base policy SHA-256:
`e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`

The base policy remains fully active and unchanged. This revision adds one
release-closure obligation:

Release-binding qualification is executable private-gate evidence, not a
caller assertion. Controlled conformance fixtures reject:

1. random compiler-receipt influence on compiled bytes;
2. absolute source-root leakage;
3. nondeterministic package metadata;
4. descriptive, missing, or malformed selection digests;
5. divergent local and workflow package bytes;
6. declared but unobserved generated-output generator revisions;
7. caller-supplied Program Kit-internal digests; and
8. unknown release-binding fixture kinds.

These checks extend release closure only. They add no private analyzer to
consumer-owned source, change no public `PKCC` diagnostic semantics, weaken no
base-policy rule, and grant no publication authority.
