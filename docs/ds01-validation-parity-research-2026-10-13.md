# DS01 name validation parity and proposed generation

## Root cause and current status

This is diagnostic 28. Reported native maxlength truncation is a consumer UI data-loss and feedback defect, not evidence that the server accepts overlong normalized names. Current `web/src/policies/collection.ts:16–17` no longer sets maxlength. Both that file and `PolicyCreationInput.cs` are untracked, so Git cannot date the change. Retained failed/later-passing logs do not prove the current deployed bundle. No Program Kit source has been shown to generate the offending assignment.

Existing `ds01-collection-read.spec.ts:31–37` inserts 121 characters and asserts retained input, invalidity and no admission. It does not prove real clipboard paste, normalized boundaries or cross-runtime parity.

## Executed synthetic evidence

A disposable Chromium page with real clipboard Control+V received space + 120 letters + space. An unrestricted input retained 122 raw units and 120 normalized units. With maxlength120, only 120 raw units and 119 normalized units remained: valid intended content changed before application validation. This is synthetic browser evidence, not current consumer acceptance. [Scripts and actual results](../artifacts/tests/validation-parity/README.md) contain no consumer data and changed no consumer source. The [HTML input constraint](https://html.spec.whatwg.org/multipage/input.html#attr-input-maxlength) applies to the raw value, not the application's approved normalization.

Current Core calls .NET Trim, measures UTF-16 length1–120 and rejects remaining controls. Browser separately calls JS trim, measures UTF-16 length and rejects C0/C1. Their trimming is not equivalent:

| Raw input | .NET | JavaScript | Consequence |
| --- | --- | --- | --- |
| U+0085 followed by A | Trims to A and accepts | Retains control and rejects | Admission differs |
| U+FEFF followed by A | Retains U+FEFF and accepts | Removes U+FEFF and accepts | Digest-bound content differs |
| TAB followed by A and LF | Trims to A and accepts | Trims to A and accepts | Boundary controls currently accepted |
| A, U+0085, B | Rejects | Rejects | Interior control rejection agrees |

The framework check used local .NET10.0.11, not the selected consumer10.0.12 API. Selected-server parity still needs execution. The trim-set distinction is documented by [Microsoft](https://learn.microsoft.com/en-us/dotnet/api/system.string.trim?view=net-10.0) and [ECMAScript](https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html#sec-white-space).

## Current constraint propagation

Spec A-03 and the data model say trimmed names1–120 characters without defining the count unit. The planned wire schema has ordinary minLength/maxLength. Actual request DTO, OpenAPI and generated TypeScript expose plain strings without executable normalization-aware validation. Browser request/response guards and Core repeat the rule. Architecture labels, parsing and generated types do not supply business validation.

Captured Foundation0.3.3 JSON exports parsing/serialization profiles and budgets, not arbitrary domain normalization. HostedPages leaves form behavior with the application. Pinned Forms0.2.1 supplies strict AJV2020 standalone generation and a facade for supplied validators; its inspected build registers localization metadata keywords and rejects an unknown trim keyword. Schema maxLength120 accepts61 emoji (122 UTF-16 units), which current Core/browser reject. Ordinary [JSON Schema maxLength](https://json-schema.org/draft/2020-12/json-schema-validation#name-maxlength) counts Unicode code points. The qualified package profile matches the accepted catalog, but the consumer has no Forms browser dependency. Adding the full runtime would not repair this mismatch.

## Proposed supported path

Retain one consumer-owned pure rule definition. An owned build tool exports an immutable descriptor from the actual Core rule: identity/version, normalization ordering and exact trim set, length unit/min/max, control rejection and safe error identities. Server admission consumes the same owner definition; the metadata is not separately hand-authored. Serialization belongs to the build adapter, preserving Core purity.

A small Program Kit generator produces the matching TypeScript normalizer/validator and field-bound metadata. Requests/digests use that normalized result; raw input remains available for correction. Response guards validate canonical stored values without rewriting them. Export via an explicit artifact or OpenAPI extension, without claiming normalized UTF-16 bounds are ordinary raw maxLength.

Initially support only a qualified declarative label subset, rejecting unsupported descriptors/versions. Avoid arbitrary C# inference, script-valued metadata, a universal rules engine or a Foundation business-validation interface. Existing Forms can consume a qualified supplied validator when selected; these two fields need no new runtime dependency. Shared metadata removes independent rule declarations; actual Core-versus-generated-client parity checks still prove the runtime implementations agree.

## Consumer repair and regression coverage

Preserve the full browser-entered value within the text control's normal representation. Validate the approved normalized value, show accessible field-level errors and block admission/create while invalid. Never substring or apply normalized limits as raw maxlength. Server validation remains authoritative. Trimming/control/count changes require explicit product decisions and ordinary compatibility review.

Required regressions cover real clipboard paste with complete retention/error/zero requests; normalized119/120/121; raw lengthabove120 that trims to120; empty/whitespace; boundary/interior controls; NEL/FEFF/NBSP; emoji and combining marks; equal Core/generatedJS normalization and digests; stale generated artifacts; and field/focus behavior. Direct invalid create requests must leave no new policy/receipt or changed acceptance state, proved independently in PostgreSQL. A preexisting admission used to test create is distinct from a new policy effect. Shared vectors complement independent oracle cases.

## Classification and grilling

Consumer implementation/parity mistakes and missing form/source-review guidance are confirmed. A particular scaffold cause is unproven. The inspected paths lack normalization-aware consumer-rule export and matching validator generation for these semantics: a narrow Program Kit integration/generation capability gap. Foundation need not own business rules, and Forms already supplies generic schema validation.

The requester accepted Q6–Q8: Core-owned export supplies matching browser generation; controls reject anywhere in raw input before trimming; UTF-16 length counting remains unchanged. Rejecting boundary controls is an intentional behavior correction and requires normal compatibility handling rather than baseline resets. The narrow generation capability is now being implemented and qualified; real-consumer corrections remain separate. Prior Q5-approved implementation continues independently.
