@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo Ultimate Animation Index needs Node.js 20 or newer.
  echo Install Node.js, then run UPDATE.bat again.
  echo.
  pause
  exit /b 1
)
where git >nul 2>nul
if errorlevel 1 (
  echo.
  echo Automatic updates need Git.
  echo Install Git, then run UPDATE.bat again.
  echo.
  pause
  exit /b 1
)
call npm run update
set "UAI_UPDATE_STATUS=%errorlevel%"
echo.
if not "%UAI_UPDATE_STATUS%"=="0" echo The update was not installed. Read the message above for details.
if "%UAI_UPDATE_STATUS%"=="0" echo You can now close this window and start the app with RUN.bat.
echo.
pause
exit /b %UAI_UPDATE_STATUS%
