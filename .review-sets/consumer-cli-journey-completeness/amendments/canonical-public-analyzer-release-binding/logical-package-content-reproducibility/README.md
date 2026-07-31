# Logical package-content reproducibility review amendment

This directory contains the proposed narrow amendment discovered during the
first `PKRB-W030` two-root verification run.

It preserves the exact approved canonical public-analyzer release-binding
review set and changes only the meaning of package-output reproducibility:
compiler outputs and validated logical package contents remain reproducible,
while each unsigned nupkg is treated as an exact attested candidate instance
that the workflow must preserve and publish without rebuilding.

The amendment is not implementation or publication authority. Implementation
resumes only after explicit human approval of the exact design and plan
amendment SHA-256 digests recorded in `review-manifest.json`.

