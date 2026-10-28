# Program Kit 1.0 preview

Program Kit adds product and architecture intake, relevant engineering knowledge and optional
helpers to native Spec Kit phases. It no longer supplies a second bootstrap or delivery lifecycle.
Human review remains part of the conversation and normal authored documents.

This preview is selected explicitly; it does not replace the latest stable release. The 0.x to
1.0.0-preview.1 transition requires deliberate re-onboarding in a fresh checkout. Preserve the
original project and bring useful architecture, ADRs, journeys and product documents into intake.
Old workflow state and approval receipts are not converted into new authority.

Future preview updates preserve authored product/specification work, application files and native
dependency locks. Toolkit customizations are preserved or refused for explicit reconciliation.
Publication requires native approval of the exact verified package bytes.

## Native BFF session renewal correction

The qualified Foundation 0.3.9 profile includes the native correction for late renewal
recreating a session after logout or idle expiry. Session creation stays separate from
renewal; the original absolute deadline and shell isolation remain enforced. Both native
sliding renewal and explicit renewal have deterministic native and browser regressions.
Published BFF 0.3.8 is affected; retained historical qualification does not establish
this revocation guarantee. Adopt the corrected profile through the supported compatibility review.

The default in-memory cache needs no application-owned authentication replacement.
Custom distributed cache adapters must implement Foundation's atomic
`IBffSessionTicketCache` capability before adopting this runtime. Existing profiles and
consumer locks remain preserved; a toolkit refresh does not migrate application dependencies.
