@echo off
title RED ZONE - Local Test Server (1.20.4)
echo ====================================================
echo   RED ZONE - локальный тестовый сервер (Paper 1.20.4)
echo ====================================================
echo.

REM --- Память: -Xms стартовая, -Xmx максимальная. 4G хватает для теста. ---
java -Xms2G -Xmx4G -jar server.jar nogui

echo.
echo Сервер остановлен. Нажми любую клавишу для выхода...
pause >nul
