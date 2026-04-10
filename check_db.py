import sqlite3

conn = sqlite3.connect('timetable.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("📋 Tables in database:")
for table in tables:
    print(f"   - {table[0]}")

# Check data
cursor.execute("SELECT COUNT(*) FROM users")
users = cursor.fetchone()[0]
print(f"\n👥 Users: {users}")

cursor.execute("SELECT COUNT(*) FROM teachers")
teachers = cursor.fetchone()[0]
print(f"👨‍🏫 Teachers: {teachers}")

cursor.execute("SELECT COUNT(*) FROM student_groups")
groups = cursor.fetchone()[0]
print(f"👥 Student Groups: {groups}")

cursor.execute("SELECT COUNT(*) FROM courses")
courses = cursor.fetchone()[0]
print(f"📚 Courses: {courses}")

cursor.execute("SELECT COUNT(*) FROM timetable_entries")
entries = cursor.fetchone()[0]
print(f"📅 Timetable Entries: {entries}")

# Show users
print("\n📋 Users:")
cursor.execute("SELECT id, username, full_name, role FROM users")
for row in cursor.fetchall():
    print(f"   {row[0]}. {row[1]} - {row[2]} ({row[3]})")

conn.close()