@echo off
cd /d "%~dp0"
for /f "delims=" %%i in ('where pythonw') do set PYW=%%i & goto :found
echo pythonw not found & pause & exit /b 1
:found
schtasks /create /tn "MuleScheduler" /tr "\"%PYW%\" \"%~dp0scheduler.py\"" /sc onlogon /rl limited /f
echo.
echo Registered. Logon 시 자동 시작. 지금 바로 시작: schtasks /run /tn MuleScheduler
pause
