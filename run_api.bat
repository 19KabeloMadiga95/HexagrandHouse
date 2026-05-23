@echo off
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
uvicorn src.api.main:app --reload
pause
