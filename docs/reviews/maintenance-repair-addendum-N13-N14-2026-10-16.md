# Maintenance addendum: N13 PDF decoding evidence and N14 build-recipe guidance

Prepared 16 October 2026. The user approved the original 43 findings and subsequently approved N12, bringing the authorized batch inventory to 44. N13 and N14 arrived afterward from the active consumer implementation chat. They are separately assessed proposed additions; they do not retroactively change the approved plan, its audit or implementation ledger. Adopting both yields 46 distinct findings.

No product or consumer code was edited by this assessment. The consumer is actively implementing; all local source observations describe the moment inspected, not a frozen acceptance baseline. Reported green tests are distinguished from independent execution.

## N13 PdfPig strict parsing does not prove successful stream decoding

### Evidence and cause

The consumer's continuation report records D32: selected PdfPig v0.1.16 catches Flate decoding failures and returns the original encoded input. Independent inspection of the exact public tagged source confirms this in [FlateFilter.Decode](https://github.com/UglyToad/PdfPig/blob/v0.1.16/src/UglyToad.PdfPig/Filters/FlateFilter.cs), lines 32–49. Consequently, absence of a thrown parse exception cannot establish that the relevant compressed data was successfully decoded. Opening a document and obtaining a page also cannot, by themselves, establish that deferred work was executed.

[ParsingOptions](https://github.com/UglyToad/PdfPig/blob/v0.1.16/src/UglyToad.PdfPig/ParsingOptions.cs), lines 54–56, exposes the public `FilterProvider` seam. [IFilterProvider](https://github.com/UglyToad/PdfPig/blob/v0.1.16/src/UglyToad.PdfPig/Filters/IFilterProvider.cs) supplies the filter-provider contract. These support adapting behavior without patching the publisher or introducing assembly-loader workarounds. The behavior is an actual selected-library limitation; whether prior Program Kit knowledge made an incorrect admission guarantee needs source attribution before claiming a specific shipped guidance defect.

Read-only inspection of the current consumer worker confirms a custom provider, bounded `ZLibStream` decoding, explicit header/checksum checks, limited ASCII wrapper support, attempts to force stream/image work, and failure for unqualified predictors/codecs. The continuation report describes OS process/CPU/address-space bounds, a managed heap cap and an outer deadline. This assessment has not run that worker or independently qualified those OS restrictions or the complete admission surface.

### Assess the local repair critically

The public extension seam and bounded execution are a reasonable approach, but they are not sufficient evidence for a general claim that a PDF is valid or safe. A manually verified trailer checksum alone does not establish an exact compressed envelope. Explicitly test truncated input, extra/concatenated streams, permitted end markers/padding, filter-chain ordering/aliases, predictor parameters, repeated decode accounting, and every supported wrapper. Reject unsupported cases honestly rather than silently broadening success.

Enumerating streams/images is evidence only for what the selected APIs actually expose and execute. Qualify the traversal and deferred work required by the declared admission scope, including relevant xref/object/content/resource/image paths, and the behavior of omitted or unreachable structures. Do not infer that one traversal covers every PDF feature. A general PDF validator is not implied by a narrowly qualified inspection operation.

Confirm actual worker isolation on each supported execution platform, cancellation, descendant termination, bounded output/draining, timeout classification and cleanup. A managed heap limit does not replace a demonstrated process-memory limit. Resource-limit, crash or uncertain decode outcomes must remain inconclusive/rejected for this admission purpose, with no automatic paid OCR/model dispatch. Keep the consumer's accepted domain policy and paid-operation authority separate from shared mechanism qualification.

### Planned handling and closure

**Owners:** Program Kit selected-version integration knowledge and central representative native examples; relevant publisher public seams if a confirmed generic gap requires them. Consumer-specific PDF acceptance, business policy and its worker remain consumer responsibilities unless a reusable capability is explicitly adopted through normal review. Do not copy a consumer parser into Program Kit or Foundation solely because this finding exists.

1. Trace existing selected-version PDF guidance and identify any actual overclaim. Document the exact library behavior, public seam, supported codec/envelope limits, deferred-execution boundaries and honest result meanings at the point of use. Correct confirmed misleading examples.
2. Supply a bounded representative integration/example and meaningful regressions for the shared advice. Test malformed Flate data that demonstrates catch-and-return behavior and prove the recommended public-seam adaptation rejects it. Test valid supported fixtures as well as unsupported codecs/predictors, corrupt checksums, truncation, expansion limits and relevant deferred data. Qualify the exact envelope and traversal claims, not just API calls.
3. Keep the actual domain's adversarial corpus and platform worker tests in the consumer. Central shared examples establish their stated boundary without duplicating the entire domain suite or claiming every PDF is supported.
4. Preserve the public runtime distinction: the previously selected Foundation Host integrates older Nuplane behavior; fixed Nuplane preview.111 packages already exist. A custom PDF filter does not repair or qualify the deployed Host's satellite loading. Retain the limitation until a corrected Foundation public package/image/knowledge closure is independently verified and adopted, as required by the approved plan.

**Closure evidence:** attributed correction or precise capability/knowledge disposition; actual selected public package integration; malformed/valid/unsupported/deferred and bounded-execution cases supporting each advertised claim; no hidden fallback, source patch, broader PDF guarantee or paid execution. Keep pending publisher integration and actual consumer acceptance explicit.

## N14 Custom-build rejection should identify the supported output-copy recipe

### Evidence and cause

The consumer report records D30: an initial custom publish/embedded-resource target was rejected by PKV003. The consumer replaced it with declared `buildProjectReferences`/`buildOutputCopies` and the existing generated build-output recipe, without an allowlist or waiver. It reports subsequent compilation passing with zero warnings; this maintenance assessment did not independently run that compilation.

Current Program Kit source independently confirms both sides: `repository_verification.py:file_items` rejects unrecognized custom target tasks with a generic evaluated-graph-adapter message; `build_output_recipe.py` already supplies a closed SDK-output-copy recipe whose derived nodes are recognized by that verifier. Its declarations require distinct graph-owned build projects, bounded copy rows, owned non-overlapping tools destinations and supported SDK output layout. This is a consumer scaffold correction plus a recovery/discoverability gap, not an invalid verification boundary.

### Planned handling and closure

**Owners:** Program Kit native verifier diagnostics, build/task authoring guidance and central installed-command validation; packages F/I/J of the approved plan.

1. Where applicable, identify the supported `buildProjectReferences`/`buildOutputCopies` recipe and its actual installed command in PKV003 recovery guidance. Explain the bounded intended use and link the current recipe documentation. Do not guess that every rejected target is convertible.
2. At task/scaffold authoring, expose the existing supported pattern before inventing custom packaging targets. Derive output ownership from the accepted graph, preserving native build/restore and runtime dependency semantics. Do not add arbitrary custom targets to the allowed-node set.
3. Keep evaluated graph/output adapters required for unsupported custom behavior, dynamic inputs and nonstandard SDK layouts. A helpful suggestion is not an automatic migration or permission to delete a custom target.
4. Centrally exercise the emitted instructions in an installed synthetic consumer: declare producer/copy inputs, render the recipe, execute native build/publish/pack, verify the actual owned outputs and prove the verifier recognizes only exact recipe-derived nodes. Tampered recipes, unknown tasks, external paths and stale graph/output declarations must still fail.

**Closure evidence:** actionable applicable diagnostic; executable current example; real native output/pack verification; unchanged rejection of unsupported custom behavior; no waiver, guessed custom-target conversion or consumer-specific duplicate toolkit suite.

## Coverage delta and handoff

| New finding | Disposition | Required evidence |
| --- | --- | --- |
| N13 PdfPig decode failures concealed | Selected-version knowledge/admission-boundary repair, precise shared example and domain/publisher ownership assessment | Real selected-package malformed/valid/unsupported/deferred/bounded cases; no unproven general validity or loader claim. |
| N14 Generic custom-task diagnostic | Preserve guard; expose the existing closed output-copy recipe when applicable | Installed recipe instructions and actual native outputs qualify; unsupported/tampered recipes remain rejected. |

The original 44-item implementation approval remains intact. These two proposed additions have source-reviewed handling and closure requirements, but have not been implemented or accepted by this assessment. Obtain/record their adoption separately and extend the live implementation ledger rather than rewriting the original plan or audits. This addendum grants no publication, device-installation, paid-provider or paid-worker authority.
