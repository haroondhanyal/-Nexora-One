"""Tenant scoped file attachments for workspace records."""
from alembic import op
from app.db import Base
from app.models import WorkspaceAttachment

revision = "0008_workspace_attachments"
down_revision = "0007_api_client_credentials"
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=[WorkspaceAttachment.__table__], checkfirst=True)
    op.execute("ALTER TABLE workspace_attachments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_attachments FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON workspace_attachments USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)")

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON workspace_attachments")
    op.execute("ALTER TABLE workspace_attachments NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_attachments DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=op.get_bind(), tables=[WorkspaceAttachment.__table__])
