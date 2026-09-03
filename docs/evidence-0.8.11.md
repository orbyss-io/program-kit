# Program Kit 0.8.11 correction evidence

PriceCalculator reproduced the 0.8.10 defect with a reviewed Draft whose status was followed by a
blank line, `## Core Principles`, another blank line, and its first `###` principle. Draft validation
and review generation succeeded. Ratification then removed the complete second-level heading while
reporting success and hash-binding the unintended final content.

The cause was `\s` in the multiline Draft-status substitution. It matched the newline after the
status, and the optional remainder consumed the following heading line. The corrected expression
matches only the exact canonical status marker and uses a byte-preserving finalization path.

Regression coverage captures the reviewed constitution bytes, derives the two allowed replacements,
and requires the ratified file to equal that exact expected byte sequence. It also verifies the new
reviewed/final hash evidence, validates the resulting ratification, and proves that opening a recovery
draft preserves the prior ratification record without changing the constitution.

The PriceCalculator recovery check uses its original review-basis SHA-256
`32f631012c877843e748e73e085b8af57ef9192981d6cf1db2d8f50792a03f7f`. After restoring Draft status
and the missing heading, regenerating the packet must reproduce that basis before the user is asked
to ratify again.
