@echo off
setlocal ENABLEEXTENSIONS

:: Verifica si estamos en un repositorio Git
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ❌ No estás dentro de un repositorio Git.
    pause
    exit /b
)

echo ✅ Repositorio Git detectado.
set count=1

:loop
cls
echo =========================================
echo 📦 Auto commit #%count% - %date% %time%
echo =========================================

git add .
git commit -m "Auto commit %count%" >nul 2>&1

if %errorlevel% equ 0 (
    echo ✅ Commit realizado.
    git push origin main >nul 2>&1
    echo 🚀 Push a main completado.
) else (
    echo ⚠️ No hay cambios para guardar.
)

:: Cada 10 commits, reseteamos historial
if "%count%"=="10" (
    echo 🔁 Squash de los últimos 10 commits...
    git reset --soft HEAD~10
    git commit -m "🔁 Historial limpio"
    git push --force origin main
    set count=1
) else (
    set /a count+=1
)

echo ⏳ Esperando 60 segundos...
timeout /t 60 >nul
goto loop
