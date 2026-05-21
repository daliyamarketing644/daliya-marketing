import sqlite3

conn = sqlite3.connect('daliya.db')
cursor = conn.cursor()

try:
    # Brands table-il is_available column add cheyyunnu (Default 1 = Show)
    cursor.execute("ALTER TABLE brands ADD COLUMN is_available INTEGER DEFAULT 1")
    print("Brands table updated successfully!")
except sqlite3.OperationalError:
    print("Brands column already exists.")

try:
    # Products table-il is_available column add cheyyunnu (Default 1 = Show)
    cursor.execute("ALTER TABLE products ADD COLUMN is_available INTEGER DEFAULT 1")
    print("Products table updated successfully!")
except sqlite3.OperationalError:
    print("Products column already exists.")

conn.commit()
conn.close()