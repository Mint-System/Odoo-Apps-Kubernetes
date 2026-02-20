import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelmChartValue(models.Model):
    _name = "helm.chart.value"
    _description = "Helm Chart Value"

    chart_id = fields.Many2one("helm.chart", ondelete="cascade", help="Chart for dynamic values.")
    release_chart_id = fields.Many2one("helm.chart", help="Chart for predefined values.")
    release_id = fields.Many2one("helm.release", ondelete="cascade", help="Value is copied and linked to this release.")

    filter_cluster_ids = fields.Many2many("kubectl.cluster", help="Apply value to these clusters only.")
    product_ids = fields.One2many("product.product", related="chart_id.product_ids")
    filter_product_ids = fields.Many2many(
        "product.product", help="Apply value to these products only.", domain="[('id', 'in', product_ids)]"
    )

    path = fields.Char(help="Path to the nested key of the values.yaml.", required=True)
    value = fields.Char(help="Enter python code to define the value.")
    option_id = fields.Many2one(
        "helm.chart.value.option", domain="[('path', '=', path)]", help="Select value from options."
    )
    readonly = fields.Boolean(help="If checked, this value cannot be modified in the portal.")

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.path

    def copy(self, default=None):
        """
        Copy a chart value, evaluating expressions when copying to a release.
        """
        if default is None:
            default = {}

        # If this value is being copied to a release, evaluate the expression
        if "release_id" in default and self.value:
            # Get the release to use its context for evaluation
            release = self.env["helm.release"].browse(default["release_id"])
            try:
                # Evaluate the expression and store the result
                evaluated_value = release._eval_value(self.value)
                default["value"] = str(evaluated_value)
            except Exception as e:
                _logger.error(f"Error evaluating value {self.value}: {str(e)}")
                # Keep original value if evaluation fails
                default["value"] = self.value

        return super().copy(default=default)


class HelmChartValueOption(models.Model):
    _name = "helm.chart.value.option"
    _description = "Helm Chart Value Option"
    _rec_name = "value"

    path = fields.Char(string="Path", required=True, index=True)
    value = fields.Char(required=True)

    _sql_constraints = [
        (
            "unique_value_by_path",
            "UNIQUE(value, path)",
            "Value option must be unique per path.",
        ),
    ]

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.value
