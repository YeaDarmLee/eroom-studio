@echo off
echo ===================================================
echo  Eroom Studio Mule Crawler App Builder
echo ===================================================

echo [1/4] Install required libraries...
pip install pyinstaller python-dotenv playwright
playwright install chromium

echo [2/4] Start PyInstaller build...
pyinstaller --onedir --console --name="mule_login" --clean mule_login.py

echo [3/4] Setup distribution folder: mule-crawler-app
if exist "mule-crawler-app" rmdir /s /q "mule-crawler-app"
mkdir "mule-crawler-app"

xcopy /E /I /Y "dist\mule_login" "mule-crawler-app"
xcopy /E /I /Y "template" "mule-crawler-app\template"
xcopy /E /I /Y "result" "mule-crawler-app\result"
copy /Y ".env" "mule-crawler-app\.env"

echo [4/4] Clean temporary build files...
rmdir /s /q "build"
rmdir /s /q "dist"
if exist "mule_login.spec" del /f /q "mule_login.spec"

echo ===================================================
echo  BUILD FINISHED SUCCESS!
echo  Please compress and copy 'mule-crawler-app' folder.
echo  Double-click 'mule_login.exe' inside to run.
echo ===================================================
pause
