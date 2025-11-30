@echo off
REM Przejdź do katalogu, w którym leży ten plik .bat
cd /d "%~dp0"

REM Aktywuj wirtualne środowisko (ścieżka względna do venv)
call venv\Scripts\activate.bat

REM Odpal uvicorn
python -m knn_grouping.main