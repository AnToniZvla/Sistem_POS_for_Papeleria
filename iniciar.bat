@echo off
chcp 65001 > nul
echo Iniciando Sistema de Gestión - Papelería...
.venv\Scripts\python.exe menu.py
pause

echo.
echo El programa ha finalizado.
pause