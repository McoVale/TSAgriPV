@echo off
REM Install pipenv with pip
pip install pipenv

REM Get the directory of the currently executing script
set SCRIPT_DIR=%~dp0

REM Change directory to the script directory
cd /d %SCRIPT_DIR%

REM Launch pipenv virtual environment
pipenv shell

REM Install all dependencies from the Pipfile
pipenv install

pause
