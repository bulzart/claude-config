#!/usr/bin/env bash
# check-all: every check of the /analyze-then-pick library (its suites, the docs check, Loupe's tests). Flags: --real --no-loupe --live
export PYTHONIOENCODING=utf-8
exec "/c/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe" -X utf8 "$(dirname "$0")/check_all.py" "$@"
