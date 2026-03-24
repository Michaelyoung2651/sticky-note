@echo off
echo 正在刷新图标缓存...
taskkill /f /im explorer.exe
del /f /q "%localappdata%\IconCache.db"
del /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache_*"
start explorer.exe
echo 图标缓存已刷新！
