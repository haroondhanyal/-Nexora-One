import hashlib, hmac, os, secrets
import httpx
from fastapi import HTTPException

BASE = os.getenv("ODOO_BASE_URL", "http://localhost:8069").rstrip("/")
MASTER = os.getenv("ODOO_MASTER_PASSWORD", "")

def install_tenant_database(database: str, company_name: str, country_code: str = "pk") -> None:
    """Create an isolated Odoo database and install the signed Nexora gateway."""
    if not MASTER: raise HTTPException(503,"Odoo provisioning is not configured")
    login="admin"
    password=hmac.new(MASTER.encode(),database.encode(),hashlib.sha256).hexdigest()
    try:
        with httpx.Client(timeout=120, follow_redirects=False) as client:
            # Odoo parses form booleans by truthiness. The string "false" is
            # truthy, so omit demo entirely to avoid seeding demo records.
            created=client.post(f"{BASE}/web/database/create", data={"master_pwd":MASTER,"name":database,"login":login,"password":password,"lang":"en_US","country_code":country_code,"phone":""})
            # Provisioning can be retried after a worker crash. A deterministic,
            # server-only admin secret lets the retry resume an existing tenant DB.
            if created.status_code not in {200,302,303}:
                raise RuntimeError("Odoo rejected database creation")
            auth=client.post(f"{BASE}/web/session/authenticate?db={database}", json={"jsonrpc":"2.0","method":"call","params":{"db":database,"login":login,"password":password},"id":1})
            if auth.status_code!=200 or not auth.json().get("result",{}).get("uid"):
                raise RuntimeError("Odoo database login failed")
            def call(model, method, args=None, kwargs=None):
                response=client.post(f"{BASE}/web/dataset/call_kw/{model}/{method}?db={database}",json={"jsonrpc":"2.0","method":"call","params":{"model":model,"method":method,"args":args or [],"kwargs":kwargs or {}},"id":1})
                response.raise_for_status();result=response.json()
                if result.get("error"): raise RuntimeError("Odoo module setup failed")
                return result.get("result")
            call("ir.module.module","update_list")
            modules=call("ir.module.module","search_read",[[["name","=","nexora_gateway"]]],{"fields":["id","state"],"limit":1})
            if not modules: raise RuntimeError("Nexora gateway addon is not available in Odoo")
            module=modules[0]
            if module["state"]!="installed": call("ir.module.module","button_immediate_install",[[module["id"]]])
            # Install keeps Odoo's own transaction; gateway command configures company details.
            gateway_command(database,{"operation":"company.configure","payload":{"name":company_name}},secrets.token_urlsafe(24))
    except HTTPException: raise
    except (httpx.HTTPError, ValueError, RuntimeError):
        raise HTTPException(502,"Odoo tenant setup failed. Check Odoo health and review the provisioning status.") from None

def gateway_command(database: str, body: dict, idempotency_key: str) -> dict:
    import hashlib, hmac, json, time, uuid
    secret=os.environ.get("ODOO_GATEWAY_SECRET","").encode()
    if not secret: raise HTTPException(503,"Odoo gateway signing key is not configured")
    raw=json.dumps(body,separators=(",",":"),ensure_ascii=False).encode();timestamp=str(int(time.time()));request_id=str(uuid.uuid4())
    # Bind each signature to its tenant database to prevent cross-database replay.
    signature=hmac.new(secret,timestamp.encode()+b"."+database.encode()+b"."+request_id.encode()+b"."+idempotency_key.encode()+b"."+raw,hashlib.sha256).hexdigest()
    try:
        response=httpx.post(f"{BASE}/nexora/gateway/command",params={"db":database},content=raw,headers={"Content-Type":"application/json","X-Nexora-Timestamp":timestamp,"X-Nexora-Request-ID":request_id,"X-Nexora-Signature":signature,"Idempotency-Key":idempotency_key},timeout=30)
    except httpx.HTTPError: raise HTTPException(502,"Odoo gateway is unavailable") from None
    if response.status_code>=400: raise HTTPException(502,"Odoo rejected the business command")
    result=response.json()
    if result.get("error"): raise HTTPException(422,result["error"])
    return result
