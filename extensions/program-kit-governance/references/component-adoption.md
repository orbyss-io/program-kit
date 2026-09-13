# Apply selected component mechanisms

Foundation and Forms 0.2.0 are independent component releases. Select only applicable
mechanisms and verify the exact Program Kit combination before acceptance. Existing
wire and canonical identities must survive upgrades unless explicitly redesigned.

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
