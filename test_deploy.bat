@echo off
echo Test Deployment Script
echo ====================

echo Checking folder structure...
if not exist "backend" (
    echo ERROR: backend folder not found!
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    exit /b 1
)

echo Checking Python files syntax...
for /r backend %%f in (*.py) do (
    python -m py_compile "%%f"
    if errorlevel 1 (
        echo ERROR: Syntax error in %%f
        exit /b 1
    )
)

echo All Python files compiled successfully!

echo Checking Django settings...
cd backend
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); print('Django settings OK')"
if errorlevel 1 (
    echo ERROR: Django settings problem
    exit /b 1
)

echo Testing models import...
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from prenotazioni.models import Utente, Risorsa, Prenotazione; print('Models import OK')"
if errorlevel 1 (
    echo ERROR: Models import problem
    exit /b 1
)

cd ..
echo All checks passed! The application should deploy correctly.
