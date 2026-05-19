@echo off

cd /d C:\project\app

call venv\Scripts\activate.bat

set QT_QPA_PLATFORM=vnc
set QT_OPENGL=software
set QT_QUICK_BACKEND=software
set QSG_RHI_BACKEND=software

python Main.py

pause