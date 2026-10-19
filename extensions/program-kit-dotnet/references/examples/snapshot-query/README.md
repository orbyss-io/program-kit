# Immutable snapshot query lesson

This finite extension example complements the canonical .NET construction/query
guidance; it does not replace its rules or any provider contract. An explicitly
accepted immutable snapshot and repeated owner lookups justify investigating an
index. Keep exact ordinal identity, input ordering, duplicates and owner isolation.
Do not expose mutable result collections. Rebuild for changed input; live stores
and database queries need their own owner and proof.

`SnapshotQuery.cs` owns the index; `SnapshotScan.cs` preserves the scan alternative.
`Note.cs` owns the immutable input row contract.
`OwnerReport.cs` illustrates a later consumer application. `Program.cs` is an
independent fixed oracle plus a bounded comparison. `check.py` is an ordinary
explicit named-check adapter, never invoked by teaching or selection. Build uses
the selected .NET 10 SDK/BCL without external packages. A successful build does
not replace applicable consumer analyzers or source review.

Measure 8,192 immutable rows across 64 owners and 256 lookups, warm up, alternate
measurement order for five rounds, and retain all raw samples. Compare both
read-many performance and construction plus one lookup. Record runtime, machine,
configuration and managed allocations. That allocation count is not retained heap
or process memory. Include the indexing storage/preparation cost and the mutable
counterexample. Do not turn one machine's result into a universal rule.

Extend the existing `feature_context.CAPABILITIES` detector and `codingUnits`
contract for a new responsibility. This example's finite phrase is **immutable
snapshot query**. Bind source, version, context, exact actual checks, independent
invalid examples and limits through `coding_patterns.py`; use the normal composer
and reconciliation. Unknown applicability is a missing maintained adapter, not
support. Exact framework facts remain native evaluation; runtime identity belongs
in the check's declared inputs. Installed positive/negative execution is required
before any support claim. Manual editing retains every mandatory duty.

The F6 learning fixture uses these assets in a new fictional consumer, retains
the initial gap and applied source diff, qualifies exact versions and demonstrates
privacy-safe local shared preparation. Fictional review is not authenticated
authorship, observed agent obedience or human product acceptance.
