@echo off
REM Przejdź do katalogu, w którym leży ten plik .bat (root projektu)
cd /d "%~dp0"

REM Aktywuj venv
call venv\Scripts\activate.bat

REM Odpal uvicorn tak samo jak ręcznie
python -m uvicorn main:app --host 0.0.0.0 --port 8000

