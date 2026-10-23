@echo off
setlocal
cd /d "%~dp0"
echo Academia Galactica - backend LOCAL de entrenamiento
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 goto usepython
py -m venv .venv
if errorlevel 1 goto fail
goto install
:usepython
where python >nul 2>nul
if errorlevel 1 goto nopython
python -m venv .venv
if errorlevel 1 goto fail
:install
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 goto oldpython
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo.
echo Abre http://127.0.0.1:8000 y entra en la estacion 07.
echo Para detener el servidor pulsa Ctrl+C.
echo.
".venv\Scripts\python.exe" -m uvicorn backend:app --host 127.0.0.1 --port 8000
if errorlevel 1 goto fail
goto end
:nopython
echo No se encuentra Python. Instala Python 3.11 o posterior y consulta LEEME.md.
goto fail
:oldpython
echo Se necesita Python 3.11 o posterior. Revisa el entorno .venv.
goto fail
:fail
echo No se ha podido iniciar. Lee el error anterior y consulta LEEME.md.
pause
exit /b 1
:end
endlocal
