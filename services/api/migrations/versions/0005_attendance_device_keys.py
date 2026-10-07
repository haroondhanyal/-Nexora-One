"""Per-tenant encrypted device signing credentials."""
from alembic import op
from app.models import AttendanceDeviceCredential
from app.db import Base

revision = "0005_attendance_device_keys"
down_revision = "0004_hr_workflows"
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind(),tables=[AttendanceDeviceCredential.__table__],checkfirst=True)
    op.execute("ALTER TABLE attendance_device_credentials ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE attendance_device_credentials FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON attendance_device_credentials USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)")

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON attendance_device_credentials")
    op.execute("ALTER TABLE attendance_device_credentials NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE attendance_device_credentials DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=op.get_bind(),tables=[AttendanceDeviceCredential.__table__])
