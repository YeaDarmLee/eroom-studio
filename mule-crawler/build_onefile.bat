@echo off
echo ===================================================
echo  [1/4] Clean up old build files...
echo ===================================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist mule_login.spec del mule_login.spec

echo.
echo ===================================================
echo  [2/4] Install required packages...
echo ===================================================
pip install -r requirements.txt
pip install pyinstaller

echo.
echo ===================================================
echo  [3/4] Build single standalone executable using PyInstaller...
echo ===================================================
pyinstaller --onefile ^
  --add-data "template;template" ^
  --add-data "img;img" ^
  --add-data ".env;." ^
  --exclude-module PyQt5 ^
  --exclude-module PyQt6 ^
  --exclude-module PySide2 ^
  --exclude-module PySide6 ^
  --clean ^
  mule_login.py

echo.
echo ===================================================
echo  [4/4] Finalizing...
echo ===================================================
if exist dist\mule_login.exe (
    echo.
    echo ===================================================
    echo  BUILD FINISHED SUCCESS!
    echo  Standalone Executable created at: dist\mule_login.exe
    echo  You can copy 'dist\mule_login.exe' to any computer and double-click to run!
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo  BUILD FAILED! Please check the logs above.
    echo ===================================================
)

pause
