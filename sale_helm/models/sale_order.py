import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_name = fields.Char(inverse="_inverse_project_name")
    custom_domain = fields.Char()
    consulting_partner_id = fields.Many2one("res.partner", domain="[('helm_product_ids','!=',False)]")
    cluster_id = fields.Many2one("kubectl.cluster")
    chart_ids = fields.One2many("helm.chart", compute="_compute_chart_ids")
    release_ids = fields.Many2many("helm.release", compute="_compute_release_ids", store=True)
    release_count = fields.Integer(string="Releases", compute="_compute_release_ids", store=True)

    @api.depends("order_line.product_id", "order_line.release_ids")
    def _compute_release_ids(self):
        for order in self:
            order.release_ids = order.order_line.mapped("release_ids")
            order.release_count = len(order.release_ids)

    def _compute_chart_ids(self):
        for rec in self:
            rec.chart_ids = rec.order_line.product_id.chart_id

    def _inverse_project_name(self):
        """
        Ensure project name is alphanumerical.
        """
        for rec in self:
            if rec.project_name:
                if not rec.project_name.isalnum():
                    raise ValidationError(_("Project name must only contain alphanumeric characters."))

    def action_confirm(self):
        """
        For each order line with a chart, create and install a release.
        """
        res = super().action_confirm()
        for order in self.filtered("chart_ids"):
            # Validate required fields for Helm deployment
            if not order.cluster_id:
                raise ValidationError(_("Cluster is required for Helm chart deployment."))
            if not order.project_name:
                raise ValidationError(_("Project name is required for Helm chart deployment."))

            for line in order.order_line:
                release_values = {
                    "name": line.product_id.chart_id.name,
                    "sale_line_id": line.id,
                    "namespace": order.project_name,
                    "create_namespace": True,
                    "cluster_id": order.cluster_id.id,
                    "product_id": line.product_id.id,
                    "partner_id": order.partner_id.id,
                }
                release_id = line.product_id.chart_id.create_release(release_values)
                release_id.action_install()
        return res

    def action_view_release(self):
        self.ensure_one()
        return {
            "name": "Releases",
            "type": "ir.actions.act_window",
            "res_model": "helm.release",
            "view_mode": "list,form",
            "domain": [("id", "in", self.release_ids.ids)],
            "target": "current",
        }
