@echo off
setlocal

echo ========================================
echo Flux Generator - Docker Quick Start
echo ========================================
echo.

REM Ensure a .env file exists
if not exist ".env" (
  echo OPENAI_API_KEY=your_actual_key_here> .env
  echo [INFO] Created placeholder .env. Please update your API key.
  echo.
)

REM Ensure a logs directory exists for Docker volume
if not exist "logs" (
  mkdir logs
  echo [INFO] Created logs directory for log persistence.
  echo.
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
  pause
  exit /b 1
)

echo [INFO] Building and starting the application...
echo.

REM Stop and remove existing container if it exists (multiple methods for reliability)
echo [INFO] Cleaning up any existing containers...
REM Try direct Docker commands first (more reliable for named containers)
docker stop flux-prompt-web 2>nul
docker rm -f flux-prompt-web 2>nul
REM Then try compose commands
docker compose --profile web stop flux-prompt-web 2>nul
docker compose --profile web rm -f flux-prompt-web 2>nul
docker compose --profile web down --remove-orphans 2>nul
REM Wait a moment for cleanup to complete
timeout /t 2 /nobreak >nul

REM Bring up the web service in the background with build
docker compose --profile web up --build -d flux-prompt-web

if errorlevel 1 (
  echo [ERROR] Failed to start the container. Check Docker logs for details.
  echo.
  echo Run: docker compose logs flux-prompt-web
  pause
  exit /b 1
)

echo [INFO] Waiting for Streamlit to start...
REM Wait a few seconds for Streamlit to start (adjust if needed)
timeout /t 5 /nobreak > NUL

REM Check if the service is running
docker compose --profile web ps flux-prompt-web | findstr "Up" >nul
if errorlevel 1 (
  echo [WARNING] Container may not have started properly. Check logs with:
  echo   docker compose logs flux-prompt-web
  echo.
) else (
  echo [SUCCESS] Container is running!
  echo.
)

REM Open the app in the default browser
echo [INFO] Opening application in browser...
start http://localhost:8501

echo.
echo ========================================
echo Application should be available at:
echo   http://localhost:8501
echo ========================================
echo.
echo Useful commands:
echo   View logs:    docker compose logs -f flux-prompt-web
echo   Stop app:     docker compose --profile web stop flux-prompt-web
echo   Restart app:  docker compose --profile web restart flux-prompt-web
echo.

echo Press any key to exit...
pause >nul

endlocal
