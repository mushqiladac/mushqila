@echo off
REM Quick Start Script for Local Docker Development (Windows)

echo ==========================================
echo Starting Mushqila Local Development
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

echo Docker is running
echo.

REM Step 1: Build containers
echo Step 1: Building Docker containers...
echo -----------------------------------
docker-compose build
if errorlevel 1 (
    echo Build failed
    exit /b 1
)
echo Build complete
echo.

REM Step 2: Start containers
echo Step 2: Starting containers...
echo -----------------------------------
docker-compose up -d
if errorlevel 1 (
    echo Failed to start containers
    exit /b 1
)
echo Containers started
echo.

REM Step 3: Wait for database
echo Step 3: Waiting for database...
echo -----------------------------------
timeout /t 5 /nobreak >nul
echo Database ready
echo.

REM Step 4: Run migrations
echo Step 4: Running migrations...
echo -----------------------------------
docker-compose exec -T web python manage.py migrate
echo Migrations complete
echo.

REM Step 5: Collect static files
echo Step 5: Collecting static files...
echo -----------------------------------
docker-compose exec -T web python manage.py collectstatic --noinput
echo Static files collected
echo.

REM Step 6: Create finance users
echo Step 6: Creating finance users...
echo -----------------------------------
docker-compose exec -T web python manage.py create_finance_users
echo Finance users created
echo.

REM Step 7: Show container status
echo Step 7: Container status...
echo -----------------------------------
docker-compose ps
echo.

echo ==========================================
echo Local Development Environment Ready!
echo ==========================================
echo.
echo Access the application:
echo   Main Site:    http://localhost:8000
echo   Admin Panel:  http://localhost:8000/admin/
echo   Finance App:  http://localhost:8000/finance/login/
echo   Webmail:      http://localhost:8000/webmail/login/
echo   B2B Login:    http://localhost:8000/accounts/login/
echo.
echo Finance Login Credentials:
echo   Email: saddam110@mushqila.com
echo   Password: Sinan210
echo   User Type: Admin
echo.
echo Useful commands:
echo   View logs:       docker-compose logs -f web
echo   Stop:            docker-compose down
echo   Restart:         docker-compose restart
echo   Shell:           docker-compose exec web python manage.py shell
echo.
echo For more commands, see: RUN-LOCAL-DOCKER.md
echo.
pause
