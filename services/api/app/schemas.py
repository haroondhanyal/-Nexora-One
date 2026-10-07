from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, field_validator

class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    industry: str = Field(default="General", max_length=100)

class CompanyProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    industry: str = Field(default="General", max_length=100)
    address: str = Field(default="", max_length=500)
    currency: str = Field(default="PKR", pattern="^[A-Z]{3}$")
    timezone: str = Field(default="Asia/Karachi", max_length=80)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Timezone must be a valid IANA timezone") from None
        return value

class UserPreferencesUpdate(BaseModel):
    theme: str = Field(pattern="^(Ocean Light|Midnight Dark|Emerald Light|Plum Dark|System)$")

class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    city: str = Field(default="", max_length=120)
    timezone: str = Field(default="Asia/Karachi", max_length=80)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Timezone must be a valid IANA timezone") from None
        return value

class MemberInvite(BaseModel):
    email: str = Field(min_length=6, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: str = Field(default="Staff", max_length=48)
    display_name: str = Field(default="Invited teammate", max_length=160)
    branch_ids: list[str] = Field(default_factory=list)

class MemberUpdate(BaseModel):
    role: str | None = Field(default=None, max_length=48)
    active: bool | None = None
    branch_ids: list[str] | None = None

class RecordCreate(BaseModel):
    kind: str = Field(pattern="^(leads|customers|suppliers|sales|purchasing|inventory|finance|payments|budgets|approvals)$")
    payload: dict

class RecordUpdate(BaseModel):
    payload: dict
    version: int = Field(ge=1)

class StatusCommand(BaseModel):
    status: str = Field(min_length=1, max_length=40)
    version: int = Field(ge=1)

class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)

class EmployeeCreate(BaseModel):
    employee_no: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=6, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str | None = Field(default=None, max_length=255)
    department_id: str | None = None
    branch_id: str | None = None
    shift_id: str | None = None
    job_title: str = Field(default="", max_length=120)
    hire_date: date

class ShiftCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time
    work_days: list[int] = Field(default_factory=lambda: [0,1,2,3,4], min_length=1, max_length=7)

class AttendanceCreate(BaseModel):
    employee_id: str | None = None
    work_date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    correction_reason: str = Field(default="", max_length=500)

class ReviewDecision(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")

class LeaveCreate(BaseModel):
    employee_id: str | None = None
    start_date: date
    end_date: date
    reason: str = Field(min_length=2, max_length=500)

class CompensationCreate(BaseModel):
    effective_from: date
    base_monthly: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    allowances: dict[str, Decimal] = Field(default_factory=dict)
    deductions: dict[str, Decimal] = Field(default_factory=dict)

class PayrollRunCreate(BaseModel):
    period_start: date
    period_end: date

class InventoryAdjustment(BaseModel):
    quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    reason: str = Field(min_length=3, max_length=500)
    version: int = Field(ge=1)

class DeliveryCommand(BaseModel):
    version: int = Field(ge=1)

class BudgetSpend(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str = Field(min_length=2, max_length=500)
    occurred_on: date
    version: int = Field(ge=1)

class PosSaleCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str = Field(min_length=2, max_length=240)
    tender: str = Field(pattern="^(cash|external_reference)$")
    reference: str = Field(default="", max_length=160)
    version: int = Field(ge=1)

class ReportRun(BaseModel):
    version: int = Field(ge=1)

class ManualPaymentMatch(BaseModel):
    finance_record_id: str = Field(min_length=36, max_length=36)
    version: int = Field(ge=1)
