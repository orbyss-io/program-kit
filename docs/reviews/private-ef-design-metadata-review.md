# Private EF Design metadata repair review

Program Kit checkout: `artifacts/worktrees/bootstrap-intake-analysis`, branch
`codex/bootstrap-intake-analysis`, baseline `d83156f4e7ac0e1235c923c25e2c5ae9afa67faa`.
At completion of this EF repair, the seven existing intake review changes retained
their original diff. The later authorized composition/constitution follow-up extends
some of those same owners; see [its review](composition-adoption-review.md). No private
application source was copied into this repository and no
consumer files were changed during this repair.

## Implementation owners

- Foundation's native descriptor producer is repaired in
  [Foundation PR 20](https://github.com/orbyss-io/dotnet-foundation/pull/20), commit
  `b0bc6e20b37755ea4e0fa28931f49674a331826e`, merged through
  `45b4d6cd60a8070e134a43ce2536be75d14e864d`. Those commits have the same source tree.
  Independent Build version `0.3.3` changes no runtime or EF version.
- Program Kit's [selected-root staging](../../extensions/program-kit-dotnet/templates/dotnet/files/eng/release_bundle.py)
  preserves private runtime roots, verifies tooling exclusions against package
  content identity, propagates consumed runtime/native asset roles and retains
  shared transitives and existing closure/freshness rejection.
- The [BFF baseline](../../extensions/program-kit-dotnet/templates/dotnet/web-profiles/bff-cookie/eng/web-profile.shells.json)
  selects the Json.AspNetCore feature required by BffCookie 0.3.7. The mechanical
  upgrade journey checks actual emitted and composed shell output.
- Four existing native PostgreSQL example files received readability refactors
  without changing their mapping, deployment or runtime responsibilities.
- [Focused native qualification](../../tests/validate_private_ef_metadata.py) and
  [synthetic fixtures](../../tests/fixtures/private-ef-metadata) cover packing,
  staging, migrations and published Host behavior. The existing validation
  inventory owns selection, prerequisites and budgets.

## Executed evidence

The original Build 0.3.2 failure was independently reproduced after successful
native compilation, packing and freshness sealing. Ordinary staging then reported
PKR014 for missing EF Design 10.0.13. Retained result:
`artifacts/private-ef-metadata/b34fb4a9ff904545a90762d0ed2ac1a5/results.json`.
Before public adoption, the final validator repeated that expected negative using
the then-emitted qualified Build 0.3.2 pin:
`artifacts/private-ef-metadata/7c9f0d2bad7c4e99ab22b266d75a613c/results.json`.

The prepublication Build 0.3.3 candidate archive SHA256 was
`aaf22d08d75b266321c6aaa606ef52ed136417b06b1f88dda67fff32fb9b68f0`.
Its positive result is
`artifacts/private-ef-metadata/fa0d9d1e461743039c6bb375ae8cc2f8/results.json`:
32 successful recorded steps totaling 33.987 seconds, with 234 unchanged source
inputs. It proves fresh native metadata/packing, ordinary integrity-validating
staging, native EF authoring/deployment/model drift, stable migration history,
separate database identities, exact published Host activation, private/shared
Newtonsoft execution, real BFF antiforgery token/cookie handling, HTTP write/read
and an independent SQL observation. Host, network and database cleanup succeeded.
This development archive is not the publication artifact.

The exact tagged CI artifact was subsequently downloaded and its archive digest
verified as `f67704e3f6cb85112bb144b9530b4960de6a90f04476af3307ec25cae1abe257`
(Actions artifact `12682250104`). Its Build package SHA256 is
`2ad9578d4b98fe5717ce536f3c4139c3ce751bd00ccf687e9dce697f72722595`,
with repository commit `b0bc6e20b37755ea4e0fa28931f49674a331826e`.
The same full native scenario passed against those exact package bytes:
`artifacts/private-ef-metadata/4d1566b7c8d44234bcf6edf07320f103/results.json`.
The public registry and profile-adoption claims were qualified separately below.

The final positive run used the newly promoted default with no version override
and no local candidate feed:
`artifacts/private-ef-metadata/8230adba2ccc4ed7b46eee87c4d6261a/results.json`.
All 32 recorded steps passed (58.649 seconds for the complete validator). Its fresh
NuGet cache contains the signed public Build 0.3.3 archive, SHA256
`1f1c846976a4446d8c1ac9f82e4294bb1e08943833102aa4535c2197e876284b`.
The same native descriptor, private/shared runtime, EF deployment, HTTP/database
and BFF checks passed; all 234 source inputs remained unchanged. Host, network and
PostgreSQL cleanup succeeded. `public-package-observation.json` beside the result
binds the actual restored public package and absence of a local candidate feed.

Independent final review compared all 234 source hashes, raw migration bytes,
installed staging-tool parity and the emitted BFF activation, then inspected the
retained positive and negative streams. Eight semantic migration mutations reject;
layout-only changes remain accepted. Review found no remaining material issue in
this bounded patch; it did not independently rerun the Host.

Local validation records before public profile adoption:

| Check | Result | Record |
| --- | --- | --- |
| Integrity | 7 passed, 8.016 seconds | `artifacts/validation-runs/20261026T191211Z-9c0ab2ca/results.json` |
| Affected | All 29 executed checks passed, 193.695 seconds; aggregate needs-attention for three explicit manual selections | `artifacts/validation-runs/20261026T191248Z-2df35c1c/results.json` |
| Native release-bundle regressions | Passed, 44.330 seconds | `artifacts/validation-runs/20261026T191249Z-6a788d76/results.json` |
| Archive build and installed intake | Passed, 3.268 and 10.288 seconds | Same explicit-selection record |
| PostgreSQL lifecycle | Passed, 103.751 seconds | Affected record |

The manual native EF check was executed with an explicit candidate archive above.
Its default derives the Build pin from actual emitted qualified output, rather
than the historical raw-template fallback. Earlier setup, generated-migration and
Docker-mount/antiforgery failures remain retained separately; later success does
not relabel those failures.

Final validation after public profile promotion:

| Check | Result | Record |
| --- | --- | --- |
| Integrity | 7 passed, 7.466 seconds | `artifacts/validation-runs/20261026T203046Z-1756a224/results.json` |
| Affected from the stated baseline | All 34 executed checks passed, 330.966 seconds; no unknown coverage gaps or source changes | `artifacts/validation-runs/20261026T203106Z-72e7ffed/results.json` |
| Public-default EF/Host, archive build, installed intake | All passed, 72.671 seconds total | `artifacts/validation-runs/20261026T203105Z-812d2f1b/results.json` |
| Actual archive-installed .NET extension | Passed, 19.797 seconds; emitted Build 0.3.3, BFF Json activation and exact release-helper parity | `artifacts/ef-design-repair/final-installed-archive/results.json` |

The Affected runner retains `needs-attention` for its three explicit manual
selections; this is not an overall green suite assertion. EF and archive selections
were executed in the final explicit record; the unchanged native release-bundle
graph implementation passed its earlier explicit record above. All executed checks
stayed within their individual budgets. The final archive result records exact
archive hashes. Native installation used synthetic disposable projects only.

## Publication, adoption and limits

[Foundation CI 40383572388](https://github.com/orbyss-io/dotnet-foundation/actions/runs/40383572388)
passed Windows and Linux, including both candidate image scans. The independent
[Build release workflow](https://github.com/orbyss-io/dotnet-foundation/actions/runs/40386221991)
owns exact tagged package validation, publication and public propagation. A pushed
tag alone supplies no publication claim. Program Kit adoption additionally uses its
existing public profile preparation, qualification and promotion owners; historical
profiles and consumer locks remain intact.

The release run initially failed with PKN002 after its 900-second public-propagation
wait. Package validation and upload succeeded, but the retained observation at
2026-10-26 19:46 UTC still returned HTTP 404. Knowledge publication was skipped.
The failed run, streams and original status are preserved under
`artifacts/ef-design-repair/`; that run remains failed.

After the publisher confirmed availability, a fresh public download and the native
`verify_nuget_publication.py` check succeeded. Public package SHA256 is
`1f1c846976a4446d8c1ac9f82e4294bb1e08943833102aa4535c2197e876284b`.
All 17 nonsignature ZIP entries are byte-identical to the exact uploaded CI
package; NuGet added its repository signature. Recovery executed only the skipped
knowledge-publication step, attaching the retained asset with SHA256
`e783e5a3d577245774fc37a6befc8f2da62684f48a2d92c93acace6a77b5d599`
to the [unchanged Build tag's release](https://github.com/orbyss-io/dotnet-foundation/releases/tag/build-v0.3.3).
There was no rebuild, repeated upload, tag replacement or version bump. The separate
`artifacts/ef-design-repair/release-recovery.json` records these later observations.

The ordinary `update_dependency_profiles.py prepare`, `qualify` and `promote`
owners qualified and promoted the new default:
`foundation-0.3.7-build-0.3.3-exporter-0.2.7-forms-0.2.1-localization-0.1.2`.
Only Build changed from 0.3.2 to 0.3.3. Fresh native qualification covers 49
activation closures and four combinations, plus wrong-producer rejection
(`artifacts/profile-update-native/a88095c8`). Fresh public Host qualification
passed five cases (`artifacts/bootstrap-runtime/1cdea88d`). The portable receipt
SHA256 is `84d746461cc960adca35838ec98cf8d86066cbd4b255de22e374f39a5867ecfe`.

The maintainer disposition retained the original unchanged Forms browser evidence
from the directly executed 0.3.5 profile. All 17 fixture/toolchain inputs and npm
artifacts remain unchanged. This preserves original Chromium/Firefox/WebKit
coverage and claims no fresh browser execution. Firefox remains unavailable on
this Windows host. All 11 historical profile entries and 47 immutable direct
references preserve their original hashes. The new public knowledge capture has
33 package records and 461 source documents, with all indexed hashes verified;
Build graph, targets and README come from the released source. Contributor review
journals and AGENTS were excluded. Commands and installed-default inspection are
retained at `artifacts/profile-adoption-build-0.3.3`.

Consumer requalification and workaround retirement remain separate: the original
private consumer has not been changed by this repair. Program Kit remains
uncommitted and unpublished. Exact-source package CI and a maintainer disposition
of the separate upstream asset-admission finding remain release work.

The native migration proof includes an explicit readable review adaptation of the
retained EF-generated Up/Down operations. It preserves native identity, designer
and model snapshot. It does not establish unchanged generated-code readability or
human acceptance.

A separate published Nuplane fallback admits EF's analyzer-only DLL into feature
discovery, where CShells logs a recoverable missing-Roslyn warning. The EF and BFF
features nevertheless activated and executed. The precise package, restore,
descriptor and stream evidence is retained beside the positive result in
`interop-observation.json`. This repair does not claim to fix Nuplane's tooling
asset admission, and adds no Roslyn runtime requirement.

See [maintenance and workaround retirement](../maintenance/private-ef-design-metadata.md)
for the maintained contract and sequencing. Consumer requalification must exercise
the corrected producer with its temporary hook absent before the original
consumer's local repair target/script are retired. Program Kit commits, pushes and
publication remain separate from the authorized independent Foundation release.
