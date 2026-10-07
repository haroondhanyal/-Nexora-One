"""Tenant-safe, provider-neutral workflows for commerce, operations and automation."""
import hashlib
import csv
import io
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db
from .api_credentials import API_CLIENT_ROLES, new_api_token, token_digest
from .document_storage import validate_text_upload
from .reporting import REPORT_GROUPS, REPORT_SOURCES, aggregate_report
from .models import ApiClientCredential, AuditEvent, Branch, BusinessRecord, IdempotencyKey, Membership, WorkspaceResource
from .pos import cash_variance, pos_cash_totals
from .schemas import PosSaleCreate, ReportRun
from .security import membership

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace operations"])
KINDS = {
    "storefronts", "orders", "promotions", "returns", "pos_sessions", "projects", "timesheets", "payments",
    "service_tickets", "field_jobs", "documents", "workflows", "workflow_runs", "reports",
    "api_clients", "webhooks", "custom_fields", "integration_health", "imports",
}
MANAGE = {"Owner", "Admin"}
KIND_ROLES = {
    "storefronts": MANAGE, "orders": {"Owner", "Admin", "Sales", "Finance manager"},
    "payments": {"Owner", "Admin", "Finance manager"},
    "promotions": {"Owner", "Admin", "Sales"}, "returns": {"Owner", "Admin", "Sales", "Finance manager"},
    "pos_sessions": {"Owner", "Admin", "Sales"}, "projects": {"Owner", "Admin", "Sales", "Staff"},
    "timesheets": {"Owner", "Admin", "Sales", "Staff", "Employee", "HR manager"},
    "service_tickets": {"Owner", "Admin", "Sales", "Staff"}, "field_jobs": {"Owner", "Admin", "Sales", "Staff"},
    "documents": {"Owner", "Admin", "Finance manager", "HR manager", "Employee", "Staff"},
    "workflows": MANAGE, "workflow_runs": MANAGE, "reports": {"Owner", "Admin", "Finance manager", "HR manager", "Sales"},
    "api_clients": MANAGE, "webhooks": MANAGE, "custom_fields": MANAGE, "integration_health": MANAGE, "imports": MANAGE,
}
BRANCH_REQUIRED = {"orders", "returns", "pos_sessions", "projects", "timesheets", "payments", "service_tickets", "field_jobs", "documents", "imports"}
INITIAL = {"storefronts":"draft", "orders":"draft", "promotions":"draft", "returns":"pending", "pos_sessions":"open", "projects":"active", "timesheets":"submitted", "payments":"unmatched", "service_tickets":"open", "field_jobs":"scheduled", "documents":"active", "workflows":"draft", "workflow_runs":"queued", "reports":"ready", "api_clients":"active", "webhooks":"active", "custom_fields":"active", "integration_health":"unknown", "imports":"queued"}
TRANSITIONS = {
    "storefronts":{"draft":{"disabled"}},
    # Local records cannot assert provider payment, stock delivery or refunds.
    "orders":{"draft":{"pending","cancelled"},"pending":{"cancelled"}},
    "promotions":{"draft":{"active","disabled"},"active":{"disabled"}},
    "returns":{"pending":{"approved","rejected"},"approved":{"closed"}}, "payments":{"unmatched":{"matched","exception"}},
    "pos_sessions":{"open":{"closed"}}, "projects":{"active":{"on_hold","completed","cancelled"},"on_hold":{"active","cancelled"}},
    "timesheets":{"submitted":{"approved","rejected"},"rejected":{"submitted"}},
    "service_tickets":{"open":{"in_progress","closed"},"in_progress":{"waiting","resolved","closed"},"waiting":{"in_progress","closed"},"resolved":{"closed","reopened"}},
    "field_jobs":{"scheduled":{"in_progress","cancelled"},"in_progress":{"completed","blocked"},"blocked":{"in_progress","cancelled"}},
    "documents":{"active":{"archived"}}, "workflows":{"draft":{"active","disabled"},"active":{"disabled"}},
    "workflow_runs":{"queued":{"running","failed"},"running":{"succeeded","failed"}},
    "reports":{"ready":{"archived"}}, "api_clients":{"active":{"revoked"}}, "webhooks":{"active":{"disabled"}},
    "custom_fields":{"active":{"disabled"}}, "integration_health":{"unknown":{"healthy","degraded","disconnected"},"healthy":{"degraded","disconnected"},"degraded":{"healthy","disconnected"},"disconnected":{"healthy"}},
    "imports":{"queued":{"running","cancelled"},"running":{"completed","failed"}},
}

class ResourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    branch_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

class ResourceUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    branch_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(ge=1)

class ResourceTransition(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    version: int = Field(ge=1)

class WorkflowRun(BaseModel):
    target_kind: str = Field(min_length=1, max_length=48)
    target_id: uuid.UUID
    expected_status: str = Field(min_length=1, max_length=32)
    note: str = Field(default="", max_length=500)

class ImportRun(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=1, max_length=1000)

class PaymentMatch(BaseModel):
    finance_record_id: uuid.UUID
    version: int = Field(ge=1)

class AssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    sources: list[str] = Field(min_length=1, max_length=8)


def _hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",",":"), default=str).encode()).hexdigest()

def _audit(db, member, request, action, kind, entity_id, detail=None):
    db.add(AuditEvent(tenant_id=member.tenant_id, actor=member.subject, action=action, entity=kind, entity_id=str(entity_id), detail=detail or {}, request_id=request.state.request_id))

def _allowed(member: Membership, kind: str):
    if member.role not in KIND_ROLES[kind]: raise HTTPException(403, "Insufficient permission")
    if member.role not in MANAGE and kind in BRANCH_REQUIRED and not member.branch_ids: raise HTTPException(403, "Assign at least one branch to this membership")

def _branch(db, member, value, kind):
    if not value:
        if kind in BRANCH_REQUIRED and member.role not in MANAGE: raise HTTPException(422, "Choose a branch in this workspace")
        return None
    try: branch_id=uuid.UUID(value)
    except (TypeError, ValueError): raise HTTPException(422, "Branch ID must be a UUID") from None
    if not db.scalar(select(Branch.id).where(Branch.id==branch_id,Branch.tenant_id==member.tenant_id)): raise HTTPException(422, "Branch is outside this workspace")
    if member.role not in MANAGE and str(branch_id) not in member.branch_ids: raise HTTPException(403, "Branch is outside your assigned scope")
    return branch_id

def _row(db, member, kind, resource_id):
    row=db.scalar(select(WorkspaceResource).where(WorkspaceResource.id==resource_id,WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind==kind).with_for_update())
    if row is None: raise HTTPException(404, "Workspace record not found")
    if member.role not in MANAGE:
        if row.branch_id and str(row.branch_id) not in member.branch_ids: raise HTTPException(404, "Workspace record not found")
        if kind=="documents" and row.created_by!=member.subject: raise HTTPException(404, "Workspace record not found")
        if kind=="timesheets" and row.created_by!=member.subject and member.role=="Employee": raise HTTPException(404, "Workspace record not found")
    return row

def _output(row):
    return {"id":str(row.id),"kind":row.kind,"title":row.title,"status":row.status,"branch_id":str(row.branch_id) if row.branch_id else "","data":row.data,"version":row.version,"created_by":row.created_by,"created_at":row.created_at.isoformat(),"updated_at":row.updated_at.isoformat()}

def _custom_field_errors(db, member, kind, data):
    fields=db.scalars(select(WorkspaceResource).where(WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind=="custom_fields",WorkspaceResource.status=="active"))
    for item in fields:
        definition=item.data
        if definition.get("entity")!=kind: continue
        key=definition.get("key") or ""
        value=data.get(key)
        if definition.get("required") and (value is None or value==""):
            raise HTTPException(422, f"Custom field '{definition.get('label',key)}' is required")
        if value is None: continue
        field_type=definition.get("field_type")
        if field_type=="number":
            try: Decimal(str(value))
            except InvalidOperation: raise HTTPException(422, f"Custom field '{definition.get('label',key)}' must be numeric") from None
        if field_type=="boolean" and not isinstance(value,bool): raise HTTPException(422, f"Custom field '{definition.get('label',key)}' must be true or false")
        if field_type=="date" and (not isinstance(value,str) or len(value)!=10): raise HTTPException(422, f"Custom field '{definition.get('label',key)}' must use YYYY-MM-DD")

def _validate_data(kind, data):
    numeric_fields={"orders":["total"],"returns":["amount"],"projects":["budget"],"pos_sessions":["opening_cash","closing_cash"],"timesheets":["hours"]}.get(kind,[])
    for field in numeric_fields:
        value=data.get(field)
        if value in (None,""):
            if field in {"total","amount","budget","opening_cash","hours"}: raise HTTPException(422,f"{field.replace('_',' ').title()} is required")
            continue
        try: number=Decimal(str(value))
        except InvalidOperation: raise HTTPException(422,f"{field.replace('_',' ').title()} must be numeric") from None
        if not number.is_finite() or number<0 or field=="hours" and (number==0 or number>24): raise HTTPException(422,f"{field.replace('_',' ').title()} is outside the allowed range")
    if kind=="promotions":
        try: discount=Decimal(str(data.get("discount")))
        except InvalidOperation: raise HTTPException(422,"Discount must be a percentage") from None
        if not discount.is_finite() or discount<0 or discount>100: raise HTTPException(422,"Discount must be from 0 to 100")
    if kind=="payments":
        try: amount=Decimal(str(data.get("amount")))
        except InvalidOperation: raise HTTPException(422,"Payment amount must be numeric") from None
        currency=str(data.get("currency") or "")
        if not amount.is_finite() or amount<=0 or not data.get("reference") or len(currency)!=3 or not currency.isalpha() or currency.upper()!=currency: raise HTTPException(422,"Payment reference, positive amount and uppercase ISO currency are required")
    if kind=="reports":
        if data.get("source_kind") not in REPORT_SOURCES: raise HTTPException(422,"Choose a supported operational report source")
        if data.get("group_by") not in REPORT_GROUPS: raise HTTPException(422,"Group reports by status or branch")
        if len(str(data.get("status_filter") or ""))>32: raise HTTPException(422,"Report status filter is too long")

@router.get("/{kind}")
def list_resources(kind:str, db:Session=Depends(get_db), member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    query=select(WorkspaceResource).where(WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind==kind).order_by(WorkspaceResource.updated_at.desc()).limit(1000)
    rows=db.scalars(query)
    if member.role not in MANAGE:
        rows=[row for row in rows if (not row.branch_id or str(row.branch_id) in member.branch_ids) and (kind!="documents" or row.created_by==member.subject) and (kind!="timesheets" or member.role!="Employee" or row.created_by==member.subject)]
    return [_output(row) for row in rows]

@router.post("/{kind}",status_code=201)
def create_resource(kind:str, body:ResourceCreate, request:Request, idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"), db:Session=Depends(get_db), member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    command={"kind":kind,"title":body.title,"branch_id":body.branch_id,"data":body.data}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    branch_id=_branch(db,member,body.branch_id,kind)
    if kind in {"custom_fields"}:
        field_type=body.data.get("field_type")
        if field_type not in {"text","number","date","boolean"}: raise HTTPException(422,"Custom field type must be text, number, date or boolean")
        if body.data.get("entity") not in {"orders","projects","timesheets","service_tickets","field_jobs","documents"}: raise HTTPException(422,"Custom field entity is not supported")
        body.data["label"]=body.title.strip()
        body.data["key"]="".join(ch.lower() if ch.isalnum() else "_" for ch in body.title).strip("_")
        if not body.data["key"]: raise HTTPException(422,"Custom field label is required")
    if kind=="workflows" and body.data.get("action_type") not in {"create_approval","set_status"}: raise HTTPException(422,"Workflow action must be create_approval or set_status")
    _validate_data(kind,body.data)
    api_token=None
    if kind=="api_clients":
        role_scope=body.data.get("role_scope")
        if role_scope not in API_CLIENT_ROLES:
            raise HTTPException(422,"Choose a supported least-privilege role for this API client")
        if not branch_id: raise HTTPException(422,"Choose one branch to scope the API client")
        try: expires_in_days=int(body.data.get("expires_in_days",90))
        except (TypeError,ValueError): raise HTTPException(422,"API client expiry must be 1–365 days") from None
        if not 1<=expires_in_days<=365: raise HTTPException(422,"API client expiry must be 1–365 days")
        scoped_branch=str(branch_id)
        if member.role not in MANAGE and scoped_branch not in member.branch_ids: raise HTTPException(403,"API client branch is outside your assigned scope")
        branch_ids=[scoped_branch]
        expires_at=datetime.now(timezone.utc)+timedelta(days=expires_in_days)
        api_token=new_api_token()
        body.data={**body.data,"role_scope":role_scope,"expires_in_days":expires_in_days,"branch_ids":branch_ids,"expires_at":expires_at.isoformat()}
    if kind=="webhooks": raise HTTPException(422,"Webhook delivery is unavailable until a secure outbound delivery worker is configured")
    if kind not in {"custom_fields","workflows"}: _custom_field_errors(db,member,kind,body.data)
    row=WorkspaceResource(tenant_id=member.tenant_id,kind=kind,branch_id=branch_id,title=body.title.strip(),status=INITIAL[kind],data=body.data,created_by=member.subject,updated_by=member.subject)
    db.add(row);db.flush()
    if api_token:
        db.add(ApiClientCredential(tenant_id=member.tenant_id,resource_id=row.id,token_hash=token_digest(api_token),subject=member.subject,role=body.data["role_scope"],branch_ids=body.data["branch_ids"],expires_at=expires_at))
    result=_output(row)
    _audit(db,member,request,f"workspace.{kind}.created",kind,row.id)
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit()
    if api_token: return {**result,"api_token":api_token,"warning":"Copy this token now. It will not be shown again."}
    return result

@router.post("/documents/upload",status_code=201)
async def upload_document(request:Request,title:str=Form(...,min_length=1,max_length=200),file:UploadFile=File(...),branch_id:str|None=Form(default=None),idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    _allowed(member,"documents")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    raw=await file.read(2*1024*1024+1)
    try: filename=validate_text_upload(file.filename,file.content_type,raw)
    except ValueError as error: raise HTTPException(422,str(error)) from None
    finally: await file.close()
    if not title.strip(): raise HTTPException(422,"Document title is required")
    digest=hashlib.sha256(raw).hexdigest()
    branch=_branch(db,member,branch_id,"documents")
    command={"kind":"documents","title":title.strip(),"branch_id":str(branch or ""),"filename":filename,"sha256":digest}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    root=Path(os.getenv("DOCUMENT_STORAGE_ROOT","/tmp/nexora-documents")).resolve()
    tenant_dir=(root/str(member.tenant_id)).resolve()
    if root not in tenant_dir.parents: raise HTTPException(500,"Document storage path is invalid")
    try:
        tenant_dir.mkdir(mode=0o700,parents=True,exist_ok=True)
        tenant_dir.chmod(0o700)
        file_id=uuid.uuid4()
        stored=(tenant_dir/f"{file_id.hex}.txt").resolve()
        if stored.parent!=tenant_dir: raise OSError("Unsafe storage path")
        stored.write_bytes(raw)
        stored.chmod(0o600)
    except OSError:
        raise HTTPException(503,"Local document storage is unavailable") from None
    row=WorkspaceResource(tenant_id=member.tenant_id,kind="documents",branch_id=branch,title=title.strip(),status="active",data={"filename":filename,"file_id":str(file_id),"content_type":"text/plain; charset=utf-8","size_bytes":len(raw),"sha256":digest},created_by=member.subject,updated_by=member.subject)
    try:
        db.add(row);db.flush();result=_output(row)
        _audit(db,member,request,"workspace.document_uploaded","documents",row.id,{"filename":filename,"size_bytes":len(raw),"sha256":digest})
        db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result))
        db.commit()
    except Exception:
        db.rollback()
        stored.unlink(missing_ok=True)
        raise
    return result

@router.get("/documents/{resource_id}/download")
def download_document(resource_id:uuid.UUID,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership)):
    _allowed(member,"documents")
    row=_row(db,member,"documents",resource_id)
    if row.status!="active": raise HTTPException(410,"Archived documents are not downloadable")
    try: file_id=uuid.UUID(row.data.get("file_id",""))
    except (AttributeError,TypeError,ValueError): raise HTTPException(404,"This document has no uploaded file") from None
    root=Path(os.getenv("DOCUMENT_STORAGE_ROOT","/tmp/nexora-documents")).resolve()
    tenant_dir=(root/str(member.tenant_id)).resolve();stored=(tenant_dir/f"{file_id.hex}.txt").resolve()
    if stored.parent!=tenant_dir or root not in tenant_dir.parents: raise HTTPException(404,"Document file not found")
    if not stored.is_file(): raise HTTPException(410,"Document file is no longer available")
    _audit(db,member,request,"workspace.document_downloaded","documents",row.id,{"sha256":row.data.get("sha256","")});db.commit()
    filename=quote(row.data.get("filename","document.txt"),safe="")
    return FileResponse(stored,media_type="text/plain; charset=utf-8",headers={"Content-Disposition":f"attachment; filename=\"document.txt\"; filename*=UTF-8''{filename}","X-Content-Type-Options":"nosniff","Cache-Control":"private, no-store"})

@router.put("/{kind}/{resource_id}")
def update_resource(kind:str,resource_id:uuid.UUID,body:ResourceUpdate,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    if kind in {"api_clients","webhooks","workflow_runs"}: raise HTTPException(405,"This resource is immutable")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    row=_row(db,member,kind,resource_id)
    command={"kind":kind,"id":str(row.id),"title":body.title,"branch_id":body.branch_id,"data":body.data,"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if row.version!=body.version: raise HTTPException(409,"Record changed; reload before editing")
    if kind=="payments" and row.status!="unmatched": raise HTTPException(409,"Matched or exception payments cannot be edited")
    if kind=="pos_sessions" and row.status!="open": raise HTTPException(409,"Closed POS sessions cannot be edited")
    if kind=="pos_sessions" and row.data.get("sales"): raise HTTPException(409,"A POS session with recorded sales cannot be edited")
    if kind=="orders" and row.status!="draft": raise HTTPException(409,"Only draft local orders can be edited")
    if kind=="timesheets" and row.status not in {"submitted","rejected"}: raise HTTPException(409,"Approved timesheets cannot be edited")
    branch_id=_branch(db,member,body.branch_id,kind)
    _validate_data(kind,body.data)
    if kind=="documents" and row.data.get("file_id"):
        protected_file_fields={key:row.data[key] for key in ("file_id","filename","content_type","size_bytes","sha256") if key in row.data}
        body.data={**body.data,**protected_file_fields}
    _custom_field_errors(db,member,kind,body.data)
    row.title=body.title.strip();row.branch_id=branch_id;row.data=body.data;row.version+=1;row.updated_by=member.subject
    result=_output(row);_audit(db,member,request,f"workspace.{kind}.updated",kind,row.id)
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.post("/pos_sessions/{session_id}/sales",status_code=201)
def record_pos_sale(session_id:uuid.UUID,body:PosSaleCreate,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if member.role not in {"Owner","Admin","Sales"}: raise HTTPException(403,"Sales permission is required")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    session=_row(db,member,"pos_sessions",session_id)
    command={"session_id":str(session.id),**body.model_dump(mode="json")}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if session.version!=body.version: raise HTTPException(409,"POS session changed; reload before recording a sale")
    if session.status!="open": raise HTTPException(409,"POS sales can only be added to an open session")
    if body.tender=="external_reference" and not body.reference.strip(): raise HTTPException(422,"An externally verified payment reference is required")
    sales=list(session.data.get("sales",[]))
    sale={"id":str(uuid.uuid4()),"amount":str(body.amount),"description":body.description.strip(),"tender":body.tender,"reference":body.reference.strip(),"recorded_by":member.subject,"created_at":datetime.now(timezone.utc).isoformat()}
    sales.append(sale)
    try: totals=pos_cash_totals(session.data["opening_cash"],sales)
    except (KeyError,ValueError) as error: raise HTTPException(409,str(error) or "POS session cash totals are invalid") from None
    session.data={**session.data,"sales":sales,"cash_sales":str(totals["cash_sales"]),"expected_closing_cash":str(totals["expected_closing_cash"].quantize(Decimal("0.01")))}
    session.version+=1;session.updated_by=member.subject
    result={"id":sale["id"],"session_id":str(session.id),"sale":sale,"cash_sales":session.data["cash_sales"],"expected_closing_cash":session.data["expected_closing_cash"],"version":session.version}
    _audit(db,member,request,"workspace.pos_sale_recorded","pos_sessions",session.id,{"amount":sale["amount"],"tender":sale["tender"]})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.post("/{kind}/{resource_id}/transition")
def transition_resource(kind:str,resource_id:uuid.UUID,body:ResourceTransition,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    row=_row(db,member,kind,resource_id);command={"kind":kind,"id":str(row.id),"status":body.status.lower(),"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if row.version!=body.version: raise HTTPException(409,"Record changed; reload before advancing its state")
    target=body.status.lower()
    if target not in TRANSITIONS[kind].get(row.status,set()): raise HTTPException(409,f"Transition {row.status} to {target} is not allowed")
    if kind=="api_clients" and target=="revoked":
        credential=db.scalar(select(ApiClientCredential).where(ApiClientCredential.tenant_id==member.tenant_id,ApiClientCredential.resource_id==row.id).with_for_update())
        if credential is None: raise HTTPException(409,"API credential record is missing")
        credential.revoked_at=datetime.now(timezone.utc)
    if kind=="pos_sessions" and target=="closed":
        if row.data.get("closing_cash") in (None,""): raise HTTPException(422,"Enter counted closing cash before closing the POS session")
        try:
            totals=pos_cash_totals(row.data.get("opening_cash",0),row.data.get("sales",[]))
            variance=cash_variance(row.data["closing_cash"],totals["expected_closing_cash"])
        except (KeyError,ValueError) as error: raise HTTPException(422,str(error) or "POS session cash totals are invalid") from None
        row.data={**row.data,"cash_sales":str(totals["cash_sales"]),"expected_closing_cash":str(totals["expected_closing_cash"].quantize(Decimal("0.01"))),"cash_variance":str(variance)}
    if target in {"approved","paid","refunded","fulfilled","completed","published"} and member.role not in MANAGE|{"Finance manager"}: raise HTTPException(403,"A workspace approver is required")
    if target=="approved" and row.created_by==member.subject: raise HTTPException(403,"The requester cannot approve their own request")
    row.status=target;row.version+=1;row.updated_by=member.subject
    result=_output(row);_audit(db,member,request,f"workspace.{kind}.{target}",kind,row.id)
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.delete("/{kind}/{resource_id}",status_code=204)
def delete_resource(kind:str,resource_id:uuid.UUID,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    if kind not in {"reports","imports","workflow_runs"}: raise HTTPException(409,"This record must be closed or archived through its status workflow")
    row=_row(db,member,kind,resource_id)
    if row.status not in {"ready","queued","failed","cancelled","archived","completed"}: raise HTTPException(409,"Only inactive records can be removed")
    _audit(db,member,request,f"workspace.{kind}.deleted",kind,row.id);db.delete(row);db.commit()

@router.get("/analytics/summary")
def analytics_summary(db:Session=Depends(get_db),member:Membership=Depends(membership)):
    allowed=[kind for kind,roles in KIND_ROLES.items() if member.role in roles]
    rows=db.scalars(select(WorkspaceResource).where(WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind.in_(allowed)).order_by(WorkspaceResource.created_at.desc()).limit(5000))
    summary={kind:{"count":0,"by_status":{}} for kind in allowed}
    for row in rows:
        if member.role not in MANAGE and row.branch_id and str(row.branch_id) not in member.branch_ids: continue
        bucket=summary[row.kind];bucket["count"]+=1;bucket["by_status"][row.status]=bucket["by_status"].get(row.status,0)+1
    return {"generated_at":datetime.now(timezone.utc).isoformat(),"scope":"workspace and assigned branches","resources":summary,"note":"Live counts from workspace operational records; no external ledger or payroll values are included."}

@router.post("/reports/{report_id}/run")
def run_report(report_id:uuid.UUID,body:ReportRun,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if member.role not in KIND_ROLES["reports"]: raise HTTPException(403,"Reports are not available to this role")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    report=_row(db,member,"reports",report_id)
    command={"report_id":str(report.id),"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if report.version!=body.version: raise HTTPException(409,"Report changed; reload before running it")
    if report.status!="ready": raise HTTPException(409,"Only ready reports can run")
    source=report.data.get("source_kind")
    if source not in REPORT_SOURCES: raise HTTPException(422,"Report source is not supported")
    rows=list_resources(source,db,member)
    result=aggregate_report(rows,report.data.get("group_by","status"),str(report.data.get("status_filter") or ""))
    branch_names={str(row.id):row.name for row in db.scalars(select(Branch).where(Branch.tenant_id==member.tenant_id))}
    if result["group_by"]=="branch": result["groups"]={((branch_names.get(key,"Unassigned")+f" · {key[:8]}") if key!="unassigned" else "Unassigned"):value for key,value in result["groups"].items()}
    result={**result,"report_id":str(report.id),"title":report.title,"source_kind":source,"run_at":datetime.now(timezone.utc).isoformat()}
    report.data={**report.data,"last_run":result};report.version+=1;report.updated_by=member.subject
    _audit(db,member,request,"workspace.report_run","reports",report.id,{"source_kind":source,"record_count":result["record_count"]})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.get("/{kind}/export.json")
def export_resources(kind:str,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    rows=list_resources(kind,db,member)
    _audit(db,member,request,"workspace.resource_exported",kind,"",{"count":len(rows),"format":"json"});db.commit()
    return {"kind":kind,"count":len(rows),"exported_at":datetime.now(timezone.utc).isoformat(),"records":rows}

@router.get("/{kind}/export.csv")
def export_resources_csv(kind:str,request:Request,db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if kind not in KINDS: raise HTTPException(404,"Unknown workspace resource")
    _allowed(member,kind)
    rows=list_resources(kind,db,member)
    flattened=[]
    keys={"id","kind","title","status","branch_id","version","created_by","created_at","updated_at"}
    for row in rows:
        item={key:row.get(key,"") for key in keys}
        for key,value in (row.get("data") or {}).items():
            name=f"data.{key}";keys.add(name)
            cell=json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else value
            if isinstance(cell,str) and cell.lstrip().startswith(("=","+","-","@","\t","\r")): cell="'"+cell
            item[name]=cell
        for key,value in list(item.items()):
            if isinstance(value,str) and value.lstrip().startswith(("=","+","-","@","\t","\r")): item[key]="'"+value
        flattened.append(item)
    output=io.StringIO(newline="")
    columns=sorted(keys)
    writer=csv.DictWriter(output,fieldnames=columns,extrasaction="ignore",lineterminator="\r\n")
    writer.writeheader();writer.writerows(flattened)
    _audit(db,member,request,"workspace.resource_exported",kind,"",{"count":len(rows),"format":"csv"});db.commit()
    return Response(content="\ufeff"+output.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="nexora-{kind}.csv"'})

@router.post("/imports/{import_id}/run")
def run_import(import_id:uuid.UUID,body:ImportRun,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if member.role not in MANAGE: raise HTTPException(403,"Only workspace administrators can run imports")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    command={"import_id":str(import_id),"rows":body.rows}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    job=_row(db,member,"imports",import_id)
    if job.status!="queued": raise HTTPException(409,"Only queued import jobs can run")
    target_kind=job.data.get("target_kind")
    importable={"storefronts","orders","promotions","returns","pos_sessions","projects","timesheets","service_tickets","field_jobs","documents"}
    if target_kind not in importable: raise HTTPException(422,"Import target is not supported")
    created=[]
    for index,item in enumerate(body.rows):
        if not isinstance(item,dict): raise HTTPException(422,f"Import row {index+1} must be an object")
        title=str(item.get("title") or "").strip();data=item.get("data") or {}
        if not title or len(title)>200 or not isinstance(data,dict): raise HTTPException(422,f"Import row {index+1} needs a title and object data")
        branch_id=_branch(db,member,item.get("branch_id"),target_kind)
        _validate_data(target_kind,data)
        _custom_field_errors(db,member,target_kind,data)
        record=WorkspaceResource(tenant_id=member.tenant_id,kind=target_kind,branch_id=branch_id,title=title,status=INITIAL.get(target_kind,"active"),data=data,created_by=member.subject,updated_by=member.subject)
        db.add(record);created.append(record)
    job.status="completed";job.data={**job.data,"imported_count":len(created),"completed_at":datetime.now(timezone.utc).isoformat()};job.version+=1;job.updated_by=member.subject
    db.flush();result={"id":str(job.id),"status":job.status,"imported_count":len(created),"record_ids":[str(row.id) for row in created]}
    _audit(db,member,request,"workspace.import_completed","imports",job.id,{"target_kind":target_kind,"count":len(created)})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.post("/payments/{payment_id}/match")
def match_manual_payment(payment_id:uuid.UUID,body:PaymentMatch,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if member.role not in {"Owner","Admin","Finance manager"}: raise HTTPException(403,"Finance permission is required")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    payment=_row(db,member,"payments",payment_id);command={"payment_id":str(payment.id),"finance_record_id":str(body.finance_record_id),"version":body.version}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    if payment.status!="unmatched" or payment.version!=body.version: raise HTTPException(409,"Payment changed or has already been matched")
    invoice=db.scalar(select(BusinessRecord).where(BusinessRecord.id==body.finance_record_id,BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="finance").with_for_update())
    if not invoice: raise HTTPException(404,"Invoice not found")
    if invoice.payload.get("status")!="posted": raise HTTPException(409,"Only posted Odoo invoices and bills can be manually matched")
    legacy_match=db.scalar(select(BusinessRecord.id).where(BusinessRecord.tenant_id==member.tenant_id,BusinessRecord.kind=="payments",BusinessRecord.payload.contains({"finance_record_id":str(invoice.id)})))
    other_match=db.scalar(select(WorkspaceResource.id).where(WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind=="payments",WorkspaceResource.id!=payment.id,WorkspaceResource.data.contains({"finance_record_id":str(invoice.id)})))
    if legacy_match or other_match: raise HTTPException(409,"This invoice already has a locally matched payment")
    if member.role not in MANAGE and (str(payment.branch_id)!=invoice.payload.get("branch_id") or str(payment.branch_id) not in member.branch_ids): raise HTTPException(403,"Payment and invoice must be in the same assigned branch")
    try: payment_amount=Decimal(str(payment.data.get("amount")));invoice_amount=Decimal(str(invoice.payload.get("total")))
    except InvalidOperation: raise HTTPException(409,"Payment or invoice amount is unavailable") from None
    if not invoice.payload.get("currency") or payment.data.get("currency")!=invoice.payload.get("currency"): raise HTTPException(409,"Payment and invoice currency must match")
    if not payment_amount.is_finite() or not invoice_amount.is_finite(): raise HTTPException(409,"Payment or invoice amount is invalid")
    if payment_amount!=invoice_amount: raise HTTPException(409,"Payment amount must equal the open invoice amount; partial matching is not supported")
    payment.status="matched";payment.version+=1;payment.updated_by=member.subject;payment.data={**payment.data,"finance_record_id":str(invoice.id),"invoice_reference":invoice.payload.get("document") or invoice.payload.get("odoo_name") or "","matched_at":datetime.now(timezone.utc).isoformat()}
    result=_output(payment);_audit(db,member,request,"workspace.payment_manually_matched","payments",payment.id,{"finance_record_id":str(invoice.id),"amount":str(payment_amount)})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.post("/workflows/{workflow_id}/run",status_code=201)
def run_workflow(workflow_id:uuid.UUID,body:WorkflowRun,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),db:Session=Depends(get_db),member:Membership=Depends(membership)):
    if member.role not in MANAGE: raise HTTPException(403,"Only workspace administrators can run automation")
    if not idempotency_key or len(idempotency_key)>200: raise HTTPException(400,"A valid Idempotency-Key is required")
    command={"workflow_id":str(workflow_id),**body.model_dump(mode="json")}
    prior=db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id==member.tenant_id,IdempotencyKey.key==idempotency_key))
    if prior:
        if prior.request_hash!=_hash(command): raise HTTPException(409,"Idempotency key was already used for a different request")
        return prior.result
    workflow=_row(db,member,"workflows",workflow_id)
    if workflow.status!="active": raise HTTPException(409,"Only active workflows can run")
    target_kind=body.target_kind
    if target_kind not in KINDS or target_kind in {"workflows","workflow_runs","api_clients","webhooks"}: raise HTTPException(422,"Unsupported workflow target")
    target=_row(db,member,target_kind,body.target_id)
    action=workflow.data.get("action_type")
    if target.status!=body.expected_status: raise HTTPException(409,"Target status changed; reload before running this workflow")
    if action=="set_status":
        next_status=workflow.data.get("target_status")
        if next_status not in TRANSITIONS[target_kind].get(target.status,set()): raise HTTPException(422,"Configured workflow transition is not valid for this target")
        if next_status in {"approved","paid","refunded","fulfilled","completed","published"}: raise HTTPException(403,"Automations cannot approve, pay, refund, fulfill or publish records")
        target.status=next_status;target.version+=1;target.updated_by=member.subject
    elif action=="create_approval":
        approval=BusinessRecord(tenant_id=member.tenant_id,kind="approvals",payload={"request":f"Automation approval: {target.title}","requested_by":member.display_name,"approver":workflow.data.get("approver",""),"status":"pending","amount":0,"branch_id":str(target.branch_id or ""),"target_kind":target_kind,"target_id":str(target.id),"note":body.note,"workflow_id":str(workflow.id)},created_by=member.subject)
        db.add(approval)
    else: raise HTTPException(422,"Workflow action is not configured")
    run=WorkspaceResource(tenant_id=member.tenant_id,kind="workflow_runs",title=workflow.title,status="succeeded",branch_id=target.branch_id,data={"target_kind":target_kind,"target_id":str(target.id),"action_type":action,"note":body.note,"workflow_id":str(workflow.id)},created_by=member.subject,updated_by=member.subject)
    db.add(run);db.flush();result=_output(run)
    _audit(db,member,request,"workspace.workflow_run_succeeded","workflow_run",run.id,{"workflow_id":str(workflow.id),"target_kind":target_kind,"target_id":str(target.id),"action_type":action})
    db.add(IdempotencyKey(tenant_id=member.tenant_id,key=idempotency_key,request_hash=_hash(command),result=result));db.commit();return result

@router.post("/assistant/ask")
def assistant_ask(body:AssistantRequest,db:Session=Depends(get_db),member:Membership=Depends(membership)):
    permitted=[]
    for kind in body.sources:
        if kind not in KINDS or member.role not in KIND_ROLES[kind]: raise HTTPException(403,"One or more requested sources are not available to this role")
        permitted.append(kind)
    words={word.lower().strip(".,?!") for word in body.question.split() if len(word)>2}
    rows=db.scalars(select(WorkspaceResource).where(WorkspaceResource.tenant_id==member.tenant_id,WorkspaceResource.kind.in_(permitted)).order_by(WorkspaceResource.updated_at.desc()).limit(300))
    matches=[]
    for row in rows:
        if member.role not in MANAGE and row.branch_id and str(row.branch_id) not in member.branch_ids: continue
        if row.kind=="documents" and member.role not in MANAGE and row.created_by!=member.subject: continue
        if row.kind=="timesheets" and member.role=="Employee" and row.created_by!=member.subject: continue
        haystack=(row.title+" "+json.dumps(row.data,default=str)).lower()
        score=sum(1 for word in words if word in haystack)
        if score: matches.append((score,row))
    matches.sort(key=lambda pair:(pair[0],pair[1].updated_at),reverse=True)
    sources=[{"kind":row.kind,"id":str(row.id),"title":row.title,"status":row.status,"updated_at":row.updated_at.isoformat()} for _,row in matches[:5]]
    if not sources:
        return {"answer":"I could not find a matching record in the selected workspace sources. No outside data or AI provider was used.","sources":[],"mode":"local_search"}
    return {"answer":f"Found {len(sources)} matching workspace record(s). Review the linked records for full details; this local assistant only searches titles and record fields and does not make decisions.","sources":sources,"mode":"local_search"}
