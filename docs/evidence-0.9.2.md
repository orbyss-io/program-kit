# Program Kit 0.9.2 correction evidence

PriceCalculator reproduced the 0.9.1 defect with a truthful canonical report containing the
standard Spec Kit findings table and no actionable rows. Its metrics explicitly recorded zero
blocking and non-blocking findings. The lifecycle nevertheless returned `PKL009` because it searched
the entire Markdown document for bare severity words and interpreted explanatory labels as findings.

The corrected parser treats the upstream Spec Kit findings table as the sole machine-readable
region. It requires exactly the columns `ID`, `Category`, `Severity`, `Location(s)`, `Summary`, and
`Recommendation`, accepts an empty table or one explicit `No findings` sentinel, validates every
finding row, and persists structured finding objects, count, severity set, report format, report
path, report hash, and artifact hashes in lifecycle state. Surrounding Markdown remains complete
human evidence but has no classification authority.

Regression coverage proves:

- the unchanged PriceCalculator report parses to zero findings;
- zero-count metrics and severity names in headings, legends, and prose do not create findings;
- genuine MEDIUM/LOW rows are recorded and remain ready under the current policy;
- genuine HIGH/CRITICAL rows are recorded and block implementation;
- missing, duplicate, invalid-severity, mixed-sentinel, and malformed rows fail with `PKL017`;
- report-format failures preserve the active analysis and can be corrected and completed in place;
- a structurally valid blocking report completes the analysis and clears `active`, allowing changed
  artifacts to begin a new hash-bound analysis.
