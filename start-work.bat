@echo off
title Start work - getting the latest
cd /d "%~dp0"

echo.
echo  Updating %CD%
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo  [X] This folder is not a git repository.
    echo.
    pause
    exit /b 1
)

git pull --rebase
if errorlevel 1 (
    echo.
    echo  [!] A conflict needs your input. Open GitHub Desktop.
    echo.
    pause
    exit /b 1
)

echo.
echo  up to date - you can start working
echo.
timeout /t 3 >nul
