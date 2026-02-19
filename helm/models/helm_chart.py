import logging
import subprocess

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HelmChart(models.Model):
    _name = "helm.chart"
    _description = "Helm Chart"

    name = fields.Char(required=True)
    state = fields.Selection(related="repo_id.state")

    repo_id = fields.Many2one("helm.repo", required=True)
    product_ids = fields.One2many("product.product", "chart_id", domain=[("type", "=", "service")])

    values = fields.Text(compute="_compute_values", string="Chart values.yaml")
    value_ids = fields.One2many(
        "helm.chart.value",
        "chart_id",
        string="Dynamic values",
        help="These values will be computed and applied to the release values.",
    )
    release_value_ids = fields.One2many(
        "helm.chart.value",
        "release_chart_id",
        domain=[("release_id", "=", False)],
        string="Predefined values",
        help="These values will be copied to the release and can be updated.",
    )
    secret_ids = fields.One2many(
        "helm.chart.secret",
        "chart_id",
    )

    def _compute_values(self):
        for chart in self:
            if chart.state == "added":
                try:
                    result = subprocess.run(
                        [
                            "helm",
                            "show",
                            "values",
                            f"{chart.repo_id.name}/{chart.name}",
                        ],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    chart.values = result.stdout
                except subprocess.CalledProcessError as e:
                    chart.values = e.stderr
            else:
                chart.values = ""

    @api.depends("release_value_ids.release_id")
    def _compute_release_count(self):
        for chart in self:
            chart.release_count = self.env["helm.release"].search_count([("chart_id", "=", chart.id)])

    def create_release(self, values):
        """
        Create release from chart. Select the first context of the cluster.
        Copy the updateabel values and secrets.
        """
        self.ensure_one()

        # Set defaults
        values["chart_id"] = self.id

        # Copy values
        release_value_ids = self.release_value_ids.copy()
        secret_ids = self.secret_ids.copy()

        # Create release record
        release_id = self.env["helm.release"].create(values)

        # Update copied values
        release_value_ids.write({"chart_id": False, "release_id": release_id.id})
        secret_ids.write({"chart_id": False, "release_id": release_id.id})

        # Evaluate expressions in copied values
        for value in release_value_ids:
            if value.value and value.value.strip():
                try:
                    # Evaluate the expression and store the result
                    evaluated_value = release_id._eval_value(value.value)
                    value.value = str(evaluated_value)
                except Exception as e:
                    _logger.error(f"Error evaluating value {value.value}: {str(e)}")
                    # Keep original value if evaluation fails
                    pass

        return release_id

    def action_release(self):
        """
        Opens the release wizard when the Release button is clicked.
        """
        return {
            "name": "Create Release",
            "type": "ir.actions.act_window",
            "res_model": "helm.chart.install",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": self.name,
                "default_chart_id": self.id,
                "default_product_id": self.product_ids[0].id,
            },
        }

    def action_view_releases(self):
        """
        Opens the list view of releases for this chart.
        """
        self.ensure_one()
        return {
            "name": "Releases",
            "type": "ir.actions.act_window",
            "res_model": "helm.release",
            "view_mode": "list,form",
            "domain": [("chart_id", "=", self.id)],
            "context": {"search_default_chart_id": self.id, "default_chart_id": self.id},
        }
