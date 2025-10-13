@echo off
REM scripts\run.bat
REM Starts backend (FastAPI) and frontend (Streamlit) using .venv in separate windows

REM Set project root directory
set "PROJECT_ROOT=%~dp0.."

REM Start backend in new window
start "Backend" cmd /k "cd /d "%PROJECT_ROOT%\backend" && ..\.venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000"

REM Start frontend in new window
start "Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && ..\.venv\Scripts\activate && streamlit run app.py --server.port 8501"

echo Backend and frontend started in new windows.
pause
