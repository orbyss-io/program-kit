# Intake analysis validation

Product source remained at `969ccf04d90e9a539df402836c810dc54349bd7b` on branch `codex/bootstrap-intake-analysis`. Tracked changes are review documents only. The report, scenario and transcript were fixed while Integrity and Affected ran. This note records their results afterward; the diagnostic manifests describe each run’s actual input snapshot.

| Execution | Result | Local diagnostic record |
| --- | --- | --- |
| `./scripts/Test-ProgramKit.ps1 -Python C:/Users/tech_/AppData/Roaming/uv/tools/specify-cli/Scripts/python.exe` | Seven checks passed; 7.511 seconds total | [Integrity results](../../../artifacts/validation-runs/20261023T182113Z-e45c38ee/results.json) |
| Prepared Python: `scripts/run_validation.py --suite Affected --changed-from 969ccf04d90e9a539df402836c810dc54349bd7b --engines=chromium,webkit` | Documentation-only changes selected seven integrity checks; all passed; 7.642 seconds total; no coverage gaps | [Affected results](../../../artifacts/validation-runs/20261023T182131Z-500f03fa/results.json) |
| Prepared Python: `scripts/run_validation.py --check validate_feature_knowledge --check validate_specification_intake --reason "Analyze existing scoped architecture projection and durable feature-intake confirmation before proposing bootstrap responsibility changes" --engines=chromium,webkit` | Both passed; 3.82 seconds total | [Focused results](../../../artifacts/validation-runs/20261023T181311Z-7a2b049e/results.json) |

The prepared interpreter is the existing Specify installation at `C:/Users/tech_/AppData/Roaming/uv/tools/specify-cli/Scripts/python.exe`. Temporary directories were assigned to the analysis worktree’s ignored writable temporary directory for these local runs. JSON Schema dependencies were prepared through the shipped pinned setup, without copying another runtime.

The installed consumer’s draft builder, draft-intake validator and proxy verifier passed. Its marker remains `full-intake`, `authority: none`, `independentLiveWorker: false`; the intake remains `draft`, and no bootstrap workflow exists. The explicit authority guard rejected promotion. The [preserved preparation and consumer archive](../../../artifacts/intake-sessions/2c3d70267d9f44058ab4e92b93f84dcb/REVIEW.md) was refreshed after the rehearsal with `finish --prepare-only --keep-workspace`. Its conversation status is `not-requested` because no separate interactive Codex session ran; the retained transcript is disclosed current-session proxy authoring.

The [scenario](scenario.md) and [transcript](transcript.md) are review copies of the fictional consumer input and proxy transcript. Original diagnostics, including failed attempts, are retained under `artifacts/intake-analysis/`. Full generated artifacts remain in the disposable consumer and preserved archive. They are local evidence rather than committed product fixtures.

These results support the structural and bounded behavioral observations in the report. They do not establish independent interview behavior, a completed bootstrap roadmap, a first specification, production correctness or human acceptance. No browser or device execution was needed for the documentation change and focused intake observations; the known local Firefox limitation was not exercised.
