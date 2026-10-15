# Program Kit 0.13.2 preparation and validation

The owner lifted the earlier publication hold on 2026-10-15 and authorized this
session to run `scripts/Invoke-LocalRelease.ps1 -AuthorizedCodexTask`, integrate
[PR 41](https://github.com/orbyss-io/program-kit/pull/41), tag and publish only after
all mandatory gates pass. No paid workers, interactive intake, consumer checkout
changes, device installations or new automation are authorized by this work.

## Preserved handoff results

- [CI 38705842587](https://github.com/orbyss-io/program-kit/actions/runs/38705842587)
  passed on `d88f5bd428588e763b69ed44c79494ccd3e78694`, including Linux/Firefox
  and Windows checks. This is repair-source evidence before the new dependency closure.
- [Dependency update 38702683156](https://github.com/orbyss-io/program-kit/actions/runs/38702683156)
  failed on older `801e9f5dc6be5e755130ad6c16ad7ace007edfe7`. Qualification,
  deterministic checks and Host scanning passed, but GitHub rejected the generated
  branch push because the Actions token could not update workflow files. The job
  remains failed and is not final-source acceptance. Its log, job metadata and full
  uploaded artifact are preserved under `artifacts/tests/patch-0.13.2/`.
- Cancelled dependency run 38701630051 remains cancelled; its available log and
  job metadata are preserved separately. Earlier failures and evidence remain intact.

The current maintenance pins were refreshed locally from public metadata, including
the workflow pins, before dispatching the new qualification. This removes that
specific workflow-write requirement from delivery of the new tested profile.

## Independent public Foundation verification

Foundation [v0.3.5](https://github.com/orbyss-io/dotnet-foundation/releases/tag/v0.3.5)
is public at source `ff091a2be8daab217291efe5309d2289567339c8`. Its complete
[tagged Release 38716632596](https://github.com/orbyss-io/dotnet-foundation/actions/runs/38716632596)
succeeded, including browser qualification, packaged Host/PostgreSQL consumption,
both prepublication image security scans and publication. The annotated tag was
independently dereferenced to that source.

Downloaded public `foundation-knowledge.json` SHA-256:
`77aaa3a20fbb9b24085e582f58a116a2ebd8a7ec2a2d7003ad88efff82181d28`.
Every unsigned payload file in all 30 public NuGet packages matches the knowledge;
package versions/repository commits match 0.3.5/source above. All 128 embedded
document/Host fact hashes were checked. Registry signatures are excluded from the
publisher's payload comparison, as defined by its knowledge contract.

Public immutable Host:
`ghcr.io/orbyss-io/foundation-host@sha256:cbe7b57dc71e1f7931b72d1c0447668b840f395c320afc5f4dcffd4c86c3f973`.
Independent public manifest inspection resolves Linux amd64 to
`sha256:7ecd5639463ab5a72c77b11f699e0dec06b897001c4757d902e50c70439aadc4`
and Linux arm64 to
`sha256:13a51acb6a0de0b1b47d98a93f464a2d20ce431537a4cfbcd23e9bd352922279`.

The image's actual dependency manifest binds all five Nuplane packages to
`1.0.0-preview.109`. Every recorded SHA-512 matches its public Feedz archive.
The actual image's `Nuplane.Loading.dll` equals the public net10.0 assembly;
SHA-256 `4f4bf32c9b0c74b029bbde2ad21976b36b293f220c2363a2621e8767fdf89a46`.
The never-started inspection container was removed after extracting these files.

Public Nuplane `0.0.11-preview.108` binds source
`b7eb09097686afaca63a068104d191dd41911b0a`, the multi-assembly loading repair
in PR 133. Public `1.0.0-preview.109` binds its direct successor
`79b2bb6fbdd56aec088489cfba9fc8b942920f52`; the only intervening commit restores
the 1.0.0 package version line and adjusts an isolated test. Production loader
files are unchanged. Thus the published Host contains the original repair through
the successor package version. This establishes its contents, not fitness for
adoption: the later regression below blocks selection of this closure.

Exact downloaded public files, package hashes, source comparison, extracted Host
evidence and the Foundation Release log are retained in
`artifacts/tests/patch-0.13.2/upstream/`. This establishes public availability;
Program Kit adoption still requires its own complete qualification and security gates.

### Later revert and independently reproduced regression

The owner correctly identified the subsequent revert. Nuplane PR 135 merged
`d83b6fcb771a8bed878025a2948b0023dd2b0bce` at 10:01:26 UTC on October 15,
after the 109 publication at `79b2bb6`. The 109 package still contains the
original repair, but also the satellite-resource regression that caused the
revert. PR 136 (`fa70b60f09fea7138aad5bd46c1187ef1e99d1ea` at inspection)
restores multi-assembly loading with culture-aware resolution. Its CI passes,
but it remains unmerged/unpublished and cannot be adopted as source.

An independent ignored probe compiled against the extracted, unchanged public
Host assemblies and used only `NuplaneHostIntegratedLoader.LoadActivePackagesAsync`.
Its actual loader hash equals the image/public-package hash above. With real
public PdfPig 0.1.16 it loaded all seven assemblies, without a `PdfPig.dll`, and
opened a synthetic one-page PDF. A separate process loading real public
System.CommandLine 2.0.0-beta4.22272.1 reproduced conflicting identities for its
different-culture satellite assemblies. Both outcomes are preserved under
`upstream/runtime-probe/`; the initial compilation against internal types
remains a failed diagnostic and was replaced with the supported public API.

Foundation 0.3.5 is therefore **not adopted**, even if its current Program Kit
qualification succeeds. Publication waits for an independently verified corrected
Nuplane release, public Foundation Host/package/knowledge closure, both image
scans and fresh Program Kit qualification. No unpublished branch substitutes for
that gate. The passing PdfPig observation does not waive the satellite regression.

## Migration and current gates

Published `migration-0.13.1.md` was restored byte-for-byte from its public asset and
checked against the published tag. SHA-256:
`89ca98c3149a8ae3505458e364de415ee2e1e4800606325b499ee40f732beeb8`.
All published history entries were retained; unpublished diagnostics guidance moved
to `migration-0.13.2.md` and its semantic introduction moved to 0.13.2.

The new semantic change selects `fresh-feature-delete-v1` and supersedes old
continuation/archival routes. Ten focused release-guidance cases pass, including
upgrades from 0.12.5, 0.12.11, 0.13.0 and 0.13.1 plus historical-target retention.
The sandboxed attempt failed to create temporary fixtures; the separate run with
normal temporary-directory access passed. Both logs are preserved.

Current preparation source is `d1d31cb134db7426f63a038796f8f6a9456079a6`.
[Dependency update 38728296943](https://github.com/orbyss-io/program-kit/actions/runs/38728296943)
and [CI 38728301173](https://github.com/orbyss-io/program-kit/actions/runs/38728301173)
were dispatched on that source. The latter failed on its PR merge test commit
`8b5bad5acf4edb6e1ee161cfcdb8682134ad57db`; Windows passed. The preparation
commit has refreshed manifests but not the update job's regenerated locks/default
catalog, so UI/bootstrap checks reject Playwright manifest/lock mismatches and
effective-context checks reject active exporter 0.2.6 versus old catalog 0.2.5.
Dependent checks remain blocked, not passes. Native composition preparation also
failed; its available outer logs are preserved, and inner-cause acceptance awaits
fresh coordinated closure verification. No assertion was loosened. The full CI
artifact and log remain under `artifacts/tests/patch-0.13.2/ci-38728301173*`.

The dependency run is still executing its own coordinated deterministic checks;
its final outcome remains to be recorded. Its Foundation 0.3.5 proposal cannot
be adopted because of the independently reproduced regression above, regardless
of its test outcome.

The user installed Spec Kit 1.2.0, Node 26.12.0 and npm 12.2.0 in their own
terminal. The maintained readiness wrapper subsequently passed with the actual
shared selections; installed .NET 10.0.402 was independently observed. No agent
installed device software. All three maintained npm locks were refreshed natively;
historical profiles and consumer locks remain unchanged.

Focused tests with the updated shared toolchain pass: 48 story/reset cases,
21 task cases and 10 migration-guidance cases. The updater's obsolete generic
continuation message now routes consumers to the verified migration plan and its
selected method. The patch guide includes exact reset preview/apply commands.

An explicitly unpublished package built under
`artifacts/tests/patch-0.13.2/pre-upstream-bundle/` passed the real sequential
consumer updater/reset/destination activation exercise. New evidence is in
`artifacts/consumer-upgrade-package-runs/fd909174fa414fe1b9dac4df74a97259/` and
`artifacts/tests/patch-0.13.2/packaged-restart-updated-tools.log`. It retains
confirmed fictional intake/shared inputs, deletes selected old work without a
content archive, consumes fresh installed phase contracts, refreshes installed
integrations, and proves destination failure recovery and later activation.
The prior 0.13.1 summary was copied unchanged before the maintained summary path
was updated. No coding agents or actual ClaimEvaluator changes occurred.

This is a pre-upstream rehearsal, not final-profile acceptance or a Release
receipt. Fresh bounded Development, final-source CI and the complete local
Release remain due after corrected public upstream adoption. No local Release
receipt has been created for 0.13.2 at this point.
