[CmdletBinding()]
param(
    [string]$Integration = 'codex',
    [string]$Scenario = 'clean-bootstrap',
    [int]$TimeoutSeconds = 7200,
    [switch]$ExerciseIntakeSkill,
    [int]$IntakeTimeoutSeconds = 3600,
    [switch]$ContinueFirstSlice,
    [int]$FirstSliceTimeoutSeconds = 7200,
    [switch]$Approved
)

$ErrorActionPreference = 'Stop'

throw @'
LIVE_ACCEPTANCE_V1_RETIRED

The combined paid live-bootstrap runner is retired and cannot start a coding agent. Issue a
phase-specific one-use authorization with New-LiveAcceptanceAuthorization.ps1, then run either
New-LiveBootstrapCheckpoint.ps1 or Test-LiveBuildingBlockConsumer.ps1. Historical v1 reports remain
evidence and are not converted to v2.
'@
