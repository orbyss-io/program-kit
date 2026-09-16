# Apply selected component mechanisms

Foundation 0.2.2 and Forms 0.2.0 are independent component releases. Select only applicable
mechanisms and verify the exact Program Kit combination before acceptance. Existing
wire and canonical identities must survive upgrades unless explicitly redesigned.

For bounded architecture compatibility, inspect the installed
`examples/bootstrap-runtime` sources before inventing another host/port probe. They exercise
the published Foundation 0.2.2 image, two-shell replacement, compiled Core boundaries,
strict JSON, headers, OpenAPI and unchanged-bundle restart. They are synthetic mechanism
examples, not consumer implementation or proof that an unexecuted plan works. Copy only
applicable source files into a contract-bound scratch recipe with exact selected dependencies.
The Forms producer call signatures are also demonstrated by the publisher's
[release integration probe](https://github.com/orbyss-io/forms/blob/0841adcb924ca38db957b348cdbbd301472747e4/tests/Orbyss.Forms.ReleaseIntegration.Probe/Program.cs).
Missing source access or runtime-service inputs must be resolved before scheduling a proof;
an always-failing missing-input guard is not an executable compatibility handoff.

## Immutable Forms

Prefer `forms_immutable_release` for a form published at build time. Bind its producer
slot to a build project and frontend to the consumer package. The producer uses public
`DefaultFormCatalogService` create/review/approve/publish APIs with explicit identities,
times and evidence, then exports the actual immutable `FormRelease`. Test actors are
fixture data, not fabricated production approval. The build project does not activate
deployed management endpoints. `forms_management` remains a separate product choice.

Admit the exact release and artifacts against a trusted deployment manifest with
`admitFormRelease`, prepare `prepareJsonFormsRuntime`, then use the selected facade
(React: `OrbyssJsonForms`). Test invalid/conditional fields, supported renderer behavior,
submission and reload. A handwritten schema or form replacing these selected APIs
does not satisfy adoption. Forms 0.2 uses JSON Forms 3.8.0 and the approved Node/npm
context; metadata/strict graph verification remains required before planning acceptance.

## Foundation web and JSON

WebDefaults uses shell-local `Foundation:Web:ResponsePolicies` and explicit
`WebResponseMetadata` on owned routes. One response-start writer owns headers;
private/error/cookie responses remain no-store. Test endpoint policy selection and
failure behavior, not merely feature activation.

JSON endpoints explicitly obtain `JsonProfileCatalog.Get("strict-request")` (or the
appropriate accepted profile) and perform typed admission. `Json.AspNetCore` does
not configure global HttpJsonOptions or infer profiles from DTO types. Tolerant response
reading is a distinct boundary policy. Do not silently replace existing canonical
numeric/hash identity with the new canonicalizer during upgrade.

HostedPages supports typed public bootstrap, fixed encoded semantic HTML and admitted
immutable assets with Vite `mount(element, bootstrap)`. It does not support arbitrary
templates, private downloads or SVG branding. Program Kit's broader UI SVG allowance
does not imply HostedPages compatibility; use an allowed branding representation or
review a different adapter. Verify the actual hosted journey and asset admission.

## Evidence shape

`capability-adoption.json` dispositions every selected instance. Current instances name
owner, rationale and mechanisms. Each mechanism names publicApi, placement,
implementationPaths and checkIds from the feature's obligation design. Required
mechanism identities are defined by `scripts/capability_adoption.py`; remaining
compositions use `supported-public-mechanism` with substantive review.
Future-feature instances need an actual roadmapEntry, authority document and structured
duePhase. Delivery requires current targets, implementation paths, named executed
behavior and semantic review. Keep selected, materialized, activated and exercised
claims separate; none substitutes for the next.
