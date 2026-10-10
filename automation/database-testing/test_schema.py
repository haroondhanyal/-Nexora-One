"""Safe, opt-in schema and row-level-security checks for a disposable local DB."""
import os
import unittest
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


DATABASE_URL = os.getenv("NEXORA_TEST_DATABASE_URL", "")
ALLOW_TRANSACTIONAL_FIXTURES = os.getenv("NEXORA_TEST_DATABASE_ALLOW_WRITE") == "1"
SAFE_LOCAL_DATABASE = False
if DATABASE_URL:
    try:
        parsed_url = make_url(DATABASE_URL)
        SAFE_LOCAL_DATABASE = parsed_url.host in {"localhost", "127.0.0.1", "::1"} and bool(parsed_url.database) and any(word in parsed_url.database.lower() for word in ("test", "k6"))
    except Exception:
        SAFE_LOCAL_DATABASE = False


@unittest.skipUnless(SAFE_LOCAL_DATABASE, "Set NEXORA_TEST_DATABASE_URL to a localhost database with 'test' or 'k6' in its name.")
class DatabaseSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_migrations_are_at_head(self):
        with self.engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        self.assertEqual(revision, "0008_workspace_attachments")

    def test_required_tenant_tables_exist(self):
        tables = set(inspect(self.engine).get_table_names())
        self.assertTrue({"tenants", "memberships", "business_records", "workspace_resources", "workspace_attachments", "departments", "employees", "payroll_runs", "payslips"}.issubset(tables))

    def test_tenant_sensitive_tables_force_row_security(self):
        with self.engine.connect() as connection:
            rows = connection.execute(text("SELECT c.relname, c.relforcerowsecurity, p.policyname FROM pg_class c JOIN pg_policies p ON p.tablename=c.relname WHERE c.relname IN ('branches','business_records','audit_events','user_preferences','workspace_resources','workspace_attachments') AND p.policyname='tenant_isolation'" )).all()
        self.assertGreaterEqual(len(rows), 6)
        self.assertTrue(all(row.relforcerowsecurity for row in rows))

    @unittest.skipUnless(ALLOW_TRANSACTIONAL_FIXTURES, "Set NEXORA_TEST_DATABASE_ALLOW_WRITE=1 to enable rollback-only tenant-isolation fixtures.")
    def test_database_rows_are_isolated_between_tenants(self):
        tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
        record_a, record_b = str(uuid.uuid4()), str(uuid.uuid4())
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
                connection.execute(text("INSERT INTO tenants (id,name,slug,industry,address,currency,timezone,status,created_at) VALUES (:id,:name,:slug,'General','','PKR','Asia/Karachi','ready',:created_at)"), {"id":tenant_id,"name":f"DB Contract {suffix}","slug":f"db-contract-{uuid.uuid4().hex}","created_at":datetime.now(timezone.utc)})
            for tenant_id, record_id in ((tenant_a, record_a), (tenant_b, record_b)):
                connection.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id":tenant_id})
                connection.execute(text("INSERT INTO business_records (id,tenant_id,kind,payload,version,created_by,created_at,updated_at) VALUES (:id,:tenant_id,'leads',CAST(:payload AS jsonb),1,'db-contract-test',:created_at,:created_at)"), {"id":record_id,"tenant_id":tenant_id,"payload":'{"title":"isolated fixture"}',"created_at":datetime.now(timezone.utc)})
            visible_a = connection.execute(text("SELECT id::text FROM business_records WHERE id IN (:record_a,:record_b)"), {"record_a":record_a,"record_b":record_b}).scalars().all()
            self.assertEqual(visible_a, [record_b])  # The final tenant context is tenant B.
            connection.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id":tenant_a})
            visible_a = connection.execute(text("SELECT id::text FROM business_records WHERE id IN (:record_a,:record_b) ORDER BY id"), {"record_a":record_a,"record_b":record_b}).scalars().all()
            self.assertEqual(visible_a, [record_a])
        finally:
            transaction.rollback()
            connection.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
