import json
import sqlite3
import sys

case = json.load(sys.stdin)
action = case["action"]
db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys = ON")
db.executescript("""
CREATE TABLE parents(id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL);
CREATE TABLE resources(
  id INTEGER PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  business_key TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  parent_id INTEGER REFERENCES parents(id),
  UNIQUE(tenant_id, business_key)
);
INSERT INTO parents(id,tenant_id) VALUES(1,'tenant-a'),(2,'tenant-b');
INSERT INTO resources(tenant_id,business_key,parent_id) VALUES('tenant-a','fixture-a',1),('tenant-b','fixture-b',2);
""")
result = {"case": case["id"], "engine": "Python sqlite3 in-memory disposable database", "action": action}

if action == "select tenant-scoped rows":
    rows = db.execute("SELECT tenant_id,business_key FROM resources WHERE tenant_id=?", ("tenant-a",)).fetchall()
    assert rows and all(row[0] == "tenant-a" for row in rows)
elif action == "insert a valid fixture row":
    db.execute("INSERT INTO resources(tenant_id,business_key,parent_id) VALUES(?,?,?)", ("tenant-a", case["id"], 1))
    assert db.execute("SELECT 1 FROM resources WHERE tenant_id=? AND business_key=?", ("tenant-a", case["id"])).fetchone()
elif action == "update the fixture row with the current version":
    cursor = db.execute("UPDATE resources SET status='updated', version=version+1 WHERE tenant_id='tenant-a' AND business_key='fixture-a' AND version=1")
    assert cursor.rowcount == 1 and db.execute("SELECT version,status FROM resources WHERE business_key='fixture-a'").fetchone() == (2, "updated")
elif action == "delete the fixture row":
    assert db.execute("DELETE FROM resources WHERE tenant_id='tenant-a' AND business_key='fixture-a'").rowcount == 1
    assert not db.execute("SELECT 1 FROM resources WHERE business_key='fixture-a'").fetchone()
elif action == "reject a row with a missing required value":
    try: db.execute("INSERT INTO resources(tenant_id,business_key) VALUES('tenant-a',NULL)")
    except sqlite3.IntegrityError: pass
    else: raise AssertionError("NOT NULL constraint accepted a missing key")
elif action == "reject a duplicate business key":
    try: db.execute("INSERT INTO resources(tenant_id,business_key) VALUES('tenant-a','fixture-a')")
    except sqlite3.IntegrityError: pass
    else: raise AssertionError("tenant/business-key unique constraint accepted duplicate")
elif action == "rollback a transaction after a failed write":
    db.execute("BEGIN")
    try:
        db.execute("INSERT INTO resources(tenant_id,business_key) VALUES('tenant-a','fixture-a')")
        raise AssertionError("duplicate write unexpectedly succeeded")
    except sqlite3.IntegrityError: db.rollback()
    assert db.execute("SELECT COUNT(*) FROM resources WHERE business_key='fixture-a'").fetchone()[0] == 1
elif action == "deny a cross-tenant read":
    assert not db.execute("SELECT 1 FROM resources WHERE tenant_id='tenant-a' AND business_key='fixture-b'").fetchone()
elif action == "deny a cross-tenant update":
    cursor = db.execute("UPDATE resources SET status='stolen' WHERE tenant_id='tenant-a' AND business_key='fixture-b'")
    assert cursor.rowcount == 0 and db.execute("SELECT status FROM resources WHERE business_key='fixture-b'").fetchone()[0] == 'active'
elif action == "verify foreign-key references":
    try: db.execute("INSERT INTO resources(tenant_id,business_key,parent_id) VALUES('tenant-a','bad-parent',999)")
    except sqlite3.IntegrityError: pass
    else: raise AssertionError("foreign-key constraint accepted a missing parent")
elif action == "verify timestamp and status persistence":
    row = db.execute("SELECT created_at,status FROM resources WHERE business_key='fixture-a'").fetchone()
    assert row and row[0] and row[1] == 'active'
elif action == "confirm cleanup removes the fixture":
    db.execute("DELETE FROM resources WHERE tenant_id='tenant-a' AND business_key='fixture-a'")
    assert db.execute("SELECT COUNT(*) FROM resources WHERE business_key='fixture-a'").fetchone()[0] == 0
elif action == "complete report persistence lifecycle":
    db.executescript("CREATE TABLE reports(id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, payload TEXT NOT NULL, UNIQUE(tenant_id,title));")
    cursor = db.execute("INSERT INTO reports(tenant_id,title,payload) VALUES(?,?,?)", ("tenant-a", "Local QA report", '{"group_by":"status"}'))
    report_id = cursor.lastrowid
    created = db.execute("SELECT tenant_id,title,version FROM reports WHERE id=?", (report_id,)).fetchone()
    assert created == ("tenant-a", "Local QA report", 1)
    db.execute("UPDATE reports SET title=?,version=version+1 WHERE id=? AND tenant_id=? AND version=?", ("Local QA report updated", report_id, "tenant-a", 1))
    updated = db.execute("SELECT title,version FROM reports WHERE id=?", (report_id,)).fetchone()
    assert updated == ("Local QA report updated", 2)
    db.execute("DELETE FROM reports WHERE id=? AND tenant_id=?", (report_id, "tenant-a"))
    assert not db.execute("SELECT 1 FROM reports WHERE id=?", (report_id,)).fetchone()
elif action == "verify tenant membership boundaries":
    db.executescript("CREATE TABLE memberships(tenant_id TEXT NOT NULL, user_id TEXT NOT NULL, UNIQUE(tenant_id,user_id)); INSERT INTO memberships VALUES('tenant-a','user-a'),('tenant-b','user-b');")
    owned = db.execute("SELECT user_id FROM memberships WHERE tenant_id=?", ("tenant-a",)).fetchall()
    foreign = db.execute("SELECT user_id FROM memberships WHERE tenant_id=? AND user_id=?", ("tenant-a", "user-b")).fetchone()
    assert owned == [("user-a",)] and foreign is None
else:
    raise AssertionError(f"Unsupported catalog action: {action}")

db.close()
print(json.dumps(result))
