# Release candidate 0.13.2

The owner lifted the publication hold on 2026-10-15 and authorized this session to
run `Invoke-LocalRelease.ps1 -AuthorizedCodexTask`, integrate PR #41 and publish only
after every mandatory gate passes. See [the patch migration](migration-0.13.2.md).

Public Foundation 0.3.5 and its successful tagged Release are verified before
qualification. Mandatory dependency refresh, both Host platform scans, current-source
CI, packaged consumer restart rehearsal and fresh local Release remain publication
gates. Published 0.13.1 migration history is preserved. The selected unfinished
consumer uses `fresh-feature-delete-v1`; this release session changes no consumer files.

Program Kit 0.13.1 remains the latest public patch until all gates succeed.
