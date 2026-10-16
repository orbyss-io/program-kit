# Proposed N18: separate frontend product and test freshness where proven

Prepared 16 October 2026 for the consolidated additions queue. Consumer continuation D53 describes a conservative freshness-granularity inefficiency, not unsafe admission or a defective stale-input rejection. N18 is distinct from N3's human-review materiality: this concerns machine build/runtime input freshness and actual product artifacts. It remains proposed; neither the original plan/audit nor active implementation ledger is changed here.

## Evidence and attribution

The consumer reports that changing only its safe browser fixture/reporter invalidated frontend admission with PKC110 and stopped the current contract-verification path until supported native update rebuilt/restaged the frontend. It correctly preserved records and used normal refresh rather than editing receipts or bypassing admission.

Current canonical `prepare_hosted_pages.py:input_snapshot` independently confirms hashing every file under the configured frontend directory except node_modules, dist, .git, artifacts and __pycache__, then binding the frontend resource and repository Node/npm pins. Tests and reporters are therefore included unless they fall into an excluded directory. `admission` compares that complete snapshot and the compiled manifest hash. `build` binds the snapshot before running the actual npm build and checks it again before sealing, with prior revision history retained.

Current consumer package scripts separately define build (`tsc --noEmit` plus Vite) and test checks; its build tsconfig includes src, while browser tests use a separate config. Vite's configured entry is src/app.ts. These are useful source observations, not proof of an exhaustive independent build dependency closure or unchanged payload bytes after every proposed exclusion.

The exact OpenAPI failure route also needs attribution: current canonical and installed consumer `openapi_pipeline.runtime_target` already call `composition_render.verify_outputs(..., check_frontends=False)`. Do not claim all export entrypoints unconditionally require frontend admission or add another bypass flag. Trace the actual caller, preflight/closure verification and error observation from D53 before changing an integration dependency.

## Proper repair boundary

**Owners:** Program Kit frontend preparation/freshness, declared ownership/dependency model, affected verification and installed integration qualification. Existing C10 freshness guards remain enforced.

1. Establish actual product build inputs and build-validation prerequisites for the selected supported frontend recipe, separately from test execution inputs. Include source imports, generated client/types, entry/assets/HTML, branding/locales, compiler/bundler configuration, scripts/plugins, package manifest/lock, toolchain/producer identity and relevant shared inputs. A path called tests can still be imported, globbed, copied or executed by a build; its name is insufficient exclusion authority.
2. Provide an explicit owned, versioned dependency projection for supported cases. Fall back conservatively for unknown/custom/dynamic recipes rather than silently ignoring files. A shared config or dependency that affects both closures belongs to both. Preserve actual required build checks even if output bytes would be unchanged.
3. Separate product admission from current test evidence only where the model proves independence. A test/report-only change must invalidate and rerun the relevant tests, reporter/privacy checks and affected-input obligations even when an unchanged product artifact remains admitted. Unfiltered/release qualification still executes its required coverage against the actual candidate.
4. Bind and validate the projection/ownership policy itself so changing classification cannot conceal a product edit or renew stale approval/evidence. Migrate current receipts through supported regeneration. Preserve historical snapshots, receipts and prior revisions unchanged; never manufacture a new receipt from an unexecuted build.
5. Keep the build's before/after mutation detection and artifact/manifest checks. An optimized input set is safe only if omitted inputs demonstrably cannot affect the promised build or artifact; an unchanged revision string or a passing test count is insufficient proof.

## Required closure evidence

- An installed representative configured frontend builds and produces actual content-bound assets/manifest. A genuinely independent test-reporter edit reruns its owned checks without requiring unchanged product rebuild/admission; compare actual payload hashes and maintained artifact identity.
- Changes to every admitted product/config/lock/toolchain/shared input still invalidate the correct product closure. A test-directory file imported/copied by the build is treated as a product input or triggers explicit conservative rejection.
- Unknown/dynamic ownership, changed projection, missing/tampered receipts, changed manifest, generated-client changes and source mutation during a build fail honestly. Dual-role inputs invalidate both relevant closures.
- Test-only failures remain failures and cannot be hidden by reusing unchanged product bytes. Verify the actual contract/preflight route reported in D53; document its real dependency boundary without disabling required freshness.
- Migration preserves old evidence and frontend history. Central affected-input inventory and exact-candidate qualification cover the new split; there is no consumer-specific bypass or duplicate local freshness system.

Until implemented and qualified, the current supported rebuild/restage remains correct recovery. No product code, consumer state, receipt or live implementation ledger was changed by this collection task.

Later D73 attribution: its actual export log records PKC110. The early `runtime_target` exemption above is still present, but later `execute_contract` validates the runtime closure, whose `bound_content` composes the current shell with frontend admission enabled. This identifies a concrete later source path consistent with the failure. See [N23](maintenance-repair-addendum-N23-2026-10-16.md) for the separate producer/client/frontend phase cycle; N18 remains the narrower product/test freshness classification work. Neither finding authorizes weakening final runtime freshness.
