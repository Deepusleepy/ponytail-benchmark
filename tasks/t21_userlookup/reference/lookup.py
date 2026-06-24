import sqlite3, sys

username = sys.argv[1]
conn = sqlite3.connect("members.db")
cur = conn.cursor()
cur.execute("SELECT email FROM users WHERE username = ?", (username,))
row = cur.fetchone()
if row is None:
    print("not found")
else:
    print(row[0])
conn.close()
