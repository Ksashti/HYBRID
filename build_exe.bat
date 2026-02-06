@echo off
echo ========================================
echo Создание EXE файла для Voice Chat Client
echo ========================================
echo.

echo Шаг 1: Проверка установленных библиотек...
pip install -r requirements.txt
echo.

echo Шаг 2: Создание EXE файла...
pyinstaller --onefile --windowed --name="VoiceChat" --icon=NONE client_gui.py
echo.

echo ========================================
echo ГОТОВО!
echo ========================================
echo.
echo EXE файл находится в папке: dist\VoiceChat.exe
echo.
pause