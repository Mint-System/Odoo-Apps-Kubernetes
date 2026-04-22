import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class KubectlCluster(models.Model):
    _name = "kubectl.cluster"
    _description = "Kubectl Cluster"
    _resource = "cluster"

    display_name = fields.Char(compute="_compute_display_name")

    name = fields.Char(required=True)
    alias = fields.Char(required=True)
    server = fields.Char(required=True)
    domain = fields.Char(required=True)

    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    context_ids = fields.One2many("kubectl.context", "cluster_id")
    context_id = fields.Many2one("kubectl.context", string="Default Context")

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} ({rec.alias})"

    def action_show_contexts(self):
        """
        Open the list view of contexts for this cluster.
        """
        self.ensure_one()
        return {
            "name": "Contexts",
            "type": "ir.actions.act_window",
            "res_model": "kubectl.context",
            "view_mode": "list,form",
            "target": "current",
        }
