@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  Python Virtual Environment Setup
echo ============================================================
echo.

:: Use PowerShell to open a file dialog for selecting the Python executable
echo Selecting Python executable via dialog...

:: Write a temporary PowerShell script to avoid cmd.exe misinterpreting | in the filter string
set "PS_SCRIPT=%TEMP%\select_python_exe.ps1"
(
    echo Add-Type -AssemblyName System.Windows.Forms
    echo $d = New-Object System.Windows.Forms.OpenFileDialog
    echo $d.Title = 'Select Python Executable'
    echo $sep = [char]124
    echo $d.Filter = "Python Executable (python.exe)${sep}python.exe${sep}All Executables (*.exe)${sep}*.exe"
    echo $d.InitialDirectory = 'C:\'
    echo if ^($d.ShowDialog^(^) -eq 'OK'^) { $d.FileName } else { '' }
) > "%PS_SCRIPT%"

for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"`) do (
    set "PYTHON_EXE=%%P"
)
del "%PS_SCRIPT%" >nul 2>&1

:: Check if a file was selected
if "!PYTHON_EXE!"=="" (
    echo ERROR: No Python executable was selected. Aborting.
    pause
    exit /b 1
)

echo Selected Python: !PYTHON_EXE!
echo.

:: Verify the selected file is a valid Python executable
"!PYTHON_EXE!" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: The selected file does not appear to be a valid Python executable.
    pause
    exit /b 1
)

:: Determine the repository root (parent of the scripts folder)
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%"
set "REPO_ROOT=%CD%"
popd

set "VENV_DIR=%REPO_ROOT%\venv_python"

echo Repository root : %REPO_ROOT%
echo Virtual env path: %VENV_DIR%
echo.

:: Remove existing venv if present
if exist "%VENV_DIR%" (
    echo Removing existing virtual environment...
    rmdir /s /q "%VENV_DIR%"
)

:: Create the virtual environment
echo Creating virtual environment...
"!PYTHON_EXE!" -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo Virtual environment created successfully.
echo.

:: Install Flask using the venv's pip
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
echo Installing Flask...
"%VENV_PYTHON%" -m pip install --upgrade pip
"%VENV_PYTHON%" -m pip install flask
if errorlevel 1 (
    echo ERROR: Failed to install Flask.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup complete!
echo  Virtual environment : %VENV_DIR%
echo  Flask has been installed in the virtual environment.
echo ============================================================
echo.
pause
endlocal
