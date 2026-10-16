# PdfPig 0.1.16 stream decoding boundary

Opening a document with strict parsing does not establish successful stream
decoding. In the selected public version,
[FlateFilter.Decode](https://github.com/UglyToad/PdfPig/blob/v0.1.16/src/UglyToad.PdfPig/Filters/FlateFilter.cs)
catches decompression errors and returns the encoded input. The native regression
reproduces that behavior. No existing Program Kit example was found promising
general PDF admission from that option; this is a selected-library limitation and
a missing integration boundary, rather than an attributed shipped parser defect.

Use the public [ParsingOptions.FilterProvider](https://github.com/UglyToad/PdfPig/blob/v0.1.16/src/UglyToad.PdfPig/ParsingOptions.cs)
and [IFilterProvider](https://github.com/UglyToad/PdfPig/blob/v0.1.16/src/UglyToad.PdfPig/Filters/IFilterProvider.cs)
seams. Keep strict parsing; do not patch publisher assemblies or introduce loader
workarounds. The optional [native reference example](examples/pdf-decoding/Program.cs)
uses public PdfPig 0.1.16 and SharpZipLib 1.4.2. Its latter decoder exposes actual
completion, checksum processing and remaining input; stream EOF or a manually
verified checksum alone is insufficient. The example pins/lock participate in
toolkit dependency maintenance. These packages are not added to ordinary consumer
projects by setup.

The example qualifies one direct FlateDecode/Fl stage, with no predictor or
Predictor=1 and the declared 32 KiB zlib window. It supports stored, fixed and
dynamic DEFLATE blocks within one exact RFC1950 envelope. It rejects incomplete
final blocks, all truncated prefixes of the exercised vector, bad checksums,
extra bytes and concatenated streams. Internal DEFLATE alignment follows the
decoder; no trailing byte padding is admitted. Other codecs, wrappers/chains,
predictors/parameters, preset dictionaries, indirect filter declarations,
ambiguous keys and unqualified windows remain unsupported. A different policy
needs its own fixtures and demonstrated envelope/traversal behavior.

Each operation owns a fresh provider and shared budget. Encoded input, per-stream
decoded output, cumulative decoded bytes and repeated decode calls are bounded.
Concurrent uses share atomic accounting. Failed/unsupported/exhausted work keeps
the operation incomplete; cached or repeated decoding receives no free allowance.
Cancellation and elapsed-time checks run between decoder calls. These are
cooperative checks: they do not interrupt a stuck decoder call and do not establish
process CPU, resident memory or address-space ceilings. Decoder internal memory,
PDF object allocation and unfiltered streams are outside the byte-budget claim.

The native PDF cases force ordinary page content and explicitly request decoded
image bytes. They prove that obtaining a page/image object alone can omit deferred
work. An unreachable malformed stream is deliberately not visited, demonstrating
the traversal limit. No claim is made about complete xref/object-stream, font,
CMap, forms, annotations, masks, attachments, renderer or every PDF feature.
An application must define and exercise its required traversal/adversarial corpus;
this example is not a general PDF validator or production worker.

Preserve result meanings. `InvalidDataException` identifies a malformed supported
stream. `NotSupportedException` identifies an unqualified surface, and
`InspectionUnavailableException`, cancellation, crash, resource exhaustion or a
supervisor timeout supply no successful admission result. Never turn these into
automatic OCR, model dispatch, fallback parsing or a paid-operation retry.
The consumer owns its domain policy and exact provider authority.

Run `python tests/validate_pdf_decoding.py` in the toolkit repository to restore
the exact lock, build and execute the required named native cases. Missing,
substituted or duplicate case identities fail. Unique results preserve source,
lock, actual SDK/platform, commands and both streams under `artifacts/pdf-decoding`.
Fixtures are synthetic; no user PDF, provider or coding agent is involved.

For production untrusted input, separately qualify the actual platform worker,
outer deadlines, real process memory/CPU enforcement, cancellation, descendants,
bounded output/draining and cleanup. A managed heap setting is not a demonstrated
process-memory limit. Keep any unavailable platform result explicit. The existing
Foundation Host/Nuplane satellite-loading closure remains independent and open
until its actual corrected public payload is qualified; this filter does not
repair that runtime boundary.

Decoder contract: [SharpZipLib 1.4.2 Inflater](https://github.com/icsharpcode/SharpZipLib/blob/v1.4.2/src/ICSharpCode.SharpZipLib/Zip/Compression/Inflater.cs).
