@echo off
REM Pre-push check script for Mushqila project (Windows)
REM Run this before pushing to GitHub

echo.
echo ========================================
echo   Mushqila Pre-Push Checks
echo ========================================
echo.

set ERRORS=0

REM Check 1: Required files exist
echo [1/5] Checking required files...
if exist "Dockerfile" (echo [OK] Dockerfile) else (echo [MISSING] Dockerfile & set /a ERRORS+=1)
if exist "docker-compose.yml" (echo [OK] docker-compose.yml) else (echo [MISSING] docker-compose.yml & set /a ERRORS+=1)
if exist "docker-compose.prod.yml" (echo [OK] docker-compose.prod.yml) else (echo [MISSING] docker-compose.prod.yml & set /a ERRORS+=1)
if exist "requirements.txt" (echo [OK] requirements.txt) else (echo [MISSING] requirements.txt & set /a ERRORS+=1)
if exist ".env.production" (echo [OK] .env.production) else (echo [MISSING] .env.production & set /a ERRORS+=1)
if exist ".github\workflows\deploy.yml" (echo [OK] GitHub Actions workflow) else (echo [MISSING] GitHub Actions workflow & set /a ERRORS+=1)
if exist "entrypoint.sh" (echo [OK] entrypoint.sh) else (echo [MISSING] entrypoint.sh & set /a ERRORS+=1)
if exist "deploy.sh" (echo [OK] deploy.sh) else (echo [MISSING] deploy.sh & set /a ERRORS+=1)
if exist "setup-ec2.sh" (echo [OK] setup-ec2.sh) else (echo [MISSING] setup-ec2.sh & set /a ERRORS+=1)
echo.

REM Check 2: .gitignore exists
echo [2/5] Checking .gitignore...
if exist ".gitignore" (
    echo [OK] .gitignore exists
    findstr /C:".env" .gitignore >nul && echo [OK] .env in .gitignore || echo [WARNING] .env not in .gitignore
    findstr /C:"*.pem" .gitignore >nul && echo [OK] *.pem in .gitignore || echo [WARNING] *.pem not in .gitignore
    findstr /C:"db.sqlite3" .gitignore >nul && echo [OK] db.sqlite3 in .gitignore || echo [WARNING] db.sqlite3 not in .gitignore
) else (
    echo [MISSING] .gitignore
    set /a ERRORS+=1
)
echo.

REM Check 3: Documentation files
echo [3/5] Checking documentation...
if exist "README.md" (echo [OK] README.md) else (echo [MISSING] README.md & set /a ERRORS+=1)
if exist "DEPLOYMENT.md" (echo [OK] DEPLOYMENT.md) else (echo [WARNING] DEPLOYMENT.md)
if exist "GALILEO-SETUP.md" (echo [OK] GALILEO-SETUP.md) else (echo [WARNING] GALILEO-SETUP.md)
if exist "TESTING.md" (echo [OK] TESTING.md) else (echo [WARNING] TESTING.md)
echo.

REM Check 4: Python files syntax (basic check)
echo [4/5] Checking Python syntax...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python is installed
    python -c "import py_compile; py_compile.compile('manage.py')" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] manage.py syntax OK
    ) else (
        echo [ERROR] manage.py has syntax errors
        set /a ERRORS+=1
    )
) else (
    echo [WARNING] Python not found, skipping syntax check
)
echo.

REM Check 5: Git status
echo [5/5] Checking Git status...
git --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Git is installed
    git status >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Git repository initialized
    ) else (
        echo [WARNING] Not a Git repository
    )
) else (
    echo [WARNING] Git not found
)
echo.

REM Summary
echo ========================================
if %ERRORS% EQU 0 (
    echo [SUCCESS] All checks passed!
    echo.
    echo Ready to push to GitHub:
    echo   1. git add .
    echo   2. git commit -m "Your message"
    echo   3. git push origin main
    echo.
    exit /b 0
) else (
    echo [FAILED] %ERRORS% error(s) found
    echo Please fix the errors before pushing
    echo.
    exit /b 1
)
