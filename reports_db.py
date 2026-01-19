import sqlite3

DB_NAME = "reports.db"

def init_db():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        activity TEXT,
        result TEXT
    )
    """)
    con.commit()
    con.close()

def add_report(date, activity, result):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("INSERT INTO reports(date,activity,result) VALUES(?,?,?)",
                (date, activity, result))
    con.commit()
    con.close()

def get_all_reports():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("SELECT date, activity, result FROM reports ORDER BY id DESC")
    data = cur.fetchall()
    con.close()
    return data
