# Program Kit 0.8.11 compatibility report

0.8.11 is a ratification-integrity correction for 0.8.10. It does not change application runtime
contracts or the governed upgrade-record format.

The 0.8.10 ratifier used a multiline regular expression whose `\s` branch could cross a newline.
For the normal constitution layout, finalizing `**Status**: Draft` could therefore consume the next
blank line and `## Core Principles` heading. Validation and the human review packet ran before that
mutation, so they did not detect it.

The ratifier now operates on raw bytes. It requires one canonical Draft marker, derives an expected
final document by replacing only that marker and, for an initial constitution, the single pending
ratification date. It validates the expected document before an atomic replacement, verifies the
written bytes, and records the reviewed and expected-final SHA-256 values. Existing ratification
records remain readable.

Consumers affected by 0.8.10 must preserve the faulty ratification record as audit history, restore
the reviewed draft, regenerate its review packet, and obtain a new human ratification. They must not
edit the ratification JSON or proceed to architecture with the damaged document.
