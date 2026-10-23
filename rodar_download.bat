@echo off
cd /d D:\Carreira\portfolio\leilao
python src\baixar_caixa.py >> dados\download.log 2>&1
if %ERRORLEVEL% equ 0 (
    python src\ler_caixa.py >> dados\download.log 2>&1
)

