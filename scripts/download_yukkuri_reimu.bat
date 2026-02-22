@echo off
rem Download and extract Reimu zip into the repository material folder
setlocal

set "URL=http://nicotalk.com/sozai/%%E3%%81%%8D%%E3%%81%%A4%%E3%%81%%AD%%E3%%82%%86%%E3%%81%%A3%%E3%%81%%8F%%E3%%82%%8A/%%E3%%82%%8C%%E3%%81%%84%%E3%%82%%80.zip"
set "SCRIPT_DIR=%~dp0"
set "ZIP_FILE=%SCRIPT_DIR%reimu.zip"
set "DEST_DIR=%SCRIPT_DIR%..\material"

echo Creating destination folder "%DEST_DIR%"
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

echo Downloading "%URL%" to "%ZIP_FILE%"...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIP_FILE%' -ErrorAction Stop } catch { Write-Error 'Download failed'; exit 1 }"
if not exist "%ZIP_FILE%" (
	echo Download failed: file not found.
	exit /b 1
)

echo Extracting to "%DEST_DIR%"...
powershell -NoProfile -Command "try { Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%DEST_DIR%' -Force -ErrorAction Stop } catch { Write-Error 'Extraction failed'; exit 1 }"
if %ERRORLEVEL% neq 0 (
	echo Extraction failed.
	exit /b %ERRORLEVEL%
)

echo Removing temporary zip "%ZIP_FILE%"
del /f /q "%ZIP_FILE%"

echo Done.
endlocal
exit /b 0

