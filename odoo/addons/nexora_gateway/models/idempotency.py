from odoo import fields, models

class NexoraGatewayRequest(models.Model):
    _name = "nexora.gateway.request"
    _description = "Nexora Gateway Idempotency Receipt"
    _order = "create_date desc"

    request_key = fields.Char(required=True, index=True)
    response_json = fields.Json(required=True)
    _sql_constraints = [("request_key_unique", "unique(request_key)", "Gateway request keys must be unique.")]
