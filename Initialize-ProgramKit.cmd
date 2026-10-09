@echo off
setlocal DisableDelayedExpansion
set "PROGRAM_KIT_REF=v0.12.10"

rem Program Kit consumer bootstrap for a repository that does not already contain Program Kit.
rem Run this file from a normal user-owned PowerShell prompt in the repository root.

if "%~1"=="" (
  echo ERROR: Supply exactly one Spec Kit integration ID, for example: %~nx0 codex 1>&2
  exit /b 2
)
if not "%~2"=="" (
  echo ERROR: Supply exactly one Spec Kit integration ID, for example: %~nx0 codex 1>&2
  exit /b 2
)
set "PROGRAM_KIT_INTEGRATION=%~1"
for /f "delims=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" %%A in ("%PROGRAM_KIT_INTEGRATION%") do (
  echo ERROR: Supply exactly one Spec Kit integration ID, for example: %~nx0 codex 1>&2
  exit /b 2
)

for %%I in ("%~dp0.") do set "PROGRAM_KIT_SCRIPT_DIR=%%~fI"
if /I not "%CD%"=="%PROGRAM_KIT_SCRIPT_DIR%" (
  echo ERROR: Change to the repository root containing %~nx0 before running it. 1>&2
  exit /b 2
)

if defined CODEX_SESSION_ID goto :agent_environment
if defined CODEX_THREAD_ID goto :agent_environment
if defined CODEX_INTERNAL_ORIGINATOR_OVERRIDE goto :agent_environment

if exist ".specify\bundle-records.json" (
  "%SystemRoot%\System32\findstr.exe" /i /c:"program-kit" ".specify\bundle-records.json" >nul 2>nul
  if not errorlevel 1 goto :already_initialized
)
if exist ".specify\extensions.yml" (
  "%SystemRoot%\System32\findstr.exe" /i /c:"program-kit-governance" /c:"program-kit-dotnet" ".specify\extensions.yml" >nul 2>nul
  if not errorlevel 1 goto :already_initialized
)
if exist ".specify\workflows\workflow-registry.json" (
  "%SystemRoot%\System32\findstr.exe" /i /c:"program-kit-bootstrap" ".specify\workflows\workflow-registry.json" >nul 2>nul
  if not errorlevel 1 goto :already_initialized
)
for %%F in (
  ".specify\extension-catalogs.yml"
  ".specify\preset-catalogs.yml"
  ".specify\workflow-catalogs.yml"
  ".specify\bundle-catalogs.yml"
) do (
  if exist "%%~F" (
    "%SystemRoot%\System32\findstr.exe" /i /c:"program-kit" "%%~F" >nul 2>nul
    if not errorlevel 1 goto :already_initialized
  )
)
if exist ".specify\extensions\program-kit-governance\extension.yml" goto :already_initialized
if exist ".specify\extensions\program-kit-dotnet\extension.yml" goto :already_initialized
if exist ".specify\workflows\program-kit-bootstrap\workflow.yml" goto :already_initialized
if exist ".agents\skills\speckit-program-kit-governance-bootstrap\SKILL.md" goto :already_initialized

rem CMD can discard an inherited PATH longer than 8191 characters. Resolve native
rem tools through Windows PowerShell, with the persisted user/machine PATH as a
rem fallback. Explicit executable overrides also support nonstandard installations.
if not defined PROGRAM_KIT_SPECIFY call :resolve_command specify PROGRAM_KIT_SPECIFY
if not defined PROGRAM_KIT_GIT call :resolve_command git PROGRAM_KIT_GIT
if not defined SPECKIT_PYTHON call :resolve_command python SPECKIT_PYTHON
if not defined PROGRAM_KIT_SPECIFY (
  echo PKT030: Spec Kit required ^>=1.1.1,^<2 from the Program Kit bundle; detected=missing executable=missing. In your own terminal use a shared installation: uv tool install specify-cli==1.1.1 --force --no-python-downloads then uv tool update-shell. Refresh and verify Get-Command specify -All and specify version. 1>&2
  echo If uv is absent, follow https://docs.astral.sh/uv/getting-started/installation/. If already installed, repair persistent PATH rather than installing another copy. 1>&2
  exit /b 2
)
if not defined PROGRAM_KIT_GIT (
  echo ERROR: Cannot resolve Git. Install Git or set PROGRAM_KIT_GIT to its full executable path in this terminal. 1>&2
  exit /b 2
)
if not defined SPECKIT_PYTHON (
  echo PKT030: Python required ^>=3.11 from the Spec Kit runtime contract; detected=missing executable=missing. In your own terminal use uv python install 3.11 --default then uv python update-shell, or retain your existing device installer. 1>&2
  echo If uv is absent, follow https://docs.astral.sh/uv/getting-started/installation/. Refresh and verify Get-Command python -All and python --version. No installer was run. 1>&2
  exit /b 2
)
rem Child tools (including Spec Kit's integration/Git checks) need a usable PATH
rem and PATHEXT too. Keep changes local to this initializer's process tree.
set "PATHEXT=.EXE;.COM;.BAT;.CMD;%PATHEXT%"
set "PROGRAM_KIT_ORIGINAL_PATH=%PATH%"
call "%SPECKIT_PYTHON%" -c "import sys; print(sys.executable); assert sys.version_info >= (3,11), 'Python >=3.11 is required; update shared device Python in your own terminal and refresh the session'"
if errorlevel 1 exit /b 2
rem Check the original device selection before invocation-scoped PATH preparation.
rem Only release-owned diagnostic Python/data are downloaded; no device installer runs.
if exist "%~dp0scripts\initialize_device.py" (
  call "%SPECKIT_PYTHON%" "%~dp0scripts\initialize_device.py" --ref "%PROGRAM_KIT_REF%" --project-root "%CD%" --release-root "%~dp0."
  if errorlevel 1 exit /b 2
) else (
  set "PROGRAM_KIT_DEVICE_PREFLIGHT=%TEMP%\program-kit-device-%RANDOM%-%RANDOM%.py"
  call :device_preflight
  if errorlevel 1 exit /b 2
)
set "PATH="
call :prepare_path
if not defined PATH (
  echo ERROR: A usable PATH could not be prepared within CMD's size limit. Use a shorter PATH in this terminal and rerun; no persistent settings were changed. 1>&2
  exit /b 2
)
echo Spec Kit executable: "%PROGRAM_KIT_SPECIFY%"
call "%PROGRAM_KIT_SPECIFY%" --version
if errorlevel 1 (
  echo ERROR: Spec Kit at "%PROGRAM_KIT_SPECIFY%" could not execute. Review its error above; repair that installation or correct PROGRAM_KIT_SPECIFY. 1>&2
  exit /b 2
)
set "PROGRAM_KIT_SPECIFY_VERSION="
for /f "tokens=1,2" %%A in ('call "%PROGRAM_KIT_SPECIFY%" --version') do if "%%A"=="specify" set "PROGRAM_KIT_SPECIFY_VERSION=%%B"
call "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -Command "$v=$env:PROGRAM_KIT_SPECIFY_VERSION; if ($v -notmatch '^1\.[0-9]+\.[0-9]+$' -or [version]$v -lt [version]'1.1.1') { [Console]::Error.WriteLine('ERROR: Spec Kit >=1.1.1,<2 is required; selected version: '+$v); exit 2 }"
if errorlevel 1 exit /b 2

echo Git executable: "%PROGRAM_KIT_GIT%"
call "%PROGRAM_KIT_GIT%" --version
if errorlevel 1 (
  echo ERROR: Git at "%PROGRAM_KIT_GIT%" could not execute. Review its error above; repair Git or correct PROGRAM_KIT_GIT. 1>&2
  exit /b 2
)
call "%PROGRAM_KIT_GIT%" rev-parse --is-inside-work-tree
if errorlevel 1 goto :git_not_initialized

echo Python executable: "%SPECKIT_PYTHON%"
call "%SPECKIT_PYTHON%" -c "import sys; print(sys.executable); assert sys.version_info >= (3,11)"
if errorlevel 1 (
  echo ERROR: The selected Python interpreter must support Python 3.11 or newer. 1>&2
  exit /b 2
)

call "%SPECKIT_PYTHON%" -c "import yaml" >nul 2>nul
if errorlevel 1 (
  call "%SPECKIT_PYTHON%" -m pip --version >nul 2>nul
  if errorlevel 1 goto :pip_missing
  echo Installing the PyYAML dependency required by the Spec Kit Python resolver...
  call "%SPECKIT_PYTHON%" -m pip install --disable-pip-version-check "PyYAML>=6,<7"
  if errorlevel 1 goto :dependency_failed
  call "%SPECKIT_PYTHON%" -c "import yaml" >nul 2>nul
  if errorlevel 1 goto :dependency_failed
)

set "PROGRAM_KIT_STAGE=step 1/8: Initializing Spec Kit for %PROGRAM_KIT_INTEGRATION% with the Python script flavor"
echo [1/8] Initializing Spec Kit for %PROGRAM_KIT_INTEGRATION% with the Python script flavor...
call "%PROGRAM_KIT_SPECIFY%" init . --force --non-interactive --integration %PROGRAM_KIT_INTEGRATION% --script py
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 2/8: Registering the Program Kit extension catalog"
echo [2/8] Registering the Program Kit extension catalog...
call "%PROGRAM_KIT_SPECIFY%" extension catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/extensions.json --name program-kit --install-allowed
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 3/8: Registering the Program Kit preset catalog"
echo [3/8] Registering the Program Kit preset catalog...
call "%PROGRAM_KIT_SPECIFY%" preset catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/presets.json --name program-kit --install-allowed
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 4/8: Registering the Program Kit workflow catalog"
echo [4/8] Registering the Program Kit workflow catalog...
call "%PROGRAM_KIT_SPECIFY%" workflow catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/workflows.json --name program-kit
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 5/8: Registering the Program Kit bundle catalog"
echo [5/8] Registering the Program Kit bundle catalog...
call "%PROGRAM_KIT_SPECIFY%" bundle catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/%PROGRAM_KIT_REF%/catalogs/bundles.json --id program-kit --policy install-allowed
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 6/8: Installing the bootstrap workflow"
echo [6/8] Installing the bootstrap workflow...
call "%PROGRAM_KIT_SPECIFY%" workflow add program-kit-bootstrap
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 7/8: Installing Program Kit"
echo [7/8] Installing Program Kit...
call "%PROGRAM_KIT_SPECIFY%" bundle install program-kit --integration %PROGRAM_KIT_INTEGRATION%
if errorlevel 1 goto :failed
call "%SPECKIT_PYTHON%" ".specify\extensions\program-kit-governance\scripts\ensure_utf8.py" --target .
if errorlevel 1 goto :failed
call "%SPECKIT_PYTHON%" ".specify\extensions\program-kit-governance\scripts\schema_runtime.py" setup
if errorlevel 1 goto :failed
call "%SPECKIT_PYTHON%" ".specify\extensions\program-kit-governance\scripts\schema_runtime.py" record-copy
if errorlevel 1 goto :failed

set "PROGRAM_KIT_STAGE=step 8/8: Switching Program Kit catalogs to the update channel"
echo [8/8] Switching Program Kit catalogs to the update channel...
call "%PROGRAM_KIT_SPECIFY%" extension catalog remove program-kit
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" preset catalog remove program-kit
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" workflow catalog remove 0
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" bundle catalog remove program-kit
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" extension catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/extensions.json --name program-kit --install-allowed
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" preset catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/presets.json --name program-kit --install-allowed
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" workflow catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/workflows.json --name program-kit
if errorlevel 1 goto :failed
call "%PROGRAM_KIT_SPECIFY%" bundle catalog add https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/bundles.json --id program-kit --policy install-allowed
if errorlevel 1 goto :failed

echo.
echo Program Kit initialization is complete.
exit /b 0

:agent_environment
echo ERROR: Run %~nx0 yourself from a normal user-owned PowerShell prompt, not from a Codex Desktop task or interactive Codex CLI agent. 1>&2
exit /b 2

:already_initialized
echo ERROR: Program Kit is already installed, or a partial Program Kit installation exists in %CD%. 1>&2
echo Use the documented Program Kit update commands instead of running the initializer again. 1>&2
exit /b 2

:dependency_failed
echo ERROR: PyYAML could not be installed for the `python` command. Install "PyYAML^>=6,^<7" for that interpreter and rerun the initializer. 1>&2
exit /b 2

:pip_missing
echo ERROR: PyYAML is missing and `python -m pip` is unavailable. Install pip for this Python interpreter, then install "PyYAML^>=6,^<7" and rerun the initializer. 1>&2
exit /b 2

:git_not_initialized
echo ERROR: This directory is not inside an initialized Git work tree. 1>&2
echo Run these commands from %CD%, then rerun %~nx0 %PROGRAM_KIT_INTEGRATION%: 1>&2
echo. 1>&2
echo   git init 1>&2
echo   git status 1>&2
exit /b 2

:failed
set "PROGRAM_KIT_FAILURE_CODE=%errorlevel%"
echo ERROR: Program Kit initialization stopped during %PROGRAM_KIT_STAGE% with exit code %PROGRAM_KIT_FAILURE_CODE%. Review the output above; no execution-policy workaround is required or recommended. 1>&2
echo Preserve this output and the partial installation for diagnosis; do not delete it or force a bootstrap recovery. 1>&2
exit /b %PROGRAM_KIT_FAILURE_CODE%

:resolve_command
set "PROGRAM_KIT_LOOKUP=%~1"
for /f "delims=" %%P in ('call "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; $env:PATHEXT='.EXE;.COM;.BAT;.CMD'; $c=Get-Command $env:PROGRAM_KIT_LOOKUP -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1; if (-not $c) { $env:PATH=[Environment]::GetEnvironmentVariable('PATH','Machine')+';'+[Environment]::GetEnvironmentVariable('PATH','User'); $c=Get-Command $env:PROGRAM_KIT_LOOKUP -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1 }; if ($c) { $c.Source }"') do set "%~2=%%P"
exit /b 0

:device_preflight
call "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing ('https://raw.githubusercontent.com/orbyss-io/program-kit/'+$env:PROGRAM_KIT_REF+'/scripts/initialize_device.py') -OutFile $env:PROGRAM_KIT_DEVICE_PREFLIGHT"
if errorlevel 1 (
  echo ERROR: Exact-release device policy could not be obtained; initialization has not started. 1>&2
  exit /b 2
)
call "%SPECKIT_PYTHON%" "%PROGRAM_KIT_DEVICE_PREFLIGHT%" --ref "%PROGRAM_KIT_REF%" --project-root "%CD%"
if errorlevel 1 exit /b 2
exit /b 0

:prepare_path
rem Preserve command precedence after explicit overrides, remove duplicate/missing
rem directories, and restore Windows paths when CMD discarded the inherited PATH.
for /f "delims=" %%P in ('call "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -Command "$tools=@($env:PROGRAM_KIT_SPECIFY,$env:PROGRAM_KIT_GIT,$env:SPECKIT_PYTHON) | ForEach-Object { Split-Path -LiteralPath $_ }; $raw=$env:PROGRAM_KIT_ORIGINAL_PATH+';'+[Environment]::GetEnvironmentVariable('PATH','Machine')+';'+[Environment]::GetEnvironmentVariable('PATH','User'); $p=@($tools)+@($env:SystemRoot+'\System32')+@($raw.Split(';')); $p=$p | ForEach-Object { [Environment]::ExpandEnvironmentVariables($_).Trim().Trim([char]34) } | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Container) } | Select-Object -Unique; $p=$p -join ';'; if ($p.Length -lt 7500) { $p }"') do set "PATH=%%P"
exit /b 0
