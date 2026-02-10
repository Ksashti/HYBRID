@echo off
echo ========================================
echo   HYBRID VoiceChat v2.0 - Build EXE
echo ========================================
echo.

echo Step 1: Installing dependencies...
pip install -r requirements.txt
echo.

echo Step 2: Building client EXE...
pyinstaller --onefile --windowed --name="HYBRID" --icon=NONE ^
    --add-data "client;client" ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import opuslib ^
    client/main.py
echo.

echo ========================================
echo   DONE!
echo ========================================
echo.
echo Client EXE: dist\HYBRID.exe
echo Server: python server/main.py
echo.
pause
