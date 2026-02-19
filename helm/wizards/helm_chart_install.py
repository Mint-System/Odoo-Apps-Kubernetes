from odoo import api, fields, models


class HelmChartInstall(models.TransientModel):
    _name = "helm.chart.install"
    _description = "Helm Chart Install"

    name = fields.Char(string="Release Name", required=True)
    chart_id = fields.Many2one("helm.chart", required=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "chart_id" in fields and "name" in fields and self._context.get("active_id"):
            chart = self.env["helm.chart"].browse(self._context["active_id"])
            res["name"] = chart.name
        return res

    cluster_id = fields.Many2one("kubectl.cluster", required=True)
    create_namespace = fields.Boolean()
    namespace = fields.Char(help="Namespace with this input will be created.")
    namespace_id = fields.Many2one("kubectl.namespace", string="Linked Namespace", help="Target namespace in cluster.")
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)

    def action_confirm(self):
        """
        Create a kubectl.release record and open it.
        """
        for wizard in self:
            release_id = self.chart_id.create_release(
                {
                    "name": wizard.name,
                    "cluster_id": wizard.cluster_id.id,
                    "create_namespace": wizard.create_namespace,
                    "namespace": wizard.namespace,
                    "namespace_id": wizard.namespace_id.id,
                    "partner_id": wizard.partner_id.id,
                }
            )
            return {
                "name": "Release",
                "type": "ir.actions.act_window",
                "res_model": "helm.release",
                "res_id": release_id.id,
                "view_mode": "form",
                "target": "current",
            }
