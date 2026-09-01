@echo off
setlocal
set "PROGRAM_KIT_REF=v0.6.4"

rem Program Kit consumer bootstrap for a repository that does not already contain Program Kit.
rem Run this file from a normal user-owned PowerShell prompt in the repository root.

for %%I in ("%~dp0.") do set "PROGRAM_KIT_SCRIPT_DIR=%%~fI"
if /I not "%CD%"=="%PROGRAM_KIT_SCRIPT_DIR%" (
  echo ERROR: Change to the repository root containing %~nx0 before running it. 1>&2
  exit /b 2
)

if defined CODEX_SESSION_ID goto :agent_environment
if defined CODEX_THREAD_ID goto :agent_environment
if defined CODEX_INTERNAL_ORIGINATOR_OVERRIDE goto :agent_environment

if exist ".specify\bundle-records.json" (
  findstr /i /c:"program-kit" ".specify\bundle-records.json" >nul 2>nul
  if not errorlevel 1 goto :already_initialized
)
if exist ".specify\extensions.yml" (
  findstr /i /c:"program-kit-governance" /c:"program-kit-dotnet" ".specify\extensions.yml" >nul 2>nul
  if not errorlevel 1 goto :already_initialized
)
if exist ".specify\workflows\workflow-registry.json" (
  findstr /i /c:"program-kit-bootstrap" ".specify\workflows\workflow-registry.json" >nul 2>nul
  if not errorlevel 1 goto :already_initialized
)
for %%F in (
  ".specify\extension-catalogs.yml"
  ".specify\preset-catalogs.yml"
  ".specify\workflow-catalogs.yml"
  ".specify\bundle-catalogs.yml"
) do (
  if exist "%%~F" (
    findstr /i /c:"program-kit" "%%~F" >nul 2>nul
    if not errorlevel 1 goto :already_initialized
  )
)
if exist ".specify\extensions\program-kit-governance\extension.yml" goto :already_initialized
if exist ".specify\extensions\program-kit-dotnet\extension.yml" goto :already_initialized
if exist ".specify\workflows\program-kit-bootstrap\workflow.yml" goto :already_initialized
if exist ".agents\skills\speckit-program-kit-governance-bootstrap\SKILL.md" goto :already_initialized

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
if exist "INITIAL_DESIGN.md" (
  echo Existing INITIAL_DESIGN.md detected. Start the bootstrap from this same normal shell:
) else (
  echo Create INITIAL_DESIGN.md when ready, then start the bootstrap from this same normal shell:
)
echo.
echo   specify workflow run program-kit-bootstrap --input initial_design=./INITIAL_DESIGN.md --input integration=codex
exit /b 0

:agent_environment
echo ERROR: Run %~nx0 yourself from a normal user-owned PowerShell prompt, not from a Codex Desktop task or interactive Codex CLI agent. 1>&2
exit /b 2

:already_initialized
echo ERROR: Program Kit is already installed, or a partial Program Kit installation exists in %CD%. 1>&2
echo Use the documented Program Kit update commands instead of running the initializer again. 1>&2
exit /b 2

:failed
echo ERROR: Program Kit initialization stopped because a command failed. Review the output above; no execution-policy workaround is required or recommended. 1>&2
exit /b 1
