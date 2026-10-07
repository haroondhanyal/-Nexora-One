"""Tenant-isolated people, attendance and payroll tables."""
from alembic import op
from app import models

revision = "0003_people_payroll"
down_revision = "0002_company_profile"
branch_labels = None
depends_on = None

HR_TABLES = (models.Department.__table__, models.Employee.__table__, models.Shift.__table__, models.Attendance.__table__, models.AttendanceDeviceEvent.__table__, models.LeaveRequest.__table__, models.Compensation.__table__, models.PayrollRun.__table__, models.Payslip.__table__)

def upgrade():
    bind=op.get_bind()
    models.Base.metadata.create_all(bind=bind,tables=HR_TABLES,checkfirst=True)
    for table in ("departments","employees","shifts","attendance","attendance_device_events","leave_requests","compensations","payroll_runs","payslips"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation ON {table} USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)")

def downgrade():
    for table in ("payslips","payroll_runs","compensations","leave_requests","attendance_device_events","attendance","shifts","employees","departments"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    models.Base.metadata.drop_all(bind=op.get_bind(),tables=HR_TABLES)
