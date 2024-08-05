@echo off
REM Install all dependencies from the Pipfile
pipenv install

REM Activate the virtual environment and run the Python script
pipenv run python TSAgrivPVTracking.py

pause
