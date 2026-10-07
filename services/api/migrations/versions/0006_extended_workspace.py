"""Tenant-scoped commerce, operations and automation resources."""
from alembic import op
from app.models import WorkspaceResource
from app.db import Base

revision = "0006_extended_workspace"
down_revision = "0005_attendance_device_keys"
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=[WorkspaceResource.__table__], checkfirst=True)
    op.execute("ALTER TABLE workspace_resources ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_resources FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON workspace_resources USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)")

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON workspace_resources")
    op.execute("ALTER TABLE workspace_resources NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_resources DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=op.get_bind(), tables=[WorkspaceResource.__table__])
