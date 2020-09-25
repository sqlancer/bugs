import json
import argparse
import sys
from datetime import datetime


parser = argparse.ArgumentParser(prog='bugs.py')
parser.add_argument('action', choices=['check', 'format', 'export_database'])
args = parser.parse_args()

f = open("bugs.json", "r")
original_content = f.read()
parsed_content = json.loads(original_content)

def check():
    formatted_content = json.dumps(parsed_content, indent=4) + '\n'
    correctly_formatted = original_content == formatted_content
    sys.exit(0 if correctly_formatted else -1)

def format_json():
    formatted_content = json.dumps(parsed_content, indent=4) + '\n'
    f.close()
    fw = open("bugs.json", "w")
    fw.write(formatted_content)

def export_database():
    import sqlite3
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE DBMS_BUGS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        DBMS STRING,
        ORACLE STRING,
        STATUS STRING,
        DATE STRING,
        TEST STRING,
        TRIGGER_BUG_LINE STRING,
        SEVERITY STRING,
        URL_EMAIL STRING,
        URL_BUGTRACKER STRING,
        URL_FIX STRING
    );
    """)
    c.execute("""
    CREATE TABLE BUG_TEST_CASES(
        id INTEGER,
        STATEMENT STRING,
        POSITION INTEGER,
        FOREIGN KEY(id) REFERENCES DBMS_BUGS(id)
    );
    """)
    c.execute("""
    CREATE VIEW DBMS_BUGS_TRUE_POSITIVES AS
    SELECT * FROM DBMS_BUGS WHERE STATUS IN ('fixed', 'open', 'verified', 'fixed (in documentation)')
    """)
    c.execute("""
    CREATE VIEW DBMS_BUGS_FALSE_POSITIVES AS
    SELECT * FROM DBMS_BUGS WHERE id not IN (SELECT id FROM DBMS_BUGS_TRUE_POSITIVES);
    """)
    c.execute("""
    CREATE VIEW DBMS_BUGS_STATUS AS
    SELECT d1.DATABASE, d2.status, (SELECT COUNT(*) FROM DBMS_BUGS d3 WHERE d3.DATABASE = d1.DATABASE AND d3.STATUS = d2.STATUS) as count FROM DBMS_BUGS d1, DBMS_BUGS d2 GROUP BY d1.DATABASE, d2.STATUS;
    """)
    for bug_entry in parsed_content:
        date = datetime.strptime(bug_entry['date'], '%d/%m/%Y')
        severity = bug_entry.get('severity', None)
        c.execute("""INSERT INTO DBMS_BUGS (DBMS, ORACLE, STATUS, DATE, TEST, TRIGGER_BUG_LINE, SEVERITY, URL_EMAIL, URL_BUGTRACKER, URL_FIX) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (bug_entry['dbms'], bug_entry['oracle'], bug_entry['status'], bug_entry['date'], bug_entry['test'], bug_entry['test'].split('\n')[-1], severity, bug_entry.get('links', {}).get('email', None), bug_entry.get('links', {}).get('bugtracker', None), bug_entry.get('links', {}).get('fix', None)));
        rid = c.execute('select last_insert_rowid();').fetchall()[0][0]
        seq = 0
        for statement in bug_entry['test'].split('\n'):
            if not (statement.startswith('--') or statement == ''):
                c.execute('INSERT INTO BUG_TEST_CASES(id, STATEMENT, POSITION) VALUES(%d, "%s", %d)' % (rid, statement.replace('"', '""'), seq))
                seq += 1
    conn.commit()
action = args.action
{
    'check' : check,
    'format' : format_json,
    'export_database' : export_database
}[action]()
