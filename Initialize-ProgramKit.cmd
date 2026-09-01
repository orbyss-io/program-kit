@echo off
setlocal
set "PROGRAM_KIT_REF=v0.6.3"

rem Program Kit consumer bootstrap for a new repository.
rem Run this file from a normal user-owned PowerShell prompt in the repository root.

for %%I in ("%~dp0.") do set "PROGRAM_KIT_SCRIPT_DIR=%%~fI"
if /I not "%CD%"=="%PROGRAM_KIT_SCRIPT_DIR%" (
  echo ERROR: Change to the repository root containing %~nx0 before running it. 1>&2
  exit /b 2
)

if defined CODEX_SESSION_ID goto :agent_environment
if defined CODEX_THREAD_ID goto :agent_environment
if defined CODEX_INTERNAL_ORIGINATOR_OVERRIDE goto :agent_environment

for /f "delims=" %%F in ('dir /b /a 2^>nul') do (
  if /I not "%%F"==".git" if /I not "%%F"=="%~nx0" goto :not_empty
)

where specify >nul 2>nul
if errorlevel 1 (
  echo ERROR: Spec Kit 1.0.1 or a compatible 1.x `specify` command is required. 1>&2
  exit /b 2
)

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python must be available as `python` because Program Kit uses the Python Spec Kit runtime. 1>&2
  exit /b 2
)

echo [1/7] Initializing Spec Kit for Codex with the Python script flavor...
call specify init . --force --non-interactive --integration codex --script py
if errorlevel 1 goto :failed

echo [2/7] Registering the Program Kit extension catalog...
call specify extension catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/extensions.json --name program-kit --install-allowed
if errorlevel 1 goto :failed

echo [3/7] Registering the Program Kit preset catalog...
call specify preset catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/presets.json --name program-kit --install-allowed
if errorlevel 1 goto :failed

echo [4/7] Registering the Program Kit workflow catalog...
call specify workflow catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/workflows.json --name program-kit
if errorlevel 1 goto :failed

echo [5/7] Registering the Program Kit bundle catalog...
call specify bundle catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/bundles.json --id program-kit --policy install-allowed
if errorlevel 1 goto :failed

echo [6/7] Installing the bootstrap workflow required by Spec Kit 1.0.1...
call specify workflow add program-kit-bootstrap
if errorlevel 1 goto :failed

echo [7/7] Installing Program Kit...
call specify bundle install program-kit --integration codex
if errorlevel 1 goto :failed

echo.
echo Program Kit initialization is complete. No initial design was required.
echo Create INITIAL_DESIGN.md when ready, then start the bootstrap from this same normal shell:
echo.
echo   specify workflow run program-kit-bootstrap --input initial_design=./INITIAL_DESIGN.md --input integration=codex
exit /b 0

:agent_environment
echo ERROR: Run %~nx0 yourself from a normal user-owned PowerShell prompt, not from a Codex Desktop task or interactive Codex CLI agent. 1>&2
exit /b 2

:not_empty
echo ERROR: %CD% is not empty. Use a new repository containing only .git and %~nx0. 1>&2
exit /b 2

:failed
echo ERROR: Program Kit initialization stopped because a command failed. Review the output above; no execution-policy workaround is required or recommended. 1>&2
exit /b 1
