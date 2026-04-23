import logging
import subprocess

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class KubectlNamespace(models.Model):
    _name = "kubectl.namespace"
    _description = "Kubectl Namespace"
    _inherit = ["kubernetes.resource"]
    _kubernetes_resource = "namespace"

    display_name = fields.Char(compute="_compute_display_name", store=True)
    cluster_id = fields.Many2one("kubectl.cluster", required=True)

    _sql_constraints = [
        (
            "unique_name_by_cluster_id",
            "UNIQUE(name, cluster_id)",
            "Namespace must be unique per cluster.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("uid"):
                self._create_namespace(vals)
        return super().create(vals_list)

    def _create_namespace(self, vals_list):
        """
        Kubernetes API wrapper.
        Create Kubernetes namespace.
        """
        for vals in vals_list:
            if vals.get("name") and vals.get("cluster_id"):
                try:
                    command = [
                        "kubectl",
                        "create",
                        "namespace",
                        vals.get("name"),
                    ]
                    cluster_id = self.env["kubectl.cluster"].browse(vals.get("cluster_id"))
                    result = cluster_id.context_id.run(command)
                    _logger.info(f"Created namespace {self.namespace} in cluster {cluster_id.name}")
                except subprocess.CalledProcessError as e:
                    _logger.error(f"Failed to create namespace {self.namespace}: {e.stderr}")

    @api.model
    def get_or_create(self, values):
        namespace_id = self.search(
            [
                ("name", "=", values["name"]),
                ("cluster_id", "=", values["cluster_id"]),
            ]
        )
        if namespace_id:
            return namespace_id
        else:
            return self.create(values)

    @api.depends("name", "cluster_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} ({rec.cluster_id.name})"
