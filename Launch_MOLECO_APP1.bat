@echo off
title Launching MOLECO APP1

:: 1. NAVIGATE TO YOUR CODE FOLDER
cd /d "C:\Users\N.M.Sekar\moleco app1"

:: 2. ACTIVATE CHEMTOOLS_ENV
call "C:\Users\N.M.Sekar\miniconda3\Scripts\activate.bat" chemtools_env

:: 3. LAUNCH VOILA AND ENFORCE PYTHON SCRIPT MAPPING
echo Launching MOLWECO APP1...
python -m voila --VoilaConfiguration.extension_language_mapping="{\".py\": \"python\"}" --VoilaConfiguration.language_kernel_mapping="{\"python\": \"python3\"}"

pause