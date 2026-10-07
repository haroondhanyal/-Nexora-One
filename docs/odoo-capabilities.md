# Odoo capability map

Local development pins Odoo 19 Community and mounts `nexora_gateway` into each provisioned tenant database. This is a development implementation; validate the exact image, addon and accounting behavior before production use. Odoo external JSON-2 has subscription restrictions, so Nexora calls its own signed controller and supported ORM methods instead.

| Feature | Required model/module | Edition | Custom addon | License/dependency | Integration method | Status |
|---|---|---|---|---|---|---|
| CRM and sales | `crm.lead`, `res.partner`, `sale.order`, `stock.picking`, `account.move` | Community | `nexora_gateway` | Odoo LGPL-3; deployment addons to verify | Signed ORM create/update/confirm/full-stock delivery/invoice/cancel | Partial; delivery refuses incomplete reservations/backorders; runtime verification pending |
| Inventory and purchasing | `product.product`, `stock.quant`, `purchase.order`, `stock.picking`, `account.move` | Community | `nexora_gateway` | Odoo LGPL-3; deployment addons to verify | Signed ORM product/count-adjustment/PO/receipt/vendor-bill methods | Partial; physical count is implemented against the default location and received POs can create draft vendor bills; reservations/transfers and runtime verification pending |
| Accounting and reconciliation | `account.move`, account payment models | Community | `nexora_gateway` | Verify localization and chart requirements | Signed ORM draft/post/cancel transaction | Partial; provider events and reconciliation not implemented |
| HR and attendance | Control-plane models; possible Odoo employee/attendance extension | Community base; addon not yet mapped | Not yet integrated | Verify if/when Odoo-backed | Tenant-scoped FastAPI HR routes today | Partial; vendor device adapter and production review pending |
| Payroll | Control-plane compensation, payroll run and payslip models | Nexora limited calculation; no Odoo payroll claim | Nexora control-plane implementation | Statutory rules remain unimplemented | Effective-dated monthly components with calendar-day proration; prepared/approved/released | Partial; attendance-based rules, statutory tax/benefits and payroll execution remain unimplemented |
| Projects and services | To verify against pinned release | Undecided | Possible gateway extensions | To verify | Supported Odoo business methods | Not implemented |

Never assume Community includes Enterprise capabilities. Do not write directly into Odoo business tables using SQL. Keep each atomic posting inside a single Odoo-side transaction.
