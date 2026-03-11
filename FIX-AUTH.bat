@echo off
echo ========================================
echo   Fixing Authentication Refresh Loop
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File fix-pages.ps1

echo.
echo ========================================
echo   Fix Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Clear your browser cache and localStorage
echo 2. Restart your dev server if running
echo 3. Try logging in again
echo.
pause
