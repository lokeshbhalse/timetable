@echo off
echo ========================================
echo Setting up Timetable Database
echo ========================================

cd C:\Users\Prince\Desktop\time-table

echo Creating database...
sqlite3 timetable.db < setup.sql

echo.
echo Database setup complete!
echo.
echo To verify, run: python check_db.py
echo To use SQLite: sqlite3 timetable.db
echo.

pause