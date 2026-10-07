"""Tenant-scoped hashed API client credentials."""
from alembic import op
from app.models import ApiClientCredential
from app.db import Base

revision = "0007_api_client_credentials"
down_revision = "0006_extended_workspace"
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=[ApiClientCredential.__table__], checkfirst=True)
    op.execute("ALTER TABLE api_client_credentials ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE api_client_credentials FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON api_client_credentials USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)")

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON api_client_credentials")
    op.execute("ALTER TABLE api_client_credentials NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE api_client_credentials DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=op.get_bind(), tables=[ApiClientCredential.__table__])
