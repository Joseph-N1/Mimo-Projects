@echo off
REM =========================================================
REM Run NAZIM_GP.py prediction interactively
REM Location: C:\Users\Joseph N Nimyel\OneDrive\Documents\Mimo Projects\F1\Predictions
REM =========================================================

REM Ask user for round number
set /p ROUND=Enter the round number to predict (e.g., 16): 

REM Ask user for how many top drivers
set /p TOPK=Enter how many top drivers to return (e.g., 5): 

REM Define dataset path
set DB_PATH=C:\Users\Joseph N Nimyel\OneDrive\Documents\Mimo Projects\F1\DataBase\F1-Seasons-2025.json

REM Run prediction
python NAZIM_GP.py --db "%DB_PATH%" --predict --round %ROUND% --topk %TOPK% --model-dir ./models

pause
