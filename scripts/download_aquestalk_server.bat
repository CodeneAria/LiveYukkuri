@echo off
rem Download aquestalk-server.exe into the repository root
setlocal

set "URL=https://github.com/Lqm1/aquestalk-server/releases/download/2.0.0/aquestalk-server.exe"
set "SCRIPT_DIR=%~dp0"
set "DEST_FILE=%SCRIPT_DIR%..\aquestalk-server.exe"

echo Downloading "%URL%" to "%DEST_FILE%"...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -OutFile '%DEST_FILE%' -ErrorAction Stop } catch { Write-Error 'Download failed'; exit 1 }"
if not exist "%DEST_FILE%" (
	echo Download failed: file not found.
	exit /b 1
)

echo Download complete: "%DEST_FILE%"
endlocal
exit /b 0

