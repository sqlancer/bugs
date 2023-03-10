#!/usr/bin/env python3

"""This script provides functionality to validate, manipulate, and
transform the bugs.json file."""

import json
import argparse
import sys
import sqlite3
from jsonschema import validate

parser = argparse.ArgumentParser(prog='bugs.py')
parser.add_argument('action', choices=['check', 'format', 'export_database'])
args = parser.parse_args()


def check():
    """Checks that the JSON file is correctly formatted."""
    formatted_content = json.dumps(parsed_content, indent=4) + '\n'
    correctly_formatted = original_content == formatted_content
    if not correctly_formatted:
        sys.exit(-1)
    schema = {
        "type": "array",
        "items": {
            "required": ["date", "dbms", "oracle", "reporter",
                         "status", "test", "title"],
            "properties": {
                "date": {"type": "string"},
                "dbms": {
                    "type": "string",
                    "pattern": r"^(SQLite|MySQL|PostgreSQL|TDEngine|"
                               r"MariaDB|CockroachDB|TiDB|DuckDB|H2)$",
                },
                "links": {
                    "type": "object"
                },
                "oracle": {
                    "type": "string",
                    "pattern": r"^(PQS|error|crash|NoREC|hang|"
                               r"TLP \(aggregate\)|TLP \(HAVING\)|"
                               r"TLP \(WHERE\)|TLP \(GROUP BY\)|"
                               r"TLP \(DISTINCT\))$"
                },
                "reporter": {"type": "string"},
                "severity": {"type": "string"},
                "status": {
                    "type": "string",
                    "pattern": r"^(closed \(not a bug\)|fixed|"
                               r"closed \(duplicate\)|"
                               r"fixed \(in documentation\)|verified|open)$"
                },
                "test": {"type": "array", "items": {"type": "string"}},
                "title": {"type": "string"},
            }
        }
    }
    validate(instance=parsed_content, schema=schema)


def format_json():
    """Consistently formats the JSON file."""
    formatted_content = json.dumps(parsed_content,
                                   indent=4,
                                   sort_keys=True,
                                   separators=(',', ': ')) + '\n'
    f.close()
    with open("bugs.json", "w", encoding="utf-8") as f_w:
        f_w.write(formatted_content)


def export_database():
    """Exports the JSON bug file as a SQLite3 database."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
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
        URL_FIX STRING,
        REPORTER STRING
    );
    """)
    cursor.execute("""
    CREATE TABLE BUG_TEST_CASES(
        id INTEGER,
        STATEMENT STRING,
        POSITION INTEGER,
        FOREIGN KEY(id) REFERENCES DBMS_BUGS(id)
    );
    """)
    cursor.execute("""
    CREATE VIEW DBMS_BUGS_TRUE_POSITIVES AS
    SELECT * FROM DBMS_BUGS
    WHERE STATUS IN ('fixed', 'open', 'verified', 'fixed (in documentation)')
    """)
    cursor.execute("""
    CREATE VIEW DBMS_BUGS_FALSE_POSITIVES AS
    SELECT * FROM DBMS_BUGS
    WHERE id not IN (SELECT id FROM DBMS_BUGS_TRUE_POSITIVES);
    """)
    cursor.execute("""
    CREATE VIEW DBMS_BUGS_STATUS AS
    SELECT d1.DATABASE, d2.status, (SELECT COUNT(*) FROM DBMS_BUGS d3
        WHERE d3.DATABASE = d1.DATABASE AND d3.STATUS = d2.STATUS) as count
        FROM DBMS_BUGS d1, DBMS_BUGS d2 GROUP BY d1.DATABASE, d2.STATUS;
    """)
    for bug_entry in parsed_content:
        severity = bug_entry.get('severity', None)
        links = bug_entry.get('links', {})
        cursor.execute("""INSERT INTO DBMS_BUGS (DBMS, ORACLE, STATUS, DATE,
        TEST, TRIGGER_BUG_LINE, SEVERITY, URL_EMAIL, URL_BUGTRACKER, URL_FIX,
            REPORTER)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (bug_entry['dbms'], bug_entry['oracle'],
                        bug_entry['status'],
                        bug_entry['date'],
                        '\n'.join(bug_entry['test']),
                        bug_entry['test'][-1],
                        severity,
                        links.get('email', None),
                        links.get('bugtracker', None),
                        links.get('fix', None),
                        bug_entry['reporter']))
        rid = cursor.execute('select last_insert_rowid();').fetchall()[0][0]
        seq = 0
        for statement in bug_entry['test']:
            if not (statement.startswith('--') or statement == ''):
                statement_replaced = statement.replace('"', '""')
                command = (
                    f"INSERT INTO BUG_TEST_CASES"
                    f"(id, STATEMENT, POSITION)"
                    f"VALUES({rid}, \"{statement_replaced}\", {seq})"
                )
                cursor.execute(command)
                seq += 1
    conn.commit()


with open("bugs.json", "r", encoding="utf-8") as f:
    original_content = f.read()
    parsed_content = json.loads(original_content)

action = args.action
{
    'check': check,
    'format': format_json,
    'export_database': export_database
}[action]()
