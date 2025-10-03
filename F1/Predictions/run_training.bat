@echo off
REM === Activate your virtual environment ===
call ..\f1_prediction_env\Scripts\activate

REM === Run training on the 2025 dataset ===
python NAZIM_GP.py --db "C:\Users\Joseph N Nimyel\OneDrive\Documents\Mimo Projects\F1\DataBase\F1-Seasons-2025.json" --train --model-dir ./models --test-size 0.2

pause
