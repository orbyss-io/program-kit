# Program Kit 0.9.1 compatibility report

0.9.1 is a compatible desired-state and contract-correction release. Existing default BFF and SPA
Keycloak outputs remain byte-equivalent, but their template source is now composed rather than
subtracted from a union. Switching profiles removes the alternative client and profile-only files.

The BFF authenticated-user body adds a non-empty `issuer` and tightens `subject` from nullable to
non-empty. Standards-compliant OIDC sessions already provide both claims; a missing claim now fails
session establishment, while an anomalous old ticket is cleared with `401
authentication_identity_invalid`.

Unmodified legacy 0.8.x root web settings are removed automatically. Customized legacy blocks are
not guessed or discarded: synchronization reports a conflict before mutation so their values can be
moved explicitly. Valid consumer-owned configuration edits no longer require a state-refresh write.

The runnable-host schema change accepts the fields the 0.9.0 producer already emitted. Managed
workflows gain an optional fixed `eng/verify.ps1` consumer gate; repositories without it retain the
locked managed-build behavior.
