@echo off
setlocal
set "CHIBI_REVIEW_PYTHON=C:\Users\JG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%CHIBI_REVIEW_PYTHON%" (
  echo Required existing Python runtime is missing. No packages or runtimes are installed automatically.
  exit /b 1
)
"%CHIBI_REVIEW_PYTHON%" -B "%~dp0run_review.py" --config "%~dp0review_config.json" %*
exit /b %errorlevel%
