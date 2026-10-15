[CmdletBinding()]
param([switch]$PrepareOnly, [switch]$AuthorizedCodexTask)

$ErrorActionPreference = 'Stop'
throw 'PROGRAM_KIT_LOCAL_RELEASE_RETIRED: Complete qualification is CI-owned. Run qualify-candidate.yml on main with expected_commit=<exact SHA>; use scripts/release_candidate.py find/download/prepare-trial. This legacy wrapper performs no build, test, preparation or receipt rewrite. See docs/releasing.md.'
