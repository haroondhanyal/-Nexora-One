import base64, hashlib, hmac, json, os, secrets, time, uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from .db import get_db
from .models import Attendance, AttendanceDeviceCredential, AttendanceDeviceEvent, AuditEvent, Branch, Compensation, Department, Employee, LeaveRequest, Membership, PayrollRun, Payslip, Shift, Tenant
from .payroll import calculate_period_pay, payroll_csv
from .schemas import AttendanceCreate, CompensationCreate, DepartmentCreate, EmployeeCreate, LeaveCreate, PayrollRunCreate, ReviewDecision, ShiftCreate
from .security import allow, identity, membership

router=APIRouter(prefix="/api/v1/hr",tags=["people"])
MANAGERS=("Owner","Admin","HR manager")
HR_USERS=(*MANAGERS,"Employee")

def audit(db, member, request, action, entity, entity_id="", detail=None):
    db.add(AuditEvent(tenant_id=member.tenant_id,actor=member.subject,action=action,entity=entity,entity_id=entity_id,detail=detail or {},request_id=request.state.request_id))

def device_fernet():
    master=os.getenv("ATTENDANCE_DEVICE_MASTER_KEY","").encode()
    if len(master)<32: raise HTTPException(503,"Attendance device encryption key is not configured")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(master).digest()))

def current_employee(db:Session, member:Membership)->Employee:
    employee=db.scalar(select(Employee).where(Employee.tenant_id==member.tenant_id,Employee.subject==member.subject,Employee.status=="active"))
    if not employee: raise HTTPException(404,"Your employee profile is not linked to this account")
    return employee

def parse_uuid(value:str|None,label:str):
    if not value: return None
    try: return uuid.UUID(value)
    except ValueError: raise HTTPException(422,f"{label} must be a valid ID") from None

def get_employee(db:Session, member:Membership, employee_id:uuid.UUID)->Employee:
    row=db.scalar(select(Employee).where(Employee.id==employee_id,Employee.tenant_id==member.tenant_id))
    if not row: raise HTTPException(404,"Employee not found")
    if member.role not in MANAGERS and row.subject!=member.subject: raise HTTPException(404,"Employee not found")
    return row

def person_data(db, row):
    department=db.get(Department,row.department_id) if row.department_id else None
    shift=db.get(Shift,row.shift_id) if row.shift_id else None
    return {"id":str(row.id),"employee_no":row.employee_no,"name":row.name,"email":row.email,"department_id":str(row.department_id) if row.department_id else "","department":department.name if department else "","branch_id":str(row.branch_id) if row.branch_id else "","shift_id":str(row.shift_id) if row.shift_id else "","shift":shift.name if shift else "","job_title":row.job_title,"hire_date":row.hire_date.isoformat(),"status":row.status}

def serialize_attendance(row, employee_name=""):
    return {"id":str(row.id),"employee_id":str(row.employee_id),"employee_name":employee_name,"work_date":row.work_date.isoformat(),"check_in":row.check_in.isoformat() if row.check_in else "","check_out":row.check_out.isoformat() if row.check_out else "","status":row.status,"source":row.source,"correction_reason":row.correction_reason,"reviewed_by":row.reviewed_by}

def serialize_leave(row, employee_name=""):
    return {"id":str(row.id),"employee_id":str(row.employee_id),"employee_name":employee_name,"start_date":row.start_date.isoformat(),"end_date":row.end_date.isoformat(),"days":(row.end_date-row.start_date).days+1,"reason":row.reason,"status":row.status,"reviewed_by":row.reviewed_by}

@router.get("/departments")
def departments(db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    return [{"id":str(row.id),"name":row.name,"status":"Active" if row.active else "Disabled"} for row in db.scalars(select(Department).where(Department.tenant_id==member.tenant_id).order_by(Department.name))]

@router.post("/departments",status_code=201)
def create_department(body:DepartmentCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    row=Department(tenant_id=member.tenant_id,name=body.name.strip());db.add(row);db.flush();audit(db,member,request,"hr.department_created","department",str(row.id));db.commit()
    return {"id":str(row.id),"name":row.name,"status":"Active"}

@router.get("/employees")
def employees(db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    rows=db.scalars(select(Employee).where(Employee.tenant_id==member.tenant_id,Employee.status!="deleted").order_by(Employee.name))
    if member.role not in MANAGERS: rows=[row for row in rows if row.subject==member.subject]
    return [person_data(db,row) for row in rows]

@router.post("/employees",status_code=201)
def create_employee(body:EmployeeCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    department_id=None
    branch_id=None
    shift_id=None
    if body.department_id:
        department_id=parse_uuid(body.department_id,"Department ID")
        if not db.scalar(select(Department.id).where(Department.id==department_id,Department.tenant_id==member.tenant_id)): raise HTTPException(422,"Department is outside this workspace")
    if body.branch_id:
        branch_id=parse_uuid(body.branch_id,"Branch ID")
        if not db.scalar(select(Branch.id).where(Branch.id==branch_id,Branch.tenant_id==member.tenant_id)): raise HTTPException(422,"Branch is outside this workspace")
    if body.shift_id:
        shift_id=parse_uuid(body.shift_id,"Shift ID")
        if not db.scalar(select(Shift.id).where(Shift.id==shift_id,Shift.tenant_id==member.tenant_id,Shift.active.is_(True))): raise HTTPException(422,"Shift is outside this workspace")
    if body.subject and not db.scalar(select(Membership.id).where(Membership.tenant_id==member.tenant_id,Membership.subject==body.subject,Membership.active.is_(True))): raise HTTPException(422,"Link the employee to an active workspace member")
    row=Employee(tenant_id=member.tenant_id,employee_no=body.employee_no,name=body.name,email=body.email.lower(),subject=body.subject,department_id=department_id,branch_id=branch_id,shift_id=shift_id,job_title=body.job_title,hire_date=body.hire_date)
    db.add(row);db.flush();audit(db,member,request,"hr.employee_created","employee",str(row.id));db.commit()
    return person_data(db,row)

@router.get("/me")
def my_employee(db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    return person_data(db,current_employee(db,member))

@router.post("/me/link")
def link_employee_profile(request:Request,user:dict=Depends(identity),db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    if user.get("email_verified") is not True or not user.get("email"): raise HTTPException(403,"A verified email is required to link an employee profile")
    existing=db.scalar(select(Employee).where(Employee.tenant_id==member.tenant_id,Employee.subject==member.subject))
    if existing: return person_data(db,existing)
    row=db.scalar(select(Employee).where(Employee.tenant_id==member.tenant_id,Employee.email==user["email"].lower(),Employee.subject.is_(None),Employee.status=="active"))
    if not row: raise HTTPException(404,"No unlinked active employee profile matches your verified email")
    row.subject=member.subject
    audit(db,member,request,"hr.employee_profile_linked","employee",str(row.id));db.commit()
    return person_data(db,row)

@router.get("/shifts")
def shifts(db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    return [{"id":str(x.id),"name":x.name,"start_time":x.start_time.isoformat(),"end_time":x.end_time.isoformat(),"work_days":x.work_days,"status":"Active" if x.active else "Disabled"} for x in db.scalars(select(Shift).where(Shift.tenant_id==member.tenant_id).order_by(Shift.name))]

@router.post("/shifts",status_code=201)
def create_shift(body:ShiftCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    if any(x not in range(7) for x in body.work_days): raise HTTPException(422,"Work days use weekday numbers 0–6")
    if body.end_time<=body.start_time: raise HTTPException(422,"Shift end must be later than shift start")
    row=Shift(tenant_id=member.tenant_id,name=body.name,start_time=body.start_time,end_time=body.end_time,work_days=sorted(set(body.work_days)));db.add(row);db.flush();audit(db,member,request,"hr.shift_created","shift",str(row.id));db.commit()
    return {"id":str(row.id),"name":row.name,"start_time":row.start_time.isoformat(),"end_time":row.end_time.isoformat(),"work_days":row.work_days,"status":"Active"}

@router.get("/attendance")
def attendance(start:date|None=None,end:date|None=None,db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    query=select(Attendance).where(Attendance.tenant_id==member.tenant_id)
    if start: query=query.where(Attendance.work_date>=start)
    if end: query=query.where(Attendance.work_date<=end)
    rows=db.scalars(query.order_by(Attendance.work_date.desc()).limit(1000))
    if member.role not in MANAGERS:
        emp=current_employee(db,member);rows=[x for x in rows if x.employee_id==emp.id]
    return [serialize_attendance(x,db.get(Employee,x.employee_id).name) for x in rows]

@router.post("/attendance",status_code=201)
def record_attendance(body:AttendanceCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    employee=current_employee(db,member) if member.role not in MANAGERS and not body.employee_id else get_employee(db,member,parse_uuid(body.employee_id,"Employee ID")) if body.employee_id else None
    if employee is None: raise HTTPException(422,"Select an employee")
    tenant=db.get(Tenant,member.tenant_id)
    try: tenant_today=datetime.now(ZoneInfo(tenant.timezone if tenant else "UTC")).date()
    except ZoneInfoNotFoundError: tenant_today=datetime.now(timezone.utc).date()
    if member.role not in MANAGERS and body.work_date!=tenant_today and not body.correction_reason.strip(): raise HTTPException(403,"Add a correction reason for attendance outside today")
    if not body.check_in and not body.check_out: raise HTTPException(422,"Provide a check-in or check-out time")
    if body.check_in and body.check_in.tzinfo is None or body.check_out and body.check_out.tzinfo is None: raise HTTPException(422,"Attendance timestamps must include a timezone")
    if body.check_in and body.check_out and body.check_out<body.check_in: raise HTTPException(422,"Check-out must be after check-in")
    row=db.scalar(select(Attendance).where(Attendance.tenant_id==member.tenant_id,Attendance.employee_id==employee.id,Attendance.work_date==body.work_date))
    prior_values={"check_in":row.check_in.isoformat() if row and row.check_in else "","check_out":row.check_out.isoformat() if row and row.check_out else "","status":row.status if row else "new"}
    if row and row.status=="approved" and member.role not in MANAGERS and not body.correction_reason.strip(): raise HTTPException(409,"Add a correction reason before requesting an HR change")
    if row is None: row=Attendance(tenant_id=member.tenant_id,employee_id=employee.id,work_date=body.work_date);db.add(row)
    row.check_in=body.check_in or row.check_in;row.check_out=body.check_out or row.check_out;row.status="pending";row.source="self" if member.role not in MANAGERS else "hr";row.correction_reason=body.correction_reason
    db.flush();audit(db,member,request,"hr.attendance_submitted","attendance",str(row.id),{"reason":body.correction_reason,"previous":prior_values,"requested":{"check_in":row.check_in.isoformat() if row.check_in else "","check_out":row.check_out.isoformat() if row.check_out else ""}});db.commit()
    return serialize_attendance(row,employee.name)

@router.post("/attendance/device-credentials",status_code=201)
def create_device_credential(request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    cipher=device_fernet();
    for old in db.scalars(select(AttendanceDeviceCredential).where(AttendanceDeviceCredential.tenant_id==member.tenant_id,AttendanceDeviceCredential.active.is_(True))): old.active=False
    key_id=str(uuid.uuid4());secret=secrets.token_urlsafe(48)
    row=AttendanceDeviceCredential(tenant_id=member.tenant_id,key_id=key_id,secret_ciphertext=cipher.encrypt(secret.encode()).decode(),active=True)
    db.add(row);audit(db,member,request,"hr.attendance_device_key_rotated","attendance_device_credential",key_id);db.commit()
    return {"key_id":key_id,"secret":secret,"warning":"Copy this secret now. It cannot be retrieved again."}

@router.delete("/attendance/device-credentials/{key_id}",status_code=204)
def revoke_device_credential(key_id:str,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    row=db.scalar(select(AttendanceDeviceCredential).where(AttendanceDeviceCredential.tenant_id==member.tenant_id,AttendanceDeviceCredential.key_id==key_id))
    if not row: raise HTTPException(404,"Attendance device credential not found")
    row.active=False;audit(db,member,request,"hr.attendance_device_key_revoked","attendance_device_credential",key_id);db.commit()

@router.post("/attendance/device-events",status_code=202)
async def attendance_device_event(request:Request,x_tenant_id:str=Header(default="",alias="X-Tenant-ID"),x_device_key_id:str=Header(default="",alias="X-Device-Key-ID"),x_device_timestamp:str=Header(default="",alias="X-Device-Timestamp"),x_device_signature:str=Header(default="",alias="X-Device-Signature"),db:Session=Depends(get_db)):
    try:
        if abs(int(x_device_timestamp)-int(time.time()))>60: raise ValueError()
    except ValueError: raise HTTPException(401,"Device event timestamp is invalid or expired") from None
    try: tenant_id=uuid.UUID(x_tenant_id)
    except ValueError: raise HTTPException(400,"X-Tenant-ID must be a UUID") from None
    content_length=request.headers.get("content-length")
    if content_length:
        try:
            declared_length=int(content_length)
        except ValueError: raise HTTPException(400,"Content-Length is invalid") from None
        if declared_length<0: raise HTTPException(400,"Content-Length is invalid")
        if declared_length>65536: raise HTTPException(413,"Attendance device event is too large")
    body=bytearray()
    async for chunk in request.stream():
        if len(body)+len(chunk)>65536: raise HTTPException(413,"Attendance device event is too large")
        body.extend(chunk)
    raw=bytes(body)
    db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"),{"tenant_id":str(tenant_id)})
    credential=db.scalar(select(AttendanceDeviceCredential).where(AttendanceDeviceCredential.tenant_id==tenant_id,AttendanceDeviceCredential.key_id==x_device_key_id,AttendanceDeviceCredential.active.is_(True)))
    if not credential: raise HTTPException(401,"Attendance device credential is invalid or revoked")
    try: secret=device_fernet().decrypt(credential.secret_ciphertext.encode())
    except InvalidToken: raise HTTPException(503,"Attendance device credential cannot be decrypted") from None
    expected=hmac.new(secret,x_device_timestamp.encode()+b"."+str(tenant_id).encode()+b"."+raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,x_device_signature): raise HTTPException(401,"Device signature is invalid")
    try: payload=json.loads(raw);payload_tenant_id=uuid.UUID(payload["tenant_id"]);event_id=str(payload["event_id"]);employee_no=str(payload["employee_no"]);event_time=datetime.fromisoformat(payload["timestamp"]);kind=payload["event"]
    except (KeyError,ValueError,TypeError): raise HTTPException(422,"Device event payload is invalid") from None
    if payload_tenant_id!=tenant_id: raise HTTPException(403,"Device payload workspace does not match its credential")
    if not event_id.strip() or len(event_id)>160 or kind not in {"check_in","check_out"} or event_time.tzinfo is None: raise HTTPException(422,"Device event fields are invalid")
    accepted_event=db.scalar(pg_insert(AttendanceDeviceEvent).values(tenant_id=tenant_id,provider_event_id=event_id).on_conflict_do_nothing(index_elements=[AttendanceDeviceEvent.tenant_id,AttendanceDeviceEvent.provider_event_id]).returning(AttendanceDeviceEvent.id))
    if accepted_event is None: return {"status":"duplicate"}
    employee=db.scalar(select(Employee).where(Employee.tenant_id==tenant_id,Employee.employee_no==employee_no,Employee.status=="active"))
    if not employee: raise HTTPException(404,"Active employee not found")
    tenant=db.get(Tenant,tenant_id)
    try: work_date=event_time.astimezone(ZoneInfo(tenant.timezone if tenant else "UTC")).date()
    except ZoneInfoNotFoundError: work_date=event_time.astimezone(timezone.utc).date()
    row=db.scalar(select(Attendance).where(Attendance.tenant_id==tenant_id,Attendance.employee_id==employee.id,Attendance.work_date==work_date))
    if row is None: row=Attendance(tenant_id=tenant_id,employee_id=employee.id,work_date=work_date,source="device");db.add(row)
    if kind=="check_in" and (row.check_in is None or event_time<row.check_in): row.check_in=event_time
    if kind=="check_out" and (row.check_out is None or event_time>row.check_out): row.check_out=event_time
    if row.check_in and row.check_out and row.check_out<row.check_in: raise HTTPException(409,"Device event conflicts with the recorded check-in")
    row.source="device";row.status="pending"
    db.add(AuditEvent(tenant_id=tenant_id,actor=f"device:{event_id}",action="hr.attendance_device_event",entity="attendance",entity_id=str(row.id),detail={"event":kind,"employee_no":employee_no},request_id=request.state.request_id));db.commit()
    return {"status":"accepted","attendance_id":str(row.id)}

@router.post("/attendance/{attendance_id}/review")
def review_attendance(attendance_id:uuid.UUID,body:ReviewDecision,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    row=db.scalar(select(Attendance).where(Attendance.id==attendance_id,Attendance.tenant_id==member.tenant_id))
    if not row: raise HTTPException(404,"Attendance record not found")
    employee=db.get(Employee,row.employee_id)
    if employee and employee.subject==member.subject: raise HTTPException(403,"You cannot review your own attendance")
    if row.status!="pending": raise HTTPException(409,"Only pending attendance can be reviewed")
    row.status=body.status;row.reviewed_by=member.subject;audit(db,member,request,f"hr.attendance_{body.status}","attendance",str(row.id));db.commit()
    return serialize_attendance(row,employee.name if employee else "")

@router.get("/leaves")
def leaves(db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    rows=db.scalars(select(LeaveRequest).where(LeaveRequest.tenant_id==member.tenant_id).order_by(LeaveRequest.start_date.desc()))
    if member.role not in MANAGERS:
        employee=current_employee(db,member);rows=[row for row in rows if row.employee_id==employee.id]
    return [serialize_leave(row,db.get(Employee,row.employee_id).name) for row in rows]

@router.post("/leaves",status_code=201)
def create_leave(body:LeaveCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    employee=current_employee(db,member) if member.role not in MANAGERS and not body.employee_id else get_employee(db,member,parse_uuid(body.employee_id,"Employee ID")) if body.employee_id else None
    if employee is None: raise HTTPException(422,"Select an employee")
    if body.end_date<body.start_date: raise HTTPException(422,"Leave end must not precede its start")
    overlap=db.scalar(select(LeaveRequest.id).where(LeaveRequest.tenant_id==member.tenant_id,LeaveRequest.employee_id==employee.id,LeaveRequest.status.in_(["pending","approved"]),LeaveRequest.start_date<=body.end_date,LeaveRequest.end_date>=body.start_date))
    if overlap: raise HTTPException(409,"Leave dates overlap an existing request")
    row=LeaveRequest(tenant_id=member.tenant_id,employee_id=employee.id,start_date=body.start_date,end_date=body.end_date,reason=body.reason);db.add(row);db.flush();audit(db,member,request,"hr.leave_requested","leave",str(row.id));db.commit()
    return serialize_leave(row,employee.name)

@router.post("/leaves/{leave_id}/review")
def review_leave(leave_id:uuid.UUID,body:ReviewDecision,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    row=db.scalar(select(LeaveRequest).where(LeaveRequest.id==leave_id,LeaveRequest.tenant_id==member.tenant_id))
    if not row: raise HTTPException(404,"Leave request not found")
    employee=db.get(Employee,row.employee_id)
    if employee and employee.subject==member.subject: raise HTTPException(403,"You cannot review your own leave request")
    if row.status!="pending": raise HTTPException(409,"Only pending leave can be reviewed")
    if body.status=="approved":
        overlap=db.scalar(select(LeaveRequest.id).where(LeaveRequest.tenant_id==member.tenant_id,LeaveRequest.employee_id==row.employee_id,LeaveRequest.id!=row.id,LeaveRequest.status=="approved",LeaveRequest.start_date<=row.end_date,LeaveRequest.end_date>=row.start_date))
        if overlap: raise HTTPException(409,"Approved leave already covers part of this period")
    row.status=body.status;row.reviewed_by=member.subject;audit(db,member,request,f"hr.leave_{body.status}","leave",str(row.id));db.commit()
    return serialize_leave(row,employee.name if employee else "")

@router.put("/employees/{employee_id}/compensation")
def set_compensation(employee_id:uuid.UUID,body:CompensationCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    employee=get_employee(db,member,employee_id)
    if any(value<0 for value in [*body.allowances.values(),*body.deductions.values()]): raise HTTPException(422,"Salary components cannot be negative")
    row=db.scalar(select(Compensation).where(Compensation.tenant_id==member.tenant_id,Compensation.employee_id==employee.id,Compensation.effective_from==body.effective_from))
    if row is None: row=Compensation(tenant_id=member.tenant_id,employee_id=employee.id,effective_from=body.effective_from,base_monthly=body.base_monthly);db.add(row)
    row.base_monthly=body.base_monthly;row.allowances={k:str(v) for k,v in body.allowances.items()};row.deductions={k:str(v) for k,v in body.deductions.items()}
    audit(db,member,request,"hr.compensation_updated","employee",str(employee.id),{"effective_from":body.effective_from.isoformat()});db.commit()
    return {"employee_id":str(employee.id),"effective_from":body.effective_from.isoformat(),"base_monthly":str(row.base_monthly),"allowances":row.allowances,"deductions":row.deductions}

@router.get("/employees/{employee_id}/compensation")
def compensation_history(employee_id:uuid.UUID,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    employee=get_employee(db,member,employee_id)
    rows=db.scalars(select(Compensation).where(Compensation.tenant_id==member.tenant_id,Compensation.employee_id==employee.id).order_by(Compensation.effective_from.desc()))
    return [{"id":str(row.id),"effective_from":row.effective_from.isoformat(),"base_monthly":str(row.base_monthly),"allowances":row.allowances,"deductions":row.deductions} for row in rows]

@router.post("/payroll/runs",status_code=201)
def create_payroll(body:PayrollRunCreate,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    if body.period_end<body.period_start: raise HTTPException(422,"Payroll period end must not precede its start")
    if body.period_start.day!=1 or (body.period_end.year,body.period_end.month)!=(body.period_start.year,body.period_start.month): raise HTTPException(422,"Payroll periods must cover one complete calendar month")
    import calendar
    if body.period_end.day!=calendar.monthrange(body.period_end.year,body.period_end.month)[1]: raise HTTPException(422,"Payroll periods must end on the last day of the month")
    if db.scalar(select(PayrollRun.id).where(PayrollRun.tenant_id==member.tenant_id,PayrollRun.period_start<=body.period_end,PayrollRun.period_end>=body.period_start)): raise HTTPException(409,"A payroll run already exists for an overlapping period")
    run=PayrollRun(tenant_id=member.tenant_id,period_start=body.period_start,period_end=body.period_end,created_by=member.subject);db.add(run);db.flush()
    active_employees=list(db.scalars(select(Employee).where(Employee.tenant_id==member.tenant_id,Employee.status=="active",Employee.hire_date<=body.period_end)))
    if not active_employees: raise HTTPException(409,"No active employees are eligible for this payroll period")
    missing=[]
    for employee in active_employees:
        compensation_rows=list(db.scalars(select(Compensation).where(Compensation.tenant_id==member.tenant_id,Compensation.employee_id==employee.id,Compensation.effective_from<=body.period_end).order_by(Compensation.effective_from)))
        bands=[{"effective_from":row.effective_from,"base_monthly":row.base_monthly,"allowances":row.allowances,"deductions":row.deductions} for row in compensation_rows]
        try:
            calculated=calculate_period_pay(body.period_start,body.period_end,employee.hire_date,bands)
        except ValueError as error:
            if "No effective compensation" in str(error):
                missing.append(employee.employee_no)
                continue
            raise HTTPException(422,f"Payroll calculation failed for employee {employee.employee_no}: {error}") from None
        detail={"allowances":{key:str(value) for key,value in calculated["allowances"].items()},"deductions":{key:str(value) for key,value in calculated["deductions"].items()},"calculation":"effective monthly components prorated by eligible calendar days in this payroll period","proration_days":calculated["proration_days"],"period_days":calculated["period_days"],"segments":calculated["segments"]}
        db.add(Payslip(tenant_id=member.tenant_id,run_id=run.id,employee_id=employee.id,base_monthly=calculated["base"],allowance_total=calculated["allowance_total"],deduction_total=calculated["deduction_total"],net_pay=calculated["net"],detail=detail))
    if missing: raise HTTPException(409,"Set effective compensation before preparing payroll for employees: "+", ".join(missing[:25]))
    audit(db,member,request,"hr.payroll_draft_created","payroll_run",str(run.id),{"period_start":body.period_start.isoformat(),"period_end":body.period_end.isoformat()});db.commit()
    return {"id":str(run.id),"period_start":run.period_start.isoformat(),"period_end":run.period_end.isoformat(),"status":run.status,"payslip_count":db.query(Payslip).filter_by(tenant_id=member.tenant_id,run_id=run.id).count(),"calculation_note":"Effective monthly components are prorated by eligible calendar days, including mid-period hire and salary changes. Statutory tax, benefits, unpaid leave and payroll execution are not applied."}

@router.get("/payroll/runs")
def payroll_runs(db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    rows=db.scalars(select(PayrollRun).where(PayrollRun.tenant_id==member.tenant_id).order_by(PayrollRun.period_start.desc()))
    return [{"id":str(x.id),"period_start":x.period_start.isoformat(),"period_end":x.period_end.isoformat(),"status":x.status,"payslip_count":db.query(Payslip).filter_by(tenant_id=member.tenant_id,run_id=x.id).count()} for x in rows]

@router.post("/payroll/runs/{run_id}/approve")
def approve_payroll(run_id:uuid.UUID,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    row=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.tenant_id==member.tenant_id))
    if not row: raise HTTPException(404,"Payroll run not found")
    if row.created_by==member.subject: raise HTTPException(403,"The payroll preparer cannot approve their own run")
    if row.status!="draft": raise HTTPException(409,"Only draft payroll runs can be approved")
    row.status="approved";row.approved_by=member.subject;audit(db,member,request,"hr.payroll_approved","payroll_run",str(row.id));db.commit()
    return {"id":str(row.id),"status":row.status}

@router.get("/payroll/runs/{run_id}/payslips")
def payroll_draft_slips(run_id:uuid.UUID,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    run=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.tenant_id==member.tenant_id))
    if not run: raise HTTPException(404,"Payroll run not found")
    rows=db.execute(select(Payslip,Employee).join(Employee,Employee.id==Payslip.employee_id).where(Payslip.tenant_id==member.tenant_id,Payslip.run_id==run.id).order_by(Employee.employee_no)).all()
    return [{"id":str(slip.id),"employee_no":employee.employee_no,"employee":employee.name,"base_monthly":str(slip.base_monthly),"allowances":slip.detail.get("allowances",{}),"deductions":slip.detail.get("deductions",{}),"allowance_total":str(slip.allowance_total),"deduction_total":str(slip.deduction_total),"net_pay":str(slip.net_pay),"calculation":slip.detail.get("calculation",""),"proration_days":slip.detail.get("proration_days"),"period_days":slip.detail.get("period_days"),"segments":slip.detail.get("segments",[]),"calculation_note":"Calendar-day proration applied. Statutory payroll rules and attendance-based deductions are not applied."} for slip,employee in rows]

@router.get("/payroll/runs/{run_id}/export.csv")
def export_payroll(run_id:uuid.UUID,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    run=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.tenant_id==member.tenant_id))
    if not run: raise HTTPException(404,"Payroll run not found")
    if run.status not in {"approved","released"}: raise HTTPException(409,"Approve the payroll run before exporting it")
    records=db.execute(select(Payslip,Employee).join(Employee,Employee.id==Payslip.employee_id).where(Payslip.tenant_id==member.tenant_id,Payslip.run_id==run.id).order_by(Employee.employee_no)).all()
    rows=[{"employee_no":employee.employee_no,"employee":employee.name,"period_start":run.period_start.isoformat(),"period_end":run.period_end.isoformat(),"base_pay":slip.base_monthly,"allowance_total":slip.allowance_total,"deduction_total":slip.deduction_total,"net_pay":slip.net_pay} for slip,employee in records]
    db.add(AuditEvent(tenant_id=member.tenant_id,actor=member.subject,action="hr.payroll_exported",entity="payroll_run",entity_id=str(run.id),detail={"count":len(rows),"format":"csv"},request_id=request.state.request_id));db.commit()
    return Response(content=payroll_csv(rows),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="nexora-payroll-{run.period_start.isoformat()}.csv"'})

@router.post("/payroll/runs/{run_id}/release")
def release_payroll(run_id:uuid.UUID,request:Request,db:Session=Depends(get_db),member:Membership=Depends(allow(*MANAGERS))):
    row=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.tenant_id==member.tenant_id))
    if not row: raise HTTPException(404,"Payroll run not found")
    if row.status!="approved": raise HTTPException(409,"Payroll must be approved before release")
    now=datetime.now(timezone.utc)
    for slip in db.scalars(select(Payslip).where(Payslip.tenant_id==member.tenant_id,Payslip.run_id==row.id)): slip.released_at=now
    row.status="released";audit(db,member,request,"hr.payroll_released","payroll_run",str(row.id));db.commit()
    return {"id":str(row.id),"status":row.status,"released_at":now.isoformat()}

@router.get("/payroll/payslips")
def payslips(db:Session=Depends(get_db),member:Membership=Depends(allow(*HR_USERS))):
    query=select(Payslip,PayrollRun,Employee).join(PayrollRun,PayrollRun.id==Payslip.run_id).join(Employee,Employee.id==Payslip.employee_id).where(Payslip.tenant_id==member.tenant_id,Payslip.released_at.is_not(None))
    if member.role not in MANAGERS: query=query.where(Employee.subject==member.subject)
    rows=db.execute(query.order_by(PayrollRun.period_start.desc())).all()
    return [{"id":str(slip.id),"employee":employee.name,"period_start":run.period_start.isoformat(),"period_end":run.period_end.isoformat(),"base_monthly":str(slip.base_monthly),"allowances":slip.detail.get("allowances",{}),"deductions":slip.detail.get("deductions",{}),"allowance_total":str(slip.allowance_total),"deduction_total":str(slip.deduction_total),"net_pay":str(slip.net_pay),"calculation":slip.detail.get("calculation",""),"proration_days":slip.detail.get("proration_days"),"period_days":slip.detail.get("period_days") } for slip,run,employee in rows]
