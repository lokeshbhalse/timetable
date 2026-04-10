@echo off
echo ========================================
echo Timetable Database Setup
echo ========================================

cd /d C:\Users\Prince\Desktop\time-table

echo Creating database from setup.sql...
sqlite3 timetable.db < setup.sql

echo.
echo ========================================
echo Database Setup Complete!
echo ========================================
echo.
echo Test the database:
sqlite3 timetable.db "SELECT * FROM users;"
echo.
pause