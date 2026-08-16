@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo Ultimate Animation Index needs Node.js 20 or newer.
  echo Download and install Node.js, then double-click RUN.bat again.
  echo.
  pause
  exit /b 1
)
set "UAI_URL=http://localhost:8787"
start "" powershell -NoProfile -WindowStyle Hidden -Command "$u='%UAI_URL%'; for($i=0;$i -lt 80;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri ($u + '/api/health') -TimeoutSec 1; if($r.StatusCode -eq 200){ Start-Process $u; break } } catch {}; Start-Sleep -Milliseconds 250 }"
echo.
echo Ultimate Animation Index
 echo Starting the site and opening it in your default browser...
echo Keep this window open while you use the site.
echo Close this window to stop the local server.
echo.
npm start
if errorlevel 1 (
  echo.
  echo The server stopped with an error.
  pause
)
