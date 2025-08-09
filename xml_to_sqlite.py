import sqlite3
import xml.etree.ElementTree as ET

# XML and DB file paths
XML_PATH = '/Users/eunyebok/Downloads/corp.xml'
DB_PATH = '/Users/eunyebok/vibe_250806_2/corp.db'

# Parse XML
tree = ET.parse(XML_PATH)
root = tree.getroot()

# Connect to SQLite DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS corp (
    corp_code TEXT PRIMARY KEY,
    corp_name TEXT NOT NULL
)
''')

# Insert data
count = 0
for corp in root.findall('list'):
    corp_code = corp.find('corp_code').text.strip()
    corp_name = corp.find('corp_name').text.strip()
    cursor.execute('INSERT OR IGNORE INTO corp (corp_code, corp_name) VALUES (?, ?)', (corp_code, corp_name))
    count += 1

conn.commit()
conn.close()
print(f"Inserted {count} companies into the database.")