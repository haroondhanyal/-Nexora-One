"""Initial control plane tables and row security."""
from alembic import op
from app.db import Base
from app import models  # noqa

revision = "0001_control_plane"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind())
    for table in ("branches", "business_records", "audit_events", "invitations", "idempotency_keys", "user_preferences"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        invitation_lookup=" OR token_hash = nullif(current_setting('app.invitation_hash', true), '')" if table=="invitations" else ""
        op.execute(f"CREATE POLICY tenant_isolation ON {table} USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid{invitation_lookup}) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)")

def downgrade():
    for table in ("user_preferences", "idempotency_keys", "invitations", "audit_events", "business_records", "branches"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=op.get_bind())
