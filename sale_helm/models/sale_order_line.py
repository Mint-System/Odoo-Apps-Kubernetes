import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    release_ids = fields.One2many("helm.release", "sale_line_id", string="Releases")
