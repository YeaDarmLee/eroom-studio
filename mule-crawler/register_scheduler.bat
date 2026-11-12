@echo off
cd /d "%~dp0"
set "SD=%~dp0"
set "PYW="
for /f "delims=" %%i in ('python -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"') do set "PYW=%%i"
if not exist "%PYW%" (
    echo pythonw.exe not found: "%PYW%"
    pause
    exit /b 1
)
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MuleScheduler.lnk"
powershell -NoProfile -Command "$q=[char]34; $s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LNK); $s.TargetPath=$env:PYW; $s.Arguments=$q+$env:SD+'scheduler.py'+$q; $s.WorkingDirectory=$env:SD; $s.Save()"
if not exist "%LNK%" (
    echo FAILED to create startup shortcut
    pause
    exit /b 1
)
echo Startup shortcut created: %LNK%
start "" "%PYW%" "%SD%scheduler.py"
echo Scheduler started. Check scheduler.log
pause
