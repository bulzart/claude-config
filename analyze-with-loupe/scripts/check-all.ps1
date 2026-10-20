# check-all: every check of the /analyze-with-loupe library (its suites, the docs check, Loupe's tests). Flags: --real --no-loupe --live
$env:PYTHONIOENCODING = "utf-8"
& "C:\Users\Glaresquare1\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 (Join-Path $PSScriptRoot "check_all.py") @args
exit $LASTEXITCODE
