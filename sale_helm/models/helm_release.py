import logging

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class HelmRelease(models.Model):
    _inherit = "helm.release"

    sale_line_id = fields.Many2one("sale.order.line", string="Sale Order Line")

    def _eval_value(self, expression):
        """
        Add order_id to context.
        """
        order_id = self.sale_line_id.order_id if self.sale_line_id else False
        if order_id:
            return safe_eval(
                expression,
                {
                    "self": self,
                    "release": self,
                    "release_id": self,
                    "generate_password": self.generate_password,
                    "order": order_id,
                    "order_id": order_id,
                },
            )
        else:
            return super()._eval_value(expression)
