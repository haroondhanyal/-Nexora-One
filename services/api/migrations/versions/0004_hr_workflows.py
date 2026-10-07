"""Shift assignment and payroll separation-of-duties metadata."""
from alembic import op

revision = "0004_hr_workflows"
down_revision = "0003_people_payroll"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS shift_id UUID REFERENCES shifts(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE payroll_runs ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255) NOT NULL DEFAULT ''")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_employees_tenant_email') THEN ALTER TABLE employees ADD CONSTRAINT uq_employees_tenant_email UNIQUE (tenant_id, email); END IF; END $$")

def downgrade():
    op.execute("ALTER TABLE employees DROP CONSTRAINT IF EXISTS uq_employees_tenant_email")
    op.execute("ALTER TABLE payroll_runs DROP COLUMN IF EXISTS approved_by")
    op.execute("ALTER TABLE employees DROP COLUMN IF EXISTS shift_id")
