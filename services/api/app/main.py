import hashlib, os, re, secrets, uuid
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from .db import Base, engine, get_db
from .models import ApiClientCredential, AuditEvent, Branch, BusinessRecord, IdempotencyKey, Invitation, Membership, Tenant, UserPreference, WorkspaceResource
from .schemas import BranchCreate, BudgetSpend, CompanyProfileUpdate, DeliveryCommand, InventoryAdjustment, ManualPaymentMatch, MemberInvite, MemberUpdate, RecordCreate, RecordUpdate, StatusCommand, UserPreferencesUpdate, WorkspaceCreate
from .security import allow, identity, membership
from .odoo import gateway_command, install_tenant_database
from .budget import add_budget_spend, budget_totals
from .hr import router as hr_router
from .extended import router as extended_router

app = FastAPI(title="Nexora One API", version="0.1.0", openapi_url="/api/v1/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")], allow_credentials=True, allow_methods=["GET","POST","PUT","PATCH","DELETE"], allow_headers=["Authorization","Content-Type","X-Tenant-ID","Idempotency-Key","If-Match","X-Device-Key-ID","X-Device-Timestamp","X-Device-Signature"])
ROLES = {"Owner", "Admin", "Finance manager", "HR manager", "Employee", "Sales", "Purchasing", "Warehouse", "Staff"}
WRITE_ROLES = {"Owner", "Admin"}
KIND_ROLES = {"leads":{"Owner","Admin","Sales"}, "customers":{"Owner","Admin","Sales","Finance manager"}, "suppliers":{"Owner","Admin","Purchasing","Finance manager"}, "sales":{"Owner","Admin","Sales"}, "purchasing":{"Owner","Admin","Purchasing"}, "inventory":{"Owner","Admin","Warehouse","Purchasing","Sales","Finance manager"}, "finance":{"Owner","Admin","Finance manager"}, "payments":{"Owner","Admin","Finance manager"}, "budgets":{"Owner","Admin","Finance manager"}, "approvals":{"Owner","Admin","Finance manager","Purchasing","Sales"}}
RECORD_WRITE_ROLES = {"leads":{"Owner","Admin","Sales"},"customers":{"Owner","Admin","Sales","Finance manager"},"suppliers":{"Owner","Admin","Purchasing","Finance manager"},"sales":{"Owner","Admin","Sales"},"purchasing":{"Owner","Admin","Purchasing"},"inventory":{"Owner","Admin","Warehouse","Purchasing"},"finance":{"Owner","Admin","Finance manager"},"payments":{"Owner","Admin","Finance manager"},"budgets":{"Owner","Admin","Finance manager"},"approvals":{"Owner","Admin","Finance manager","Purchasing","Sales"}}
app.include_router(hr_router)
app.include_router(extended_router)

@app.on_event("startup")
def startup():
    command.upgrade(Config("alembic.ini"), "head")

def audit(db: Session, member: Membership, request: Request, action: str, entity: str, entity_id: str = "", detail: dict | None = None):
    db.add(AuditEvent(tenant_id=member.tenant_id, actor=member.subject, action=action, entity=entity, entity_id=entity_id, detail=detail or {}, request_id=request.state.request_id))

def request_hash(value: dict) -> str:
    import json
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def require_idempotency_key(key: str | None) -> str:
    if not key or not key.strip(): raise HTTPException(400,"Idempotency-Key is required")
    if len(key)>200: raise HTTPException(400,"Idempotency-Key must be 200 characters or fewer")
    return key

def deliver_invitation(invite: Invitation, token: str) -> bool:
    message=EmailMessage();message["Subject"]="You are invited to Nexora One";message["From"]=os.getenv("MAIL_FROM","noreply@nexora.local");message["To"]=invite.email
    url=f"{os.getenv('PUBLIC_WEB_URL','http://localhost:3000')}/?invite={token}"
    message.set_content(f"You have been invited to a Nexora One workspace as {invite.role}.\n\nAccept your invitation within 7 days: {url}\n")
    try:
        with smtplib.SMTP(os.getenv("SMTP_HOST","mailpit"),int(os.getenv("SMTP_PORT","1025")),timeout=5) as smtp: smtp.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        return False

def numeric(value) -> float:
    if value in (None, ""): return 0.0
    try: return float(str(value).replace(",", ""))
    except ValueError: raise HTTPException(422,"Amounts and quantities must be numeric") from None

def normalize_budget_payload(payload:dict,spent:Decimal=Decimal("0"),entries:list|None=None)->dict:
    try: totals=budget_totals(payload.get("limit",payload.get("amount")),spent)
    except ValueError as error: raise HTTPException(422,str(error)) from None
    return {**payload,"limit":str(totals["limit"]),"spent":str(totals["spent"]),"remaining":str(totals["remaining"]),"over_budget":totals["over_budget"],"entries":entries or []}

def validate_related_records(db: Session, member: Membership, kind: str, payload: dict) -> None:
    related=[]
    if kind=="sales": related=[("customers",payload.get("partner_id"))]
    elif kind=="purchasing": related=[("suppliers",payload.get("partner_id"))]
    elif kind=="finance": related=[("customers" if payload.get("move_type")=="out_invoice" else "suppliers",payload.get("partner_id"))]
    if kind in {"sales","purchasing","finance"}: related.append(("inventory",payload.get("product_id")))
    for related_kind, odoo_id in related:
        if not odoo_id: raise HTTPException(422,"Select a linked contact and product from this workspace")
        candidates=db.scalars(select(BusinessRecord).where(BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind==related_kind))
        linked=next((record for record in candidates if str(record.payload.get("odoo_id"))==str(odoo_id)),None)
        if not linked: raise HTTPException(422,"Related record is not registered in this workspace")
        if member.role not in {"Owner","Admin"} and linked.payload.get("branch_id") not in member.branch_ids: raise HTTPException(403,"Related record is outside your assigned branches")
        if linked.payload.get("branch_id")!=payload.get("branch_id") and member.role not in {"Owner","Admin"}: raise HTTPException(403,"Related records must use the same branch")

@app.middleware("http")
async def request_id(request: Request, call_next):
    supplied_id=request.headers.get("x-request-id","")
    request.state.request_id=supplied_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,80}",supplied_id) else str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

@app.get("/healthz")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status":"ok"}

@app.get("/api/v1/me/workspaces")
def my_workspaces(user: dict = Depends(identity), db: Session = Depends(get_db)):
    rows = db.execute(select(Membership, Tenant).join(Tenant, Membership.tenant_id == Tenant.id).where(Membership.subject == user["sub"], Membership.active.is_(True))).all()
    return [{"id":str(m.tenant_id),"name":t.name,"industry":t.industry,"role":m.role,"branch_ids":m.branch_ids,"status":t.status,"odoo_connected":bool(t.odoo_database)} for m,t in rows]

@app.post("/api/v1/workspaces", status_code=201)
def create_workspace(body: WorkspaceCreate, request: Request, user: dict = Depends(identity), db: Session = Depends(get_db)):
    if user.get("email_verified") is not True:
        raise HTTPException(403, "Verify your email before creating a workspace")
    slug = re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-")[:70] or "workspace"
    tenant = Tenant(name=body.name, slug=f"{slug}-{secrets.token_hex(4)}", industry=body.industry, status="provisioning")
    db.add(tenant); db.flush()
    db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id":str(tenant.id)})
    member = Membership(tenant_id=tenant.id, subject=user["sub"], email=user.get("email", ""), display_name=user.get("name") or user.get("preferred_username") or user.get("email", "Owner"), role="Owner")
    db.add(member)
    local_demo=os.getenv("LOCAL_DEMO_MODE", "false").lower()=="true"
    database=f"nxo_{tenant.id.hex[:24]}"
    tenant.odoo_database=None if local_demo else database
    audit(db, member, request, "workspace.created", "tenant", str(tenant.id), {"name":tenant.name})
    db.commit()
    if local_demo:
        tenant.status="ready";db.commit()
        return {"id":str(tenant.id),"name":tenant.name,"industry":tenant.industry,"role":"Owner","status":"ready","odoo_connected":False}
    try:
        install_tenant_database(database,tenant.name)
        tenant.status="ready";db.commit()
    except HTTPException:
        tenant.status="provisioning_failed";db.commit()
        raise
    return {"id":str(tenant.id),"name":tenant.name,"industry":tenant.industry,"role":"Owner","status":tenant.status}

@app.post("/api/v1/workspaces/{tenant_id}/provision")
def retry_provision(tenant_id: uuid.UUID, request: Request, db: Session = Depends(get_db), member: Membership = Depends(allow("Owner"))):
    tenant=db.scalar(select(Tenant).where(Tenant.id==tenant_id))
    if not tenant or tenant.id!=member.tenant_id: raise HTTPException(404,"Workspace not found")
    if tenant.status=="ready": return {"status":"ready"}
    if tenant.status=="provisioning": raise HTTPException(409,"Provisioning is already running")
    tenant.status="provisioning";db.commit()
    try:
        install_tenant_database(tenant.odoo_database,tenant.name)
        tenant.status="ready"
        db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id":str(tenant.id)})
        audit(db,member,request,"workspace.provisioned","tenant",str(tenant.id));db.commit()
    except HTTPException:
        tenant.status="provisioning_failed";db.commit();raise
    return {"status":tenant.status}

@app.get("/api/v1/branches")
def list_branches(db: Session = Depends(get_db), member: Membership = Depends(membership)):
    return [{"id":str(x.id),"name":x.name,"city":x.city,"timezone":x.timezone,"active":x.active} for x in db.scalars(select(Branch).where(Branch.tenant_id==member.tenant_id).order_by(Branch.name))]

@app.get("/api/v1/company-profile")
def get_company_profile(db: Session = Depends(get_db), member: Membership = Depends(membership)):
    tenant=db.get(Tenant,member.tenant_id)
    if not tenant: raise HTTPException(404,"Workspace not found")
    return {"name":tenant.name,"industry":tenant.industry,"address":tenant.address,"currency":tenant.currency,"timezone":tenant.timezone}

@app.put("/api/v1/company-profile")
def update_company_profile(body: CompanyProfileUpdate, request: Request, db: Session = Depends(get_db), member: Membership = Depends(allow("Owner","Admin"))):
    tenant=db.get(Tenant,member.tenant_id)
    if not tenant: raise HTTPException(404,"Workspace not found")
    tenant.name=body.name;tenant.industry=body.industry;tenant.address=body.address;tenant.currency=body.currency;tenant.timezone=body.timezone
    audit(db,member,request,"workspace.profile_updated","tenant",str(tenant.id));db.commit()
    return {"name":tenant.name,"industry":tenant.industry,"address":tenant.address,"currency":tenant.currency,"timezone":tenant.timezone}

@app.get("/api/v1/me/preferences")
def get_preferences(db: Session = Depends(get_db), member: Membership = Depends(membership)):
    row=db.scalar(select(UserPreference).where(UserPreference.tenant_id==member.tenant_id,UserPreference.subject==member.subject))
    return {"theme":row.theme if row else "Ocean Light"}

@app.put("/api/v1/me/preferences")
def update_preferences(body: UserPreferencesUpdate, db: Session = Depends(get_db), member: Membership = Depends(membership)):
    row=db.scalar(select(UserPreference).where(UserPreference.tenant_id==member.tenant_id,UserPreference.subject==member.subject))
    if not row:
        row=UserPreference(tenant_id=member.tenant_id,subject=member.subject);db.add(row)
    row.theme=body.theme;db.commit()
    return {"theme":row.theme}

@app.post("/api/v1/branches", status_code=201)
def create_branch(body: BranchCreate, request: Request, db: Session = Depends(get_db), member: Membership = Depends(allow("Owner","Admin"))):
    branch=Branch(tenant_id=member.tenant_id,name=body.name,city=body.city,timezone=body.timezone);db.add(branch);db.flush();audit(db,member,request,"branch.created","branch",str(branch.id));db.commit()
    return {"id":str(branch.id),"name":branch.name,"city":branch.city,"timezone":branch.timezone,"active":branch.active}

@app.put("/api/v1/branches/{branch_id}")
def update_branch(branch_id: uuid.UUID, body: BranchCreate, request: Request, db: Session = Depends(get_db), member: Membership = Depends(allow("Owner","Admin"))):
    branch=db.scalar(select(Branch).where(Branch.id==branch_id,Branch.tenant_id==member.tenant_id))
    if not branch: raise HTTPException(404,"Branch not found")
    branch.name=body.name;branch.city=body.city;branch.timezone=body.timezone
    audit(db,member,request,"branch.updated","branch",str(branch.id));db.commit()
    return {"id":str(branch.id),"name":branch.name,"city":branch.city,"timezone":branch.timezone,"active":branch.active}

@app.delete("/api/v1/branches/{branch_id}", status_code=204)
def delete_branch(branch_id: uuid.UUID, request: Request, db: Session = Depends(get_db), member: Membership = Depends(allow("Owner","Admin"))):
    branch=db.scalar(select(Branch).where(Branch.id==branch_id,Branch.tenant_id==member.tenant_id))
    if not branch: raise HTTPException(404,"Branch not found")
    if db.scalar(select(Membership.id).where(Membership.tenant_id==member.tenant_id,Membership.branch_ids.contains([str(branch.id)]))): raise HTTPException(409,"Move members off this branch before removing it")
    audit(db,member,request,"branch.deleted","branch",str(branch.id));db.delete(branch);db.commit()

@app.get("/api/v1/members")
def list_members(db: Session = Depends(get_db), member: Membership = Depends(allow("Owner","Admin"))):
    members=[{"id":str(x.id),"email":x.email,"name":x.display_name,"role":x.role,"branch_ids":x.branch_ids,"active":x.active,"subject":x.subject} for x in db.scalars(select(Membership).where(Membership.tenant_id==member.tenant_id).order_by(Membership.email))]
    invites=db.scalars(select(Invitation).where(Invitation.tenant_id==member.tenant_id,Invitation.revoked.is_(False),Invitation.accepted_at.is_(None),Invitation.expires_at>datetime.now(timezone.utc)))
    members.extend({"id":str(i.id),"email":i.email,"name":i.display_name,"role":i.role,"branch_ids":i.branch_ids,"active":False,"pending":True} for i in invites)
    return members

@app.patch("/api/v1/members/{member_id}")
def update_member(member_id: uuid.UUID, body: MemberUpdate, request: Request, db: Session = Depends(get_db), actor: Membership = Depends(allow("Owner","Admin"))):
    target=db.scalar(select(Membership).where(Membership.id==member_id,Membership.tenant_id==actor.tenant_id))
    if not target: raise HTTPException(404,"Member not found")
    if target.role=="Owner" and actor.role!="Owner": raise HTTPException(403,"Only an owner can manage an owner membership")
    if target.role=="Owner" and (body.role not in (None,"Owner") or body.active is False):
        owners=db.scalar(select(Membership).where(Membership.tenant_id==actor.tenant_id,Membership.role=="Owner",Membership.active.is_(True)))
        if owners and owners.id==target.id and len(db.scalars(select(Membership.id).where(Membership.tenant_id==actor.tenant_id,Membership.role=="Owner",Membership.active.is_(True))).all())<=1:
            raise HTTPException(409,"The final active owner cannot be removed or demoted")
    access_changed=(body.role is not None and body.role!=target.role) or (body.active is not None and body.active!=target.active) or (body.branch_ids is not None and body.branch_ids!=target.branch_ids)
    if body.role is not None:
        if body.role not in ROLES: raise HTTPException(422,"Unsupported role")
        if actor.role!="Owner" and body.role=="Owner": raise HTTPException(403,"Only an owner can grant owner access")
        target.role=body.role
    if body.active is not None: target.active=body.active
    if body.branch_ids is not None:
        allowed={str(x) for x in db.scalars(select(Branch.id).where(Branch.tenant_id==actor.tenant_id)).all()}
        if not set(body.branch_ids).issubset(allowed): raise HTTPException(422,"Branch is outside this workspace")
        target.branch_ids=body.branch_ids
    if access_changed:
        db.query(ApiClientCredential).filter(ApiClientCredential.tenant_id==actor.tenant_id,ApiClientCredential.subject==target.subject,ApiClientCredential.revoked_at.is_(None)).update({ApiClientCredential.revoked_at:datetime.now(timezone.utc)},synchronize_session=False)
    audit(db,actor,request,"membership.updated","membership",str(target.id),{"role":target.role,"active":target.active,"api_credentials_revoked":access_changed});db.commit()
    return {"id":str(target.id),"role":target.role,"active":target.active,"branch_ids":target.branch_ids}

@app.delete("/api/v1/members/{member_id}", status_code=204)
def delete_member(member_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor: Membership = Depends(allow("Owner","Admin"))):
    target=db.scalar(select(Membership).where(Membership.id==member_id,Membership.tenant_id==actor.tenant_id))
    if not target: raise HTTPException(404,"Member not found")
    if target.role=="Owner" and actor.role!="Owner": raise HTTPException(403,"Only an owner can remove an owner membership")
    if target.role=="Owner" and target.active and len(db.scalars(select(Membership.id).where(Membership.tenant_id==actor.tenant_id,Membership.role=="Owner",Membership.active.is_(True))).all())<=1: raise HTTPException(409,"The final active owner cannot be removed")
    db.query(ApiClientCredential).filter(ApiClientCredential.tenant_id==actor.tenant_id,ApiClientCredential.subject==target.subject,ApiClientCredential.revoked_at.is_(None)).update({ApiClientCredential.revoked_at:datetime.now(timezone.utc)},synchronize_session=False)
    audit(db,actor,request,"membership.deleted","membership",str(target.id));db.delete(target);db.commit()

@app.post("/api/v1/invitations", status_code=201)
def create_invitation(body: MemberInvite, request: Request, db: Session = Depends(get_db), actor: Membership = Depends(allow("Owner","Admin"))):
    if body.role not in ROLES: raise HTTPException(422,"Unsupported role")
    if body.role=="Owner" and actor.role!="Owner": raise HTTPException(403,"Only an owner can invite another owner")
    existing=db.scalar(select(Invitation.id).where(Invitation.tenant_id==actor.tenant_id,Invitation.email==body.email.lower(),Invitation.revoked.is_(False),Invitation.accepted_at.is_(None),Invitation.expires_at>datetime.now(timezone.utc)))
    if existing: raise HTTPException(409,"An active invitation already exists for this email")
    allowed={str(x) for x in db.scalars(select(Branch.id).where(Branch.tenant_id==actor.tenant_id)).all()}
    if not set(body.branch_ids).issubset(allowed): raise HTTPException(422,"Branch is outside this workspace")
    token=secrets.token_urlsafe(32); invite=Invitation(tenant_id=actor.tenant_id,email=body.email.lower(),display_name=body.display_name,role=body.role,branch_ids=body.branch_ids,token_hash=hashlib.sha256(token.encode()).hexdigest(),expires_at=datetime.now(timezone.utc)+timedelta(days=7))
    db.add(invite);db.flush();audit(db,actor,request,"invitation.created","invitation",str(invite.id),{"email":invite.email,"role":invite.role});db.commit()
    delivered=deliver_invitation(invite,token)
    return {"id":str(invite.id),"email":invite.email,"role":invite.role,"expires_at":invite.expires_at,"delivery":"sent" if delivered else "failed; retry required"}

@app.post("/api/v1/invitations/{invitation_id}/resend")
def resend_invitation(invitation_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor: Membership = Depends(allow("Owner","Admin"))):
    invite=db.scalar(select(Invitation).where(Invitation.id==invitation_id,Invitation.tenant_id==actor.tenant_id,Invitation.revoked.is_(False),Invitation.accepted_at.is_(None)))
    if not invite: raise HTTPException(404,"Pending invitation not found")
    token=secrets.token_urlsafe(32)
    invite.token_hash=hashlib.sha256(token.encode()).hexdigest()
    invite.expires_at=datetime.now(timezone.utc)+timedelta(days=7)
    audit(db,actor,request,"invitation.resent","invitation",str(invite.id),{"email":invite.email});db.commit()
    delivered=deliver_invitation(invite,token)
    return {"id":str(invite.id),"delivery":"sent" if delivered else "failed; retry required"}

@app.delete("/api/v1/invitations/{invitation_id}", status_code=204)
def revoke_invitation(invitation_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor: Membership = Depends(allow("Owner","Admin"))):
    invite=db.scalar(select(Invitation).where(Invitation.id==invitation_id,Invitation.tenant_id==actor.tenant_id,Invitation.accepted_at.is_(None)))
    if not invite: raise HTTPException(404,"Invitation not found")
    invite.revoked=True;audit(db,actor,request,"invitation.revoked","invitation",str(invite.id));db.commit()

@app.post("/api/v1/invitations/accept")
def accept_invitation(payload: dict, request: Request, user: dict = Depends(identity), db: Session = Depends(get_db)):
    raw=payload.get("token","");token_hash=hashlib.sha256(raw.encode()).hexdigest()
    db.execute(text("SELECT set_config('app.invitation_hash', :token_hash, true)"), {"token_hash":token_hash})
    invite=db.scalar(select(Invitation).where(Invitation.token_hash==token_hash,Invitation.revoked.is_(False),Invitation.accepted_at.is_(None)))
    if not invite or invite.expires_at < datetime.now(timezone.utc): raise HTTPException(400,"Invitation is invalid or expired")
    if (user.get("email") or "").lower()!=invite.email or user.get("email_verified") is not True: raise HTTPException(403,"Sign in with the verified invited email")
    db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id":str(invite.tenant_id)})
    member=Membership(tenant_id=invite.tenant_id,subject=user["sub"],email=invite.email,display_name=invite.display_name,role=invite.role,branch_ids=invite.branch_ids);invite.accepted_at=datetime.now(timezone.utc);db.add(member);audit(db,member,request,"invitation.accepted","invitation",str(invite.id));db.commit()
    return {"tenant_id":str(member.tenant_id),"role":member.role}

@app.get("/api/v1/roles")
def roles(member: Membership = Depends(membership)):
    return [{"name":name,"permissions":sorted(perms)} for name,perms in {"Owner":set(KIND_ROLES)|{"hr"},"Admin":set(KIND_ROLES)|{"hr"},"HR manager":{"hr"},"Employee":{"self_service"},"Sales":{"leads","customers","sales"},"Purchasing":{"suppliers","purchasing","inventory"},"Warehouse":{"inventory"},"Finance manager":{"customers","suppliers","finance","payments","budgets","approvals"},"Staff":set()}.items()]

@app.get("/api/v1/records/{kind}")
def list_records(kind: str, db: Session = Depends(get_db), member: Membership = Depends(membership)):
    if kind not in KIND_ROLES: raise HTTPException(404,"Unknown record type")
    if member.role not in KIND_ROLES[kind]: raise HTTPException(403,"Insufficient permission")
    if member.role not in {"Owner","Admin"} and not member.branch_ids: raise HTTPException(403,"Assign at least one branch to this membership")
    rows=db.scalars(select(BusinessRecord).where(BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind==kind).order_by(BusinessRecord.created_at.desc()))
    scoped=[r for r in rows if member.role in {"Owner","Admin"} or r.payload.get("branch_id") in member.branch_ids]
    if kind in {"budgets","approvals","payments"}: return [{"id":str(r.id),"version":r.version,**r.payload} for r in scoped]
    tenant=db.get(Tenant,member.tenant_id)
    if os.getenv("LOCAL_DEMO_MODE", "false").lower()=="true" and (not tenant or tenant.status!="ready" or not tenant.odoo_database):
        return [{"id":str(r.id),"version":r.version,**r.payload} for r in scoped]
    if not tenant or tenant.status!="ready" or not tenant.odoo_database: raise HTTPException(503,"This workspace Odoo database is not ready")
    external=gateway_command(tenant.odoo_database,{"operation":"records.list","payload":{"kind":kind,"ids":[r.payload.get("odoo_id") for r in scoped if r.payload.get("odoo_id")]}},f"list-{uuid.uuid4()}").get("records",[])
    indexed={int(item["odoo_id"]):item for item in external}
    result=[]
    for record in scoped:
        remote=indexed.get(int(record.payload.get("odoo_id",0)))
        if not remote: continue
        payload=dict(record.payload)
        if kind=="leads": payload.update({"lead":remote.get("name",""),"contact":remote.get("contact_name",""),"email":remote.get("email_from",""),"phone":remote.get("phone",""),"stage":(remote.get("stage_id") or [0,"New"])[1],"value":remote.get("expected_revenue",0),"status":(remote.get("stage_id") or [0,"New"])[1].lower()})
        elif kind in {"customers","suppliers"}: payload.update({"customer" if kind=="customers" else "supplier":remote.get("name",""),"email":remote.get("email",""),"phone":remote.get("phone",""),"odoo_id":remote["odoo_id"]})
        elif kind=="sales": payload.update({"document":remote.get("name",""),"customer":(remote.get("partner_id") or [0,""])[1],"status":"invoiced" if payload.get("status")=="invoiced" else {"draft":"draft","sent":"approved","sale":"confirmed","done":"posted","cancel":"cancelled"}.get(remote.get("state"),"draft"),"total":remote.get("amount_total",0)})
        elif kind=="purchasing": payload.update({"purchase_order":remote.get("name",""),"supplier":(remote.get("partner_id") or [0,""])[1],"status":"billed" if payload.get("status")=="billed" else {"draft":"draft","sent":"pending","to approve":"pending","purchase":"confirmed","done":"received","cancel":"cancelled"}.get(remote.get("state"),"draft"),"total":remote.get("amount_total",0)})
        elif kind=="inventory": payload.update({"product":remote.get("name",""),"sku":remote.get("default_code") or "","on_hand":remote.get("qty_available",0),"reorder_at":payload.get("reorder_at",0),"odoo_id":remote["odoo_id"]})
        elif kind=="finance": payload.update({"document":remote.get("name",""),"party":(remote.get("partner_id") or [0,""])[1],"due_date":remote.get("invoice_date_due") or "","currency":(remote.get("currency_id") or [0,""])[1],"status":{"draft":"draft","posted":"posted","cancel":"cancelled"}.get(remote.get("state"),"draft"),"total":remote.get("amount_total",0)})
        result.append({"id":str(record.id),"version":record.version,**payload})
    return result

@app.post("/api/v1/records", status_code=201)
def create_record(body: RecordCreate, request: Request, db: Session = Depends(get_db), member: Membership = Depends(membership), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    if member.role not in RECORD_WRITE_ROLES[body.kind]: raise HTTPException(403,"Insufficient permission")
    if member.role not in {"Owner","Admin"} and (not member.branch_ids or body.payload.get("branch_id") not in member.branch_ids): raise HTTPException(403,"Record must belong to an assigned branch")
    if idempotency_key:
        prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
        if prior:
            if prior.request_hash!=request_hash({"kind":body.kind,"payload":body.payload}): raise HTTPException(409,"Idempotency key was already used for a different request")
            return prior.result
    payload=dict(body.payload)
    try: branch_uuid=uuid.UUID(payload.get("branch_id", ""))
    except ValueError: raise HTTPException(422,"Choose a branch in this workspace") from None
    if not db.scalar(select(Branch.id).where(Branch.id==branch_uuid,Branch.tenant_id==member.tenant_id)): raise HTTPException(422,"Choose a branch in this workspace")
    if member.role not in {"Owner","Admin"} and str(branch_uuid) not in member.branch_ids: raise HTTPException(403,"Branch is outside your assigned scope")
    if body.kind=="payments":
        try: payment_amount=Decimal(str(payload.get("amount")))
        except (InvalidOperation,ValueError): raise HTTPException(422,"Payment amount must be numeric") from None
        currency=str(payload.get("currency") or "")
        if not payment_amount.is_finite() or payment_amount<=0 or not payload.get("reference") or len(currency)!=3 or not currency.isalpha() or currency.upper()!=currency: raise HTTPException(422,"Payment reference, positive amount and uppercase ISO currency are required")
        payload["amount"]=str(payment_amount.quantize(Decimal("0.01")))
    if body.kind=="budgets": payload=normalize_budget_payload(payload)
    validate_related_records(db,member,body.kind,payload)
    odoo_id=None;odoo_name=None;amount=None
    operation={"leads":"lead.create","customers":"customer.create","suppliers":"supplier.create","inventory":"product.create","sales":"sale.quote.create","purchasing":"purchase.order.create","finance":"invoice.create"}.get(body.kind)
    if operation:
        tenant=db.get(Tenant,member.tenant_id)
        if not tenant or tenant.status!="ready" or not tenant.odoo_database: raise HTTPException(503,"This workspace Odoo database is not ready")
        command_payload=dict(payload)
        if body.kind=="leads": command_payload.update({"name":payload.get("lead"),"contact_name":payload.get("contact"),"expected_revenue":numeric(payload.get("value"))})
        elif body.kind=="customers": command_payload["name"]=payload.get("customer")
        elif body.kind=="suppliers": command_payload["name"]=payload.get("supplier")
        elif body.kind=="inventory": command_payload.update({"name":payload.get("product"),"sku":payload.get("sku"),"sale_price":numeric(payload.get("sale_price")),"cost":numeric(payload.get("cost"))})
        if body.kind in {"sales","purchasing","finance"}:
            if not command_payload.get("partner_id") or not command_payload.get("product_id"): raise HTTPException(422,"Choose a linked customer/supplier and product")
            line={"product_id":int(command_payload["product_id"]),"quantity":numeric(command_payload.get("quantity") or 1),"unit_price":numeric(command_payload.get("unit_price") or 0),"description":command_payload.get("description") or command_payload.get("product") or ""}
            command_payload["lines"]=[line]
            if body.kind=="sales": command_payload["reference"]=payload.get("document")
            elif body.kind=="purchasing": command_payload["reference"]=payload.get("purchase_order")
            if body.kind=="finance" and command_payload.get("move_type") not in {"in_invoice","out_invoice"}: raise HTTPException(422,"Select supplier bill or customer invoice")
        external_result=gateway_command(tenant.odoo_database,{"operation":operation,"payload":command_payload},idempotency_key or f"record-{uuid.uuid4()}")
        odoo_id=external_result.get("id");odoo_name=external_result.get("name");amount=external_result.get("amount_total")
        payload["odoo_id"]=odoo_id;payload["odoo_name"]=odoo_name
        if amount is not None: payload["total"]=amount
        if external_result.get("currency"): payload["currency"]=external_result["currency"]
    initial_status={"leads":"new","customers":"active","suppliers":"active","sales":"draft","purchasing":"draft","inventory":"active","finance":"draft","payments":"unmatched","budgets":"draft","approvals":"pending"}[body.kind]
    if body.kind=="leads": initial_status=str(payload.get("stage","new")).lower()
    payload["status"]=initial_status
    record=BusinessRecord(tenant_id=member.tenant_id,kind=body.kind,payload=payload,created_by=member.subject);db.add(record);db.flush()
    result={"id":str(record.id),"version":record.version,**record.payload}
    audit(db,member,request,f"{body.kind}.created",body.kind,str(record.id))
    if idempotency_key: db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash({"kind":body.kind,"payload":body.payload}),result=result))
    db.commit();return result

@app.put("/api/v1/records/{record_id}")
def update_record(record_id: uuid.UUID, body: RecordUpdate, request: Request, db: Session = Depends(get_db), member: Membership = Depends(membership), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    row=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id).with_for_update())
    if not row: raise HTTPException(404,"Record not found")
    if member.role not in RECORD_WRITE_ROLES[row.kind]: raise HTTPException(403,"Insufficient permission")
    if member.role not in {"Owner","Admin"} and row.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Record not found")
    command_value={"record_id":str(row.id),"payload":body.payload}
    if idempotency_key:
        prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
        if prior:
            if prior.request_hash!=request_hash(command_value): raise HTTPException(409,"Idempotency key was already used for a different request")
            return prior.result
    if row.version!=body.version: raise HTTPException(409,"Record changed; reload before editing")
    if row.payload.get("status") in {"posted","paid","cancelled"}: raise HTTPException(409,"Posted or closed documents cannot be edited")
    payload=dict(body.payload)
    if row.kind=="payments":
        if row.payload.get("status")!="unmatched": raise HTTPException(409,"Matched or exception payments cannot be edited")
        try: amount=Decimal(str(payload.get("amount",row.payload.get("amount"))))
        except (InvalidOperation,ValueError): raise HTTPException(422,"Payment amount must be numeric") from None
        currency=str(payload.get("currency",row.payload.get("currency","")))
        if not amount.is_finite() or amount<=0 or not (payload.get("reference") or row.payload.get("reference")) or len(currency)!=3 or not currency.isalpha() or currency.upper()!=currency: raise HTTPException(422,"Payment reference, positive amount and uppercase ISO currency are required")
        payload["amount"]=str(amount.quantize(Decimal("0.01")))
    if row.kind=="budgets":
        for protected in ("spent","remaining","over_budget","entries"): payload.pop(protected,None)
        try: prior_spent=Decimal(str(row.payload.get("spent",0)))
        except (InvalidOperation,ValueError): raise HTTPException(409,"Stored budget spend is invalid") from None
        payload=normalize_budget_payload({**row.payload,**payload},prior_spent,list(row.payload.get("entries",[])))
    for protected in ("odoo_id","odoo_name","created_by"):
        payload.pop(protected,None)
    if "branch_id" in payload:
        try: branch_uuid=uuid.UUID(payload["branch_id"])
        except ValueError: raise HTTPException(422,"Choose a branch in this workspace") from None
        if not db.scalar(select(Branch.id).where(Branch.id==branch_uuid,Branch.tenant_id==member.tenant_id)): raise HTTPException(422,"Choose a branch in this workspace")
        if member.role not in {"Owner","Admin"} and str(branch_uuid) not in member.branch_ids: raise HTTPException(403,"Branch is outside your assigned scope")
    payload_for_validation={**row.payload,**payload}
    validate_related_records(db,member,row.kind,payload_for_validation)
    if row.kind in {"leads","customers","suppliers","inventory","sales","purchasing","finance"}:
        if not idempotency_key: raise HTTPException(400,"Idempotency-Key is required")
        tenant=db.get(Tenant,member.tenant_id)
        if not tenant or tenant.status!="ready" or not tenant.odoo_database: raise HTTPException(503,"This workspace Odoo database is not ready")
        payload["status"]=row.payload.get("status","draft")
        if not row.payload.get("odoo_id"): raise HTTPException(409,"The Odoo document link is missing")
        gateway_command(tenant.odoo_database,{"operation":"record.update","payload":{"kind":row.kind,"odoo_id":row.payload["odoo_id"],"record":payload_for_validation}},idempotency_key)
    payload={**row.payload,**payload,"status":row.payload.get("status","draft")}
    row.payload=payload;row.version+=1
    result={"id":str(row.id),"version":row.version,**row.payload}
    audit(db,member,request,f"{row.kind}.updated",row.kind,str(row.id))
    if idempotency_key: db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash(command_value),result=result))
    db.commit();return result

@app.post("/api/v1/records/{record_id}/inventory-adjustment")
def adjust_inventory(record_id:uuid.UUID,body:InventoryAdjustment,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership),idempotency_key:str|None=Header(default=None,alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    row=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="inventory").with_for_update())
    if not row: raise HTTPException(404,"Product not found")
    if member.role not in RECORD_WRITE_ROLES["inventory"]: raise HTTPException(403,"Inventory permission is required")
    if member.role not in {"Owner","Admin"} and row.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Product not found")
    command_value={"record_id":str(row.id),"quantity":str(body.quantity),"reason":body.reason,"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=request_hash(command_value): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if row.version!=body.version: raise HTTPException(409,"Product changed; reload before adjusting stock")
    tenant=db.get(Tenant,member.tenant_id)
    if not tenant or tenant.status!="ready" or not tenant.odoo_database: raise HTTPException(503,"This workspace Odoo database is not ready")
    if not row.payload.get("odoo_id"): raise HTTPException(409,"The Odoo product link is missing")
    external=gateway_command(tenant.odoo_database,{"operation":"product.stock.adjust","payload":{"odoo_id":row.payload["odoo_id"],"quantity":str(body.quantity),"reason":body.reason}},idempotency_key)
    row.payload={**row.payload,"on_hand":external["quantity"]};row.version+=1
    audit(db,member,request,"inventory.adjusted","product",str(row.id),{"reason":body.reason,"quantity":str(body.quantity),"odoo":external})
    result={"id":str(row.id),"version":row.version,**row.payload};db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash(command_value),result=result));db.commit();return result

@app.post("/api/v1/records/{record_id}/delivery")
def deliver_sales_order(record_id:uuid.UUID,body:DeliveryCommand,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership),idempotency_key:str|None=Header(default=None,alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    row=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="sales").with_for_update())
    if not row: raise HTTPException(404,"Sales order not found")
    if member.role not in RECORD_WRITE_ROLES["sales"]: raise HTTPException(403,"Sales permission is required")
    if member.role not in {"Owner","Admin"} and row.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Sales order not found")
    command_value={"record_id":str(row.id),"version":body.version,"action":"deliver"}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=request_hash(command_value): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if row.version!=body.version: raise HTTPException(409,"Sales order changed; reload before delivering")
    if row.payload.get("status") not in {"confirmed","invoiced"}: raise HTTPException(409,"Only confirmed sales orders can be delivered")
    if row.payload.get("delivery_status")=="delivered": raise HTTPException(409,"This sales order has already been delivered")
    if not row.payload.get("odoo_id"): raise HTTPException(409,"The Odoo sales order link is missing")
    tenant=db.get(Tenant,member.tenant_id)
    if not tenant or tenant.status!="ready" or not tenant.odoo_database: raise HTTPException(503,"This workspace Odoo database is not ready")
    external=gateway_command(tenant.odoo_database,{"operation":"sale.deliver","payload":{"odoo_id":row.payload["odoo_id"]}},idempotency_key)
    if external.get("status")!="delivered": raise HTTPException(502,"Odoo did not confirm delivery")
    row.payload={**row.payload,"delivery_status":"delivered","deliveries":external.get("deliveries",[])}
    row.version+=1
    result={"id":str(row.id),"version":row.version,**row.payload}
    audit(db,member,request,"sales.delivered","sales",str(row.id),{"odoo":external})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash(command_value),result=result));db.commit();return result

@app.post("/api/v1/records/{record_id}/budget-entries",status_code=201)
def add_budget_spend(record_id:uuid.UUID,body:BudgetSpend,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership),idempotency_key:str|None=Header(default=None,alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    row=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="budgets").with_for_update())
    if not row: raise HTTPException(404,"Budget not found")
    if member.role not in RECORD_WRITE_ROLES["budgets"]: raise HTTPException(403,"Finance permission is required")
    if member.role not in {"Owner","Admin"} and row.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Budget not found")
    command_value={"record_id":str(row.id),"amount":str(body.amount),"description":body.description,"occurred_on":body.occurred_on.isoformat(),"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=request_hash(command_value): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if row.version!=body.version: raise HTTPException(409,"Budget changed; reload before recording spend")
    if row.payload.get("status") in {"cancelled","closed","archived"}: raise HTTPException(409,"Closed budgets cannot accept spend")
    try: totals=add_budget_spend(row.payload.get("limit",row.payload.get("amount")),row.payload.get("spent",0),body.amount)
    except ValueError as error: raise HTTPException(409,str(error)) from None
    limit=totals["limit"];total=totals["spent"];remaining=totals["remaining"]
    entries=list(row.payload.get("entries",[]))
    entry={"id":str(uuid.uuid4()),"amount":str(body.amount),"description":body.description.strip(),"occurred_on":body.occurred_on.isoformat(),"recorded_by":member.subject,"created_at":datetime.now(timezone.utc).isoformat()}
    entries.append(entry)
    row.payload={**row.payload,"limit":str(limit.quantize(Decimal("0.01"))),"spent":str(total),"remaining":str(remaining),"over_budget":remaining<0,"entries":entries}
    row.version+=1
    result={"budget_id":str(row.id),"entry":entry,"spent":str(total),"limit":str(limit.quantize(Decimal("0.01"))),"remaining":str(remaining),"over_budget":remaining<0,"version":row.version}
    audit(db,member,request,"budget.spend_recorded","budget",str(row.id),{"amount":str(body.amount),"occurred_on":body.occurred_on.isoformat(),"over_budget":remaining<0})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash(command_value),result=result));db.commit();return result

@app.post("/api/v1/records/{record_id}/payment-match")
def match_legacy_manual_payment(record_id:uuid.UUID,body:ManualPaymentMatch,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership),idempotency_key:str|None=Header(default=None,alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    payment=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="payments").with_for_update())
    if not payment: raise HTTPException(404,"Payment not found")
    if member.role not in RECORD_WRITE_ROLES["payments"]: raise HTTPException(403,"Finance permission is required")
    if member.role not in {"Owner","Admin"} and payment.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Payment not found")
    command_value={"record_id":str(payment.id),"finance_record_id":body.finance_record_id,"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=request_hash(command_value): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if payment.version!=body.version or payment.payload.get("status")!="unmatched": raise HTTPException(409,"Payment changed or has already been matched")
    try: invoice_id=uuid.UUID(body.finance_record_id)
    except ValueError: raise HTTPException(422,"Invoice ID must be a valid record ID") from None
    invoice=db.scalar(select(BusinessRecord).where(BusinessRecord.id==invoice_id,BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="finance").with_for_update())
    if not invoice: raise HTTPException(404,"Invoice not found")
    if invoice.payload.get("status")!="posted": raise HTTPException(409,"Only posted invoices or bills can be matched")
    already_matched=db.scalar(select(BusinessRecord.id).where(BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="payments",BusinessRecord.id!=payment.id,BusinessRecord.payload.contains({"finance_record_id":str(invoice.id)})))
    if already_matched: raise HTTPException(409,"This invoice already has a locally matched payment")
    workspace_match=db.scalar(select(WorkspaceResource.id).where(WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind=="payments",WorkspaceResource.data.contains({"finance_record_id":str(invoice.id)})))
    if workspace_match: raise HTTPException(409,"This invoice already has a locally matched payment")
    if member.role not in {"Owner","Admin"} and (str(payment.payload.get("branch_id"))!=invoice.payload.get("branch_id") or str(payment.payload.get("branch_id")) not in member.branch_ids): raise HTTPException(403,"Payment and invoice must belong to the same assigned branch")
    try:
        amount=Decimal(str(payment.payload.get("amount")));invoice_amount=Decimal(str(invoice.payload.get("total")))
    except (InvalidOperation,ValueError): raise HTTPException(409,"Payment or invoice amount is unavailable") from None
    if not amount.is_finite() or not invoice_amount.is_finite() or amount!=invoice_amount: raise HTTPException(409,"Payment amount must equal the full invoice amount; partial matches are not supported")
    if not invoice.payload.get("currency") or payment.payload.get("currency")!=invoice.payload.get("currency"): raise HTTPException(409,"Payment and invoice currency must match")
    payment.payload={**payment.payload,"status":"matched","finance_record_id":str(invoice.id),"invoice_reference":invoice.payload.get("document") or invoice.payload.get("odoo_name") or "","matched_at":datetime.now(timezone.utc).isoformat()};payment.version+=1
    result={"id":str(payment.id),"version":payment.version,**payment.payload}
    audit(db,member,request,"payment.manually_matched","payments",str(payment.id),{"finance_record_id":str(invoice.id),"amount":str(amount)})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash(command_value),result=result));db.commit();return result

@app.post("/api/v1/records/{record_id}/status")
def transition(record_id: uuid.UUID, body: StatusCommand, request: Request, db: Session = Depends(get_db), member: Membership = Depends(membership), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    idempotency_key=require_idempotency_key(idempotency_key)
    row=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id).with_for_update())
    if not row: raise HTTPException(404,"Record not found")
    if member.role not in RECORD_WRITE_ROLES[row.kind]: raise HTTPException(403,"Insufficient permission")
    if member.role not in {"Owner","Admin"} and row.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Record not found")
    if idempotency_key:
        prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
        command_value={"record_id":str(row.id),"status":body.status.lower()}
        if prior:
            if prior.request_hash!=request_hash(command_value): raise HTTPException(409,"Idempotency key was already used for a different request")
            return prior.result
    if row.version!=body.version: raise HTTPException(409,"Record changed; reload before advancing its state")
    if row.payload.get("status") in {"posted","paid","cancelled"}: raise HTTPException(409,"Posted or closed documents are protected")
    allowed={"draft":{"pending","approved","cancelled"},"pending":{"approved","rejected","cancelled"},"approved":{"confirmed","posted","cancelled"},"confirmed":{"received","invoiced","posted","cancelled"},"received":{"billed","paid"},"posted":{"paid"},"new":{"qualified","lost"},"qualified":{"proposal","lost"},"proposal":{"won","lost"},"unmatched":{"matched","exception"}}
    current=row.payload.get("status","draft").lower()
    if body.status.lower() not in allowed.get(current,set()): raise HTTPException(409,f"Transition {current} → {body.status} is not allowed")
    target=body.status.lower()
    if target=="approved":
        if member.role not in {"Owner","Admin","Finance manager"}: raise HTTPException(403,"A finance manager or workspace administrator must approve this document")
        if row.created_by==member.subject: raise HTTPException(403,"The requester cannot approve their own document")
        if row.kind=="approvals" and row.payload.get("approver")!=member.display_name: raise HTTPException(403,"Only the assigned approver can approve this request")
    if target in {"posted","paid","matched"} and member.role not in {"Owner","Admin","Finance manager"}: raise HTTPException(403,"Finance permission is required for this action")
    if row.kind=="payments" and target=="matched": raise HTTPException(409,"Use the exact-amount payment-match action and identify a posted invoice")
    external_result=None
    odoo_operation={("leads","qualified"):"lead.stage",("leads","proposal"):"lead.stage",("leads","won"):"lead.stage",("leads","lost"):"lead.stage",("sales","confirmed"):"sale.confirm",("sales","invoiced"):"sale.invoice.create",("sales","cancelled"):"sale.cancel",("purchasing","confirmed"):"purchase.confirm",("purchasing","received"):"purchase.receive",("purchasing","billed"):"purchase.bill.create",("purchasing","cancelled"):"purchase.cancel",("finance","posted"):"invoice.post",("finance","cancelled"):"invoice.cancel"}.get((row.kind,target))
    if odoo_operation:
        if not idempotency_key: raise HTTPException(400,"Idempotency-Key is required")
        tenant=db.get(Tenant,member.tenant_id)
        if not tenant or tenant.status!="ready" or not tenant.odoo_database: raise HTTPException(503,"This workspace Odoo database is not ready")
        if not row.payload.get("odoo_id"): raise HTTPException(409,"The Odoo document link is missing")
        external_payload={"odoo_id":row.payload["odoo_id"]}
        if row.kind=="leads": external_payload["status"]=target
        external_result=gateway_command(tenant.odoo_database,{"operation":odoo_operation,"payload":external_payload},idempotency_key)
        target=external_result.get("status",target)
        if (row.kind=="sales" and target=="invoiced") or (row.kind=="purchasing" and target=="billed"):
            for invoice in external_result.get("invoices",external_result.get("bills",[])):
                lines=invoice.get("lines",[]);first_line=lines[0] if lines else {}
                invoice_payload={"odoo_id":invoice["id"],"odoo_name":invoice["name"],"document":invoice["name"],"party":invoice["partner_name"],"partner_id":invoice["partner_id"],"product_id":first_line.get("product_id"),"move_type":invoice["move_type"],"currency":invoice.get("currency",""),"due_date":invoice["invoice_date_due"],"total":invoice["amount_total"],"branch_id":row.payload.get("branch_id"),"status":"draft","source_sale_id":str(row.id) if row.kind=="sales" else "","source_purchase_id":str(row.id) if row.kind=="purchasing" else "","quantity":first_line.get("quantity",1),"unit_price":first_line.get("unit_price",0),"lines":lines}
                mirror=BusinessRecord(tenant_id=member.tenant_id,kind="finance",payload=invoice_payload,created_by=member.subject);db.add(mirror);db.flush()
                audit(db,member,request,"finance.created_from_sale" if row.kind=="sales" else "finance.created_from_purchase","finance",str(mirror.id),{"sale_record_id":str(row.id) if row.kind=="sales" else "","purchase_record_id":str(row.id) if row.kind=="purchasing" else "","odoo_invoice_id":invoice["id"]})
    if row.kind in {"sales","purchasing","finance","payments","inventory"}:
        if not idempotency_key: raise HTTPException(400,"Idempotency-Key is required")
    row.payload={**row.payload,"status":target};row.version+=1
    audit(db,member,request,f"{row.kind}.status_changed",row.kind,str(row.id),{"status":target,"odoo":external_result or {}})
    result={"id":str(row.id),"version":row.version,**row.payload}
    if idempotency_key: db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=request_hash({"record_id":str(row.id),"status":body.status.lower()}),result=result))
    db.commit();return result

@app.delete("/api/v1/records/{record_id}", status_code=204)
def delete_record(record_id: uuid.UUID, request: Request, db: Session = Depends(get_db), member: Membership = Depends(membership)):
    row=db.scalar(select(BusinessRecord).where(BusinessRecord.id==record_id,BusinessRecord.tenant_id==member.tenant_id).with_for_update())
    if not row: raise HTTPException(404,"Record not found")
    if member.role not in RECORD_WRITE_ROLES[row.kind]: raise HTTPException(403,"Insufficient permission")
    if member.role not in {"Owner","Admin"} and row.payload.get("branch_id") not in member.branch_ids: raise HTTPException(404,"Record not found")
    if row.payload.get("odoo_id"): raise HTTPException(409,"This record is owned by Odoo and cannot be deleted from the local mirror")
    if row.payload.get("status") in {"posted","paid"}: raise HTTPException(409,"Posted documents cannot be removed")
    audit(db,member,request,f"{row.kind}.deleted",row.kind,str(row.id));db.delete(row);db.commit()

@app.get("/api/v1/audit")
def audit_history(db: Session = Depends(get_db), member: Membership = Depends(allow("Owner","Admin"))):
    rows=db.scalars(select(AuditEvent).where(AuditEvent.tenant_id==member.tenant_id).order_by(AuditEvent.created_at.desc()).limit(200))
    return [{"id":str(x.id),"actor":x.actor,"action":x.action,"entity":x.entity,"entity_id":x.entity_id,"request_id":x.request_id,"created_at":x.created_at} for x in rows]
