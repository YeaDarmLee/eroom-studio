@echo off
cd /d "%~dp0"
set PYW=
for /f "delims=" %%i in ('python -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"') do set PYW=%%i
if not exist "%PYW%" (
    echo pythonw.exe not found: "%PYW%"
    pause
    exit /b 1
)
schtasks /create /tn "MuleScheduler" /tr "\"%PYW%\" \"%~dp0scheduler.py\"" /sc onlogon /rl limited /f
echo.
echo Registered. Logon 시 자동 시작. 지금 바로 시작: schtasks /run /tn MuleScheduler
pause
