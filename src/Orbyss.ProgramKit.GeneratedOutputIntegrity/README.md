# Generated-output integrity

This package owns the host-kind-neutral integrity boundary for Program Kit
generated application roots.

Every generated root contains
`.program-kit/generated-output.manifest.json`. The manifest records every other
generated file by normalized relative path, byte length, and SHA-256 digest. A
sibling `<root>.program-kit-generated-output.anchor.json` seals the exact
manifest bytes without creating a self-hash exception.

Verification is offline and does not regenerate. It reports every observable
modified, missing, unexpected, unsafe, malformed, or unsealed path with the
explicit prefix `Tampered-with Program Kit generated output`. Files outside the
generated root are consumer-owned and ignored.

Generated roots and their external anchors are build and publication inputs;
they are not checked at application runtime. Ordinary drift is preserved for
review. Recoverable publication transactions complete only previously sealed
bytes and never adopt edits from a generated root.
