@echo off

REM Check black code style
uv run black --check --diff swissparlpy examples tests
if %errorlevel% neq 0 echo "uv run black failed." && exit /b %errorlevel%

REM Check PEP-8 code style and McCabe complexity
uv run flake8 --count --show-source --statistics swissparlpy
if %errorlevel% neq 0 echo "uv run flake8 failed." && exit /b %errorlevel%

REM Run mypy type checks
uv run mypy swissparlpy
if %errorlevel% neq 0 echo "uv run mypy failed." && exit /b %errorlevel%    

REM run tests with test coverage
uv run pytest tests/
if %errorlevel% neq 0 echo "uv run pytest failed." && exit /b %errorlevel%