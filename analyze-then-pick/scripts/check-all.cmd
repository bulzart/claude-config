@echo off
rem check-all: every check of the /analyze-then-pick library (its suites, the docs check, Loupe's tests). Flags: --real --no-loupe --live
set PYTHONIOENCODING=utf-8
"C:\Users\Glaresquare1\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 "%~dp0check_all.py" %*
