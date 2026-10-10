import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now(): return datetime.now(timezone.utc)

class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    industry: Mapped[str] = mapped_column(String(100), default="General")
    address: Mapped[str] = mapped_column(String(500), default="")
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Karachi")
    status: Mapped[str] = mapped_column(String(24), default="provisioning")
    odoo_database: Mapped[str | None] = mapped_column(String(63), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "subject"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(48), default="Staff")
    branch_ids: Mapped[list] = mapped_column(JSONB, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(120), default="")
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Karachi")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class BusinessRecord(Base):
    __tablename__ = "business_records"
    __table_args__ = (Index("ix_record_tenant_kind", "tenant_id", "kind"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(48))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(default=1)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class WorkspaceResource(Base):
    __tablename__ = "workspace_resources"
    __table_args__ = (Index("ix_workspace_resource_kind", "tenant_id", "kind", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(48))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(default=1)
    created_by: Mapped[str] = mapped_column(String(255))
    updated_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class WorkspaceAttachment(Base):
    __tablename__ = "workspace_attachments"
    __table_args__ = (Index("ix_attachment_parent", "tenant_id", "entity_kind", "entity_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    entity_kind: Mapped[str] = mapped_column(String(48))
    entity_id: Mapped[str] = mapped_column(String(80))
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column()
    storage_key: Mapped[str] = mapped_column(String(64), unique=True)
    uploaded_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ApiClientCredential(Base):
    __tablename__ = "api_client_credentials"
    __table_args__ = (UniqueConstraint("tenant_id", "resource_id"), UniqueConstraint("token_hash"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspace_resources.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    subject: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(48))
    branch_ids: Mapped[list] = mapped_column(JSONB, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(160))
    entity: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80), default="")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    request_id: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("tenant_id", "key"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(200))
    request_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(48))
    branch_ids: Mapped[list] = mapped_column(JSONB, default=list)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("tenant_id", "subject"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    theme: Mapped[str] = mapped_column(String(40), default="Ocean Light")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_no"), UniqueConstraint("tenant_id", "subject"), UniqueConstraint("tenant_id", "email", name="uq_employees_tenant_email"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    employee_no: Mapped[str] = mapped_column(String(40))
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(320))
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    shift_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    job_title: Mapped[str] = mapped_column(String(120), default="")
    hire_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(24), default="active")

class Shift(Base):
    __tablename__ = "shifts"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    work_days: Mapped[list] = mapped_column(JSONB, default=lambda: [0,1,2,3,4])
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_id", "work_date"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    work_date: Mapped[date] = mapped_column(Date)
    check_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    source: Mapped[str] = mapped_column(String(24), default="self")
    correction_reason: Mapped[str] = mapped_column(String(500), default="")
    reviewed_by: Mapped[str] = mapped_column(String(255), default="")

class AttendanceDeviceEvent(Base):
    __tablename__ = "attendance_device_events"
    __table_args__ = (UniqueConstraint("tenant_id", "provider_event_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    provider_event_id: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AttendanceDeviceCredential(Base):
    __tablename__ = "attendance_device_credentials"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    key_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    secret_ciphertext: Mapped[str] = mapped_column(String(1000))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    reviewed_by: Mapped[str] = mapped_column(String(255), default="")

class Compensation(Base):
    __tablename__ = "compensations"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_id", "effective_from"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    effective_from: Mapped[date] = mapped_column(Date)
    base_monthly: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    allowances: Mapped[dict] = mapped_column(JSONB, default=dict)
    deductions: Mapped[dict] = mapped_column(JSONB, default=dict)

class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    __table_args__ = (UniqueConstraint("tenant_id", "period_start", "period_end"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(24), default="draft")
    created_by: Mapped[str] = mapped_column(String(255))
    approved_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = (UniqueConstraint("tenant_id", "run_id", "employee_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    base_monthly: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    allowance_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    deduction_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    net_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
