import sqlite3

connection = sqlite3.connect('data.db')
cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username text, password text)")
cursor.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, user_id text, filename text, path text)")
cursor.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id text, note text, date date)")

cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (1, "admin", "admin"))
connection.commit()

connection.close()