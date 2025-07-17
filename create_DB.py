import sqlite3
from datetime import datetime
import os
# Connect to SQLite database (or create it if it doesn't exist)


ass = 1
print(ass)
ASS = "more"
print(ASS)
ASS = ASS + "more ass"
print(ASS)
"""
os.remove('database.db')

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create tables


cursor.execute('''
CREATE TABLE IF NOT EXISTS User (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    Node INTEGER,
    Tokens REAL,
    FOREIGN KEY (Node) REFERENCES Node(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Node (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    User INTEGER,
    HWConfig INTEGER,
    SWConfig INTEGER,
    FreeSpaceMB INTEGER,
    BenchmarkResult INTEGER,
    LastPing DATETIME,
    State INTERER,
    ram INTEGER,
    FOREIGN KEY (User) REFERENCES User(ID),
    FOREIGN KEY (HWConfig) REFERENCES HWConfig(ID),
    FOREIGN KEY (SWConfig) REFERENCES SWConfig(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS SWConfig (
    Node INTEGER,
    ProgramPlugin INTEGER,
    FOREIGN KEY (Node) REFERENCES Node(ID),
    FOREIGN KEY (ProgramPlugin) REFERENCES ProgramPlugin(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS ProgramPlugin (
    Program INTEGER,
    Plugin INTEGER,
    Compatibility TEXT,
    FOREIGN KEY (Program) REFERENCES Program(ID),
    FOREIGN KEY (Plugin) REFERENCES Plugin(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Plugin (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    Version TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Program (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Project (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    User INTEGER,
    Name TEXT,
    RenderResult INTEGER,
    File INTEGER,
    Program INTEGER,
    RAMrequirementMB INTEGER,
    VRAMrequirementMB INTEGER,
    Priority INTEGER,
    FOREIGN KEY (User) REFERENCES User(ID),
    FOREIGN KEY (RenderResult) REFERENCES RenderResult(ID),
    FOREIGN KEY (File) REFERENCES File(ID),
    FOREIGN KEY (Program) REFERENCES Program(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS File (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Path TEXT,
    Name TEXT,
    User INTEGER,
    Size INTEGER,
    Date DATETIME,
    Hash TEXT,
    IsDeleted BOOLEAN,
    FOREIGN KEY (User) REFERENCES User(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Asset (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Project INTEGER,
    File INTEGER,
    FOREIGN KEY (Project) REFERENCES Project(ID),
    FOREIGN KEY (File) REFERENCES File(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS RenderResult (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Project INTEGER,
    Node INTEGER,
    File INTEGER,
    Tokens INTEGER,
    Errors TEXT,
    Info TEXT,
    Start DATETIME,
    End DATETIME,
    FOREIGN KEY (Project) REFERENCES Project(ID),
    FOREIGN KEY (Node) REFERENCES Node(ID),
    FOREIGN KEY (File) REFERENCES File(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS NodeBenchmark (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Node INTEGER,
    Program INTEGER,
    Benchmark REAL,
    RenderResult INTEGER,
    FOREIGN KEY (Node) REFERENCES Node(ID),
    FOREIGN KEY (Program) REFERENCES Program(ID)
    FOREIGN KEY (RenderResult) REFERENCES RenderResult(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS HWConfig (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    CPU INTEGER,
    GPU INTEGER,
    FOREIGN KEY (CPU) REFERENCES CPU(ID),
    FOREIGN KEY (GPU) REFERENCES GPU(ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS CPU (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    speed TEXT,
    cores INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS GPU (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    vram TEXT
)
''')

cursor.execute('''
               CREATE TABLE IF NOT EXISTS NodeFile(
               ID INTEGER PRIMARY KEY AUTOINCREMENT,
               Node INTEGER,
               File INTEGER,
               FOREIGN KEY (Node) REFERENCES Node(ID),
               FOREIGN KEY (File) REFERENCES File(ID)
               )
               ''')

cursor.execute('''
               
               
               INSERT INTO User (ID,username,password) VALUES (-1,'ad','ass')

               
               
               ''')


cursor.execute('''
               
               
               INSERT INTO File (id, Path, Name, Hash) VALUES (-1,'special/Benchmark.blend','b.blend', '42837084d7c0703a2f2f4abf65fa5fdb')

               
               
               ''')


cursor.execute('''
               
               
               INSERT INTO Project (id, User, Name, Priority, File) VALUES (-1,-1,'b.blend', 400, -1)

               
               
               ''')


# Commit changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")



"""