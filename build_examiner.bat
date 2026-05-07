@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

if not exist "venv\Scripts\python.exe" (
  echo Virtual environment Python was not found at venv\Scripts\python.exe
  exit /b 1
)

venv\Scripts\python.exe -m PyInstaller --noconfirm build_examiner.spec
if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete.
echo Examiner package: dist\FitTrackExaminer
