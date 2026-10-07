"""Persist company profiles and tenant-scoped user preferences."""
from alembic import op

revision = "0002_company_profile"
down_revision = "0001_control_plane"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS address VARCHAR(500) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS currency VARCHAR(3) NOT NULL DEFAULT 'PKR'")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS timezone VARCHAR(80) NOT NULL DEFAULT 'Asia/Karachi'")
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            subject VARCHAR(255) NOT NULL,
            theme VARCHAR(40) NOT NULL DEFAULT 'Ocean Light',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_preferences_tenant_subject UNIQUE (tenant_id, subject)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_preferences_tenant_id ON user_preferences (tenant_id)")
    op.execute("ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_preferences FORCE ROW LEVEL SECURITY")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='user_preferences' AND policyname='tenant_isolation') THEN CREATE POLICY tenant_isolation ON user_preferences USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid); END IF; END $$")

def downgrade():
    op.execute("DROP TABLE IF EXISTS user_preferences")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS timezone")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS currency")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS address")
