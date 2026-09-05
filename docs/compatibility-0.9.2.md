# Program Kit 0.9.2 compatibility report

0.9.2 is a governance-evidence correction for 0.9.1. It does not change application runtime APIs or
the meaning of the existing HIGH/CRITICAL blocking policy.

Existing completed lifecycle state remains readable. New successful completions add `reportFormat`,
`findingCount`, and `findings` fields to the schema-version-1 phase object; existing readers that
consume the established fields remain compatible. The complete Markdown report and its SHA-256
binding are still retained.

New analysis completions require the findings table already specified by upstream Spec Kit. Reports
that consist only of free-form prose are now rejected explicitly rather than guessed. A clean report
may use an empty findings table or a single row with placeholder identity fields whose summary is
`No findings`.

Malformed evidence no longer consumes the active analysis, so correcting only the report can retry
completion safely. A valid report with HIGH/CRITICAL findings still records a completed, non-ready
phase and clears the active run; remediation changes the governed artifacts and therefore correctly
requires a fresh analysis with new artifact hashes.
