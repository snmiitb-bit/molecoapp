@echo off
title Launching MOLWECO APP1

:: 1. NAVIGATE TO YOUR CODE FOLDER
cd /d "C:\Users\N.M.Sekar\moleco app1"

:: 2. ACTIVATE CHEMTOOLS_ENV USING THE ROOT MINICONDA PATH
call "C:\Users\N.M.Sekar\miniconda3\Scripts\activate.bat" chemtools_env

:: 3. LAUNCH THE WEB APP
echo Launching MOLWECO APP1 interface...
python -m voila molway_app.py

pause