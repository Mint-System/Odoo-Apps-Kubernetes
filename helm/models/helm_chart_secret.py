# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import subprocess

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class HelmChartSecret(models.Model):
    _name = "helm.chart.secret"
    _description = "Helm Chart Secret"
    _inherit = ["kubernetes.resource"]
    _kubernetes_resource = "secret"

    chart_id = fields.Many2one("helm.chart", ondelete="cascade")
    release_id = fields.Many2one("helm.release", ondelete="cascade")
    data_ids = fields.One2many("helm.chart.secret.data", "secret_id")

    def copy(self, default=None):
        new_secret = super().copy(default=default)
        for data in self.data_ids:
            data.copy({"secret_id": new_secret.id})
        return new_secret

    def _create_secret(self, release_id):
        """
        Kubernetes API wrapper.
        Create Kubernetes secrets for a release.
        """

        for secret in self:
            secret_data = ""
            for data in secret.data_ids:
                try:
                    evaluated_value = release_id._eval_value(data.value)
                    secret_data += f"{data.key}={evaluated_value}\n"
                except Exception as e:
                    _logger.error(f"Error evaluating secret value {data.value}: {str(e)}")
                    continue

            if not secret_data:
                continue

            # Create secret using kubectl
            try:
                # Create secret from literal values
                command = [
                    "kubectl",
                    "create",
                    "secret",
                    "generic",
                    secret.name,
                    "--namespace",
                    release_id.namespace_id.name,
                    "--from-literal=" + secret_data.strip().replace("\n", " --from-literal="),
                ]
                result = release_id.cluster_id.context_id.run(command)
                _logger.info(f"Created secret {secret.name} in namespace {release_id.namespace_id.name}")
            except subprocess.CalledProcessError as e:
                _logger.error(f"Failed to create secret {secret.name}: {e.stderr}")

    def _delete_secret(self, release_id):
        """
        Kubernetes API wrapper.
        Delete Kubernetes secrets for a release.
        """

        for secret in self:
            try:
                # Delete secret using kubectl
                command = [
                    "kubectl",
                    "delete",
                    "secret",
                    secret.name,
                    "--namespace",
                    release_id.namespace_id.name,
                    "--ignore-not-found=true",  # Don't fail if secret doesn't exist
                ]
                result = release_id.cluster_id.context_id.run(command)
                _logger.info(f"Deleted secret {secret.name} from namespace {release_id.namespace_id.name}")
            except subprocess.CalledProcessError as e:
                _logger.error(f"Failed to delete secret {secret.name}: {e.stderr}")

    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref("helm.helm_chart_secret_form_view")
        return {
            "name": _("Secret Data"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "helm.chart.secret",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
        }
