import hashlib
import hmac
import json
import os
import time
from odoo import http
from odoo.http import request

class NexoraGateway(http.Controller):
    """Private signed endpoint. Install this addon in each tenant database."""

    @http.route("/nexora/gateway/command", type="http", auth="public", methods=["POST"], csrf=False, save_session=False)
    def command(self, **_kwargs):
        raw = request.httprequest.get_data(cache=True)
        timestamp = request.httprequest.headers.get("X-Nexora-Timestamp", "")
        request_id = request.httprequest.headers.get("X-Nexora-Request-ID", "")
        signature = request.httprequest.headers.get("X-Nexora-Signature", "")
        key = request.httprequest.headers.get("Idempotency-Key", "")
        secret = os.environ.get("ODOO_GATEWAY_SECRET", "").encode()
        if not secret or not key or not request_id:
            return request.make_json_response({"error":"Gateway authentication headers are required"}, status=401)
        try:
            if abs(int(timestamp) - int(time.time())) > 60:
                return request.make_json_response({"error":"Request timestamp expired"}, status=401)
        except ValueError:
            return request.make_json_response({"error":"Invalid request timestamp"}, status=401)
        # Bind signatures to this database so a captured request cannot replay
        # against another tenant database using the shared gateway secret.
        database = request.env.cr.dbname.encode()
        signed = timestamp.encode() + b"." + database + b"." + request_id.encode() + b"." + key.encode() + b"." + raw
        expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return request.make_json_response({"error":"Invalid gateway signature"}, status=401)
        try:
            body = json.loads(raw)
            durable = body.get("operation") not in ("health", "records.list")
            fingerprint = hashlib.sha256(raw).hexdigest()
            if durable:
                prior = request.env["nexora.gateway.request"].sudo().search([("request_key", "=", key)], limit=1)
                if prior:
                    receipt = prior.response_json
                    if receipt.get("_nexora_receipt_v1") is not True or not hmac.compare_digest(receipt.get("request_hash", ""), fingerprint):
                        return request.make_json_response({"error":"Idempotency key was already used for a different or legacy request"}, status=409)
                    return request.make_json_response(receipt["response"])
            # Failed business commands must not commit earlier ORM changes
            # (for example partial stock reservations before validation fails).
            with request.env.cr.savepoint():
                result = self._execute(body)
            if durable:
                request.env["nexora.gateway.request"].sudo().create({"request_key":key,"response_json":{"_nexora_receipt_v1":True,"request_hash":fingerprint,"response":result}})
            return request.make_json_response(result)
        except ValueError as error:
            return request.make_json_response({"error":str(error)}, status=422)

    def _execute(self, body):
        operation = body.get("operation")
        payload = body.get("payload") or {}
        env = request.env
        if operation == "health":
            return {"status":"ok","database":env.cr.dbname,"odoo_version":env["ir.module.module"].sudo().search([("name","=","base")],limit=1).installed_version}
        if operation == "company.configure":
            company=env.company.sudo()
            company.write({"name":self._required(payload,"name")})
            return {"id":company.id,"name":company.name,"status":"configured"}
        if operation == "lead.create":
            record = env["crm.lead"].sudo().create({"name":self._required(payload,"name"),"contact_name":payload.get("contact_name"),"email_from":payload.get("email"),"phone":payload.get("phone"),"expected_revenue":float(payload.get("expected_revenue") or 0)})
            return {"id":record.id,"name":record.name,"status":"new"}
        if operation == "lead.stage":
            lead=env["crm.lead"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not lead: raise ValueError("CRM lead not found")
            stage_name={"proposal":"Proposition","won":"Won","qualified":"Qualified"}.get(payload.get("status"),payload.get("status"))
            if payload.get("status")=="lost":
                lead.action_set_lost()
            else:
                stage=env["crm.stage"].sudo().search([("name","ilike",stage_name)],limit=1)
                if not stage: raise ValueError("The requested CRM stage is not configured")
                lead.stage_id=stage
            return {"id":lead.id,"name":lead.name,"status":payload.get("status")}
        if operation == "customer.create":
            record = env["res.partner"].sudo().create({"name":self._required(payload,"name"),"email":payload.get("email"),"phone":payload.get("phone"),"company_type":"company" if payload.get("is_company",True) else "person","customer_rank":1})
            return {"id":record.id,"name":record.name,"status":"active"}
        if operation == "supplier.create":
            record=env["res.partner"].sudo().create({"name":self._required(payload,"name"),"email":payload.get("email"),"phone":payload.get("phone"),"company_type":"company","supplier_rank":1})
            return {"id":record.id,"name":record.name,"status":"active"}
        if operation == "product.create":
            record = env["product.template"].sudo().create({"name":self._required(payload,"name"),"default_code":payload.get("sku"),"list_price":float(payload.get("sale_price") or 0),"standard_price":float(payload.get("cost") or 0),"type":"consu"})
            return {"id":record.product_variant_id.id,"template_id":record.id,"name":record.name,"sku":record.default_code,"status":"active"}
        if operation == "product.stock.adjust":
            product=env["product.product"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not product: raise ValueError("Product not found")
            warehouse=env["stock.warehouse"].sudo().search([("company_id","=",env.company.id)],order="id",limit=1)
            if not warehouse or not warehouse.lot_stock_id: raise ValueError("The workspace has no internal stock location")
            quantity=float(self._required(payload,"quantity"))
            if quantity<0: raise ValueError("Counted stock cannot be negative")
            quant_model=env["stock.quant"].sudo().with_context(inventory_mode=True)
            domain=[("product_id","=",product.id),("location_id","=",warehouse.lot_stock_id.id),("lot_id","=",False),("package_id","=",False),("owner_id","=",False)]
            quant=quant_model.search(domain,limit=1)
            if quant:
                quant.inventory_quantity=quantity
            else:
                quant=quant_model.create({"product_id":product.id,"location_id":warehouse.lot_stock_id.id,"inventory_quantity":quantity})
            quant.action_apply_inventory()
            env.flush_all();product.invalidate_recordset()
            return {"id":product.id,"name":product.display_name,"quantity":product.qty_available,"location":warehouse.lot_stock_id.display_name,"reason":self._required(payload,"reason")}
        if operation == "sale.quote.create":
            order = env["sale.order"].sudo().create({"partner_id":int(self._required(payload,"partner_id")),"client_order_ref":payload.get("reference"),"order_line":[(0,0,self._sale_line(line)) for line in payload.get("lines",[])]})
            return {"id":order.id,"name":order.name,"status":"draft","amount_total":order.amount_total}
        if operation == "sale.confirm":
            order=env["sale.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order: raise ValueError("Sales order not found")
            order.action_confirm()
            return {"id":order.id,"name":order.name,"status":"confirmed","amount_total":order.amount_total}
        if operation == "sale.deliver":
            from odoo.tools.float_utils import float_compare
            order=env["sale.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order or order.state not in ("sale","done"): raise ValueError("Only confirmed sales orders can be delivered")
            outgoing=order.picking_ids.filtered(lambda picking: picking.picking_type_id.code=="outgoing")
            if not outgoing: raise ValueError("The sales order has no outgoing delivery")
            open_pickings=outgoing.filtered(lambda picking: picking.state not in ("done","cancel"))
            if not open_pickings:
                if all(picking.state=="done" for picking in outgoing):
                    return {"id":order.id,"name":order.name,"status":"delivered","deliveries":[picking.name for picking in outgoing]}
                raise ValueError("The sales order delivery is cancelled")
            for picking in open_pickings:
                picking.action_assign()
                incomplete=picking.move_ids.filtered(lambda move: move.state not in ("done","cancel") and float_compare(move.quantity,move.product_uom_qty,precision_rounding=move.product_uom.rounding)<0)
                if incomplete:
                    missing=[f"{move.product_id.display_name}: {move.product_uom_qty-move.quantity:g} {move.product_uom.name}" for move in incomplete]
                    raise ValueError("Insufficient reserved stock to deliver the full order: "+", ".join(missing[:20]))
                result=picking.button_validate()
                if isinstance(result,dict) and result.get("res_model")=="stock.immediate.transfer":
                    env["stock.immediate.transfer"].sudo().browse(result["res_id"]).process()
                elif isinstance(result,dict) and result.get("res_model")=="stock.backorder.confirmation":
                    raise ValueError("Odoo requested a backorder; review this delivery in the Odoo interface")
                if picking.state!="done": raise ValueError("Odoo did not complete the full delivery")
            return {"id":order.id,"name":order.name,"status":"delivered","deliveries":[picking.name for picking in outgoing]}
        if operation == "sale.cancel":
            order=env["sale.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order: raise ValueError("Sales order not found")
            order.action_cancel()
            return {"id":order.id,"name":order.name,"status":"cancelled","amount_total":order.amount_total}
        if operation == "sale.invoice.create":
            order=env["sale.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order or order.state not in ("sale","done"): raise ValueError("Only confirmed sales orders can be invoiced")
            invoices=order._create_invoices()
            if not invoices: raise ValueError("The sales order has no invoiceable quantities")
            return {"id":order.id,"name":order.name,"status":"invoiced","invoices":[{"id":move.id,"name":move.name,"partner_id":move.partner_id.id,"partner_name":move.partner_id.display_name,"move_type":move.move_type,"currency":move.currency_id.name,"invoice_date_due":move.invoice_date_due.isoformat() if move.invoice_date_due else "","state":move.state,"amount_total":move.amount_total,"lines":[{"product_id":line.product_id.id,"quantity":line.quantity,"unit_price":line.price_unit,"description":line.name} for line in move.invoice_line_ids if line.product_id]} for move in invoices]}
        if operation == "purchase.order.create":
            order=env["purchase.order"].sudo().create({"partner_id":int(self._required(payload,"partner_id")),"origin":payload.get("reference"),"order_line":[(0,0,{"product_id":int(self._required(line,"product_id")),"product_qty":float(line.get("quantity") or 1),"price_unit":float(line.get("unit_price") or 0),"name":line.get("description") or ""}) for line in payload.get("lines",[])]})
            return {"id":order.id,"name":order.name,"status":"draft","amount_total":order.amount_total}
        if operation == "purchase.confirm":
            order=env["purchase.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order: raise ValueError("Purchase order not found")
            order.button_confirm()
            return {"id":order.id,"name":order.name,"status":"confirmed","amount_total":order.amount_total}
        if operation == "purchase.cancel":
            order=env["purchase.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order: raise ValueError("Purchase order not found")
            order.button_cancel()
            return {"id":order.id,"name":order.name,"status":"cancelled","amount_total":order.amount_total}
        if operation == "purchase.receive":
            order=env["purchase.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order: raise ValueError("Purchase order not found")
            pickings=order.picking_ids.filtered(lambda picking: picking.state not in ("done","cancel"))
            if not pickings: raise ValueError("No open receipt exists for this purchase order")
            for picking in pickings:
                picking.action_assign()
                for move_line in picking.move_line_ids:
                    move_line.quantity=move_line.reserved_uom_qty
                result=picking.button_validate()
                if isinstance(result,dict) and result.get("res_model")=="stock.immediate.transfer":
                    env[result["res_model"]].sudo().browse(result["res_id"]).process()
                elif isinstance(result,dict) and result.get("res_model")=="stock.backorder.confirmation":
                    env[result["res_model"]].sudo().browse(result["res_id"]).process()
                if picking.state!="done": raise ValueError("Receipt is incomplete; confirm all quantities first")
            return {"id":order.id,"name":order.name,"status":"received","amount_total":order.amount_total}
        if operation == "purchase.bill.create":
            order=env["purchase.order"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not order or order.state not in ("purchase","done"): raise ValueError("Only confirmed purchase orders can be billed")
            if order.invoice_status=="invoiced": raise ValueError("The purchase order is already fully billed")
            prior_bill_ids=set(order.invoice_ids.ids)
            order.action_create_invoice()
            order.invalidate_recordset(["invoice_ids"])
            bills=order.invoice_ids.filtered(lambda move: move.id not in prior_bill_ids)
            if not bills: raise ValueError("The purchase order has no billable quantities")
            return {"id":order.id,"name":order.name,"status":"billed","bills":[{"id":move.id,"name":move.name,"partner_id":move.partner_id.id,"partner_name":move.partner_id.display_name,"move_type":move.move_type,"currency":move.currency_id.name,"invoice_date_due":move.invoice_date_due.isoformat() if move.invoice_date_due else "","state":move.state,"amount_total":move.amount_total,"lines":[{"product_id":line.product_id.id,"quantity":line.quantity,"unit_price":line.price_unit,"description":line.name} for line in move.invoice_line_ids if line.product_id]} for move in bills]}
        if operation == "invoice.create":
            move=env["account.move"].sudo().create({"move_type":payload.get("move_type","out_invoice"),"partner_id":int(self._required(payload,"partner_id")),"invoice_line_ids":[(0,0,{"product_id":int(self._required(line,"product_id")),"quantity":float(line.get("quantity") or 1),"price_unit":float(line.get("unit_price") or 0),"name":line.get("description") or ""}) for line in payload.get("lines",[])]})
            return {"id":move.id,"name":move.name,"status":"draft","amount_total":move.amount_total,"currency":move.currency_id.name}
        if operation == "invoice.post":
            move=env["account.move"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not move: raise ValueError("Invoice not found")
            move.action_post()
            return {"id":move.id,"name":move.name,"status":"posted","amount_total":move.amount_total}
        if operation == "invoice.cancel":
            move=env["account.move"].sudo().browse(int(self._required(payload,"odoo_id"))).exists()
            if not move: raise ValueError("Invoice not found")
            if move.state=="posted": raise ValueError("Posted invoice reversal requires the accounting reversal workflow")
            move.button_cancel()
            return {"id":move.id,"name":move.name,"status":"cancelled","amount_total":move.amount_total}
        if operation == "record.update":
            kind=self._required(payload,"kind");record_id=int(self._required(payload,"odoo_id"));data=payload.get("record") or {}
            if kind=="leads":
                record=env["crm.lead"].sudo().browse(record_id).exists()
                if not record: raise ValueError("CRM lead not found")
                record.write({"name":data.get("lead",record.name),"contact_name":data.get("contact",record.contact_name),"email_from":data.get("email",record.email_from),"phone":data.get("phone",record.phone),"expected_revenue":float(data.get("value") or record.expected_revenue)})
            elif kind in ("customers","suppliers"):
                record=env["res.partner"].sudo().browse(record_id).exists()
                if not record: raise ValueError("Contact not found")
                record.write({"name":data.get("customer" if kind=="customers" else "supplier",record.name),"email":data.get("email",record.email),"phone":data.get("phone",record.phone)})
            elif kind=="inventory":
                record=env["product.product"].sudo().browse(record_id).exists()
                if not record: raise ValueError("Product not found")
                record.product_tmpl_id.write({"name":data.get("product",record.name),"default_code":data.get("sku",record.default_code),"list_price":float(data.get("sale_price") or record.lst_price),"standard_price":float(data.get("cost") or record.standard_price)})
            elif kind=="sales":
                record=env["sale.order"].sudo().browse(record_id).exists()
                if not record or record.state not in ("draft","sent"): raise ValueError("Only draft quotations can be edited")
                values={"partner_id":int(self._required(data,"partner_id")),"client_order_ref":data.get("document",record.client_order_ref)}
                if data.get("lines"): values["order_line"]=[(5,0,0)]+[self._sale_line(line) for line in data["lines"]]
                record.write(values)
            elif kind=="purchasing":
                record=env["purchase.order"].sudo().browse(record_id).exists()
                if not record or record.state not in ("draft","sent"): raise ValueError("Only draft purchase orders can be edited")
                values={"partner_id":int(self._required(data,"partner_id")),"origin":data.get("purchase_order",record.origin)}
                if data.get("lines"): values["order_line"]=[(5,0,0)]+[(0,0,{"product_id":int(self._required(line,"product_id")),"product_qty":float(line.get("quantity") or 1),"price_unit":float(line.get("unit_price") or 0),"name":line.get("description") or ""}) for line in data["lines"]]
                record.write(values)
            elif kind=="finance":
                record=env["account.move"].sudo().browse(record_id).exists()
                if not record or record.state!="draft": raise ValueError("Only draft invoices or bills can be edited")
                values={"partner_id":int(self._required(data,"partner_id")),"invoice_date_due":data.get("due_date") or False,"move_type":data.get("move_type",record.move_type)}
                if data.get("lines"): values["invoice_line_ids"]=[(5,0,0)]+[(0,0,{"product_id":int(self._required(line,"product_id")),"quantity":float(line.get("quantity") or 1),"price_unit":float(line.get("unit_price") or 0),"name":line.get("description") or ""}) for line in data["lines"]]
                record.write(values)
            else: raise ValueError("This Odoo record cannot be edited through the gateway")
            return {"id":record.id,"name":getattr(record,"name",record.display_name),"status":getattr(record,"state","active"),"amount_total":getattr(record,"amount_total",0)}
        if operation == "records.list":
            models={"leads":("crm.lead",["name","contact_name","email_from","phone","stage_id","expected_revenue"]),"customers":("res.partner",["name","email","phone","credit","company_type"]),"suppliers":("res.partner",["name","email","phone","supplier_rank"]),"sales":("sale.order",["name","partner_id","date_order","state","invoice_status","amount_total"]),"purchasing":("purchase.order",["name","partner_id","date_order","state","amount_total"]),"inventory":("product.product",["name","default_code","qty_available","virtual_available","list_price"]),"finance":("account.move",["name","partner_id","move_type","invoice_date_due","state","amount_total","currency_id"])}
            kind=payload.get("kind"); config=models.get(kind)
            if not config: raise ValueError("Unsupported Odoo list kind")
            ids=[int(x) for x in payload.get("ids",[])]
            records=env[config[0]].sudo().browse(ids).exists()
            return {"records":[{"odoo_id":record.id,**record.read(config[1])[0]} for record in records]}
        raise ValueError("Unsupported Odoo operation")

    @staticmethod
    def _required(payload, name):
        value=payload.get(name)
        if value in (None, "", []): raise ValueError(f"Missing required field: {name}")
        return value

    def _sale_line(self, line):
        values={"product_uom_qty":float(line.get("quantity") or 1),"price_unit":float(line.get("unit_price") or 0)}
        if line.get("product_id"): values["product_id"]=int(line["product_id"])
        if line.get("description"): values["name"]=line["description"]
        return (0,0,values)
