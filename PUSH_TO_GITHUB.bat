@echo off
title Push Forest AR to GitHub
cd /d "%~dp0"
echo ========================================================
echo   Pushing 3D Forest and Bengal Tiger AR to GitHub...
echo   Repository: https://github.com/dhamodharankkp-oss/forest-3d-ar
echo ========================================================
echo.
git push -u origin main --force
echo.
if %ERRORLEVEL% EQU 0 (
  echo ========================================================
  echo   SUCCESS! All files uploaded to GitHub.
  echo   Now go to: https://github.com/dhamodharankkp-oss/forest-3d-ar/settings/pages
  echo   Under Branch, select "main" and click "Save".
  echo ========================================================
) else (
  echo ========================================================
  echo   Push encountered an error. Please check your GitHub login.
  echo ========================================================
)
echo.
pause
