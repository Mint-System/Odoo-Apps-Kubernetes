import logging
import subprocess

import yaml

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

from .ir_actions_client import display_notification

_logger = logging.getLogger(__name__)


class HelmRelease(models.Model):
    _name = "helm.release"
    _description = "Helm Release"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(help="Name of the release.", required=True)
    state = fields.Selection(
        selection=[("draft", "Draft"), ("installed", "Installed")],
        default="draft",
    )
    output = fields.Text()
    ingress_url = fields.Char(compute="_compute_ingress_url")
    display_name = fields.Char(compute="_compute_display_name")

    chart_id = fields.Many2one("helm.chart", help="Chart to installed.", required=True)
    cluster_id = fields.Many2one("kubectl.cluster", help="Target cluster to deploy to.", required=True)
    create_namespace = fields.Boolean()
    namespace = fields.Char(help="Namespace with this input will be created.")
    namespace_id = fields.Many2one(
        "kubectl.namespace",
        inverse="_inverse_namespace_id",
        string="Linked Namespace",
        help="Target namespace in cluster.",
    )
    product_id = fields.Many2one("product.product", required=True)
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)

    value_ids = fields.One2many(
        "helm.chart.value",
        "release_id",
        string="Updatable values",
        help="These values can be changed.",
    )
    values = fields.Text(
        compute="_compute_values", store=True, help="Values computed from the chart and the release values."
    )
    customer_notice = fields.Text(
        string="Customer Notice",
        compute="_compute_customer_notice",
        help="Computed customer notice based on chart template",
    )
    secret_ids = fields.One2many(
        "helm.chart.secret",
        "release_id",
    )

    def _inverse_namespace_id(self):
        for rec in self:
            if rec.namespace_id:
                rec.namespace = rec.namespace_id.name

    def get_value(self, path):
        """
        Returns a value from path. The chart_id.value_ids and the release_id.value_ids are checked.
        """
        self.ensure_one()

        # First check release-specific values
        for value in self.value_ids:
            if value.path == path:
                # Use the option value if option_id is set, otherwise use the main value
                if value.option_id:
                    return value.option_id.value
                else:
                    return value.value

        # Then check chart-level values
        for value in self.chart_id.value_ids:
            if value.path == path:
                try:
                    return self._eval_value(value.value)
                except Exception as e:
                    _logger.error(f"Error evaluating chart value {value.value}: {str(e)}")
                    return None

        return None

    def _compute_customer_notice(self):
        """
        Compute the customer notice based on the chart template.
        """
        for release in self:
            if release.chart_id.customer_notice_template:
                try:
                    # Prepare rendering context
                    render_context = {
                        "release": release,
                        "release_id": release,
                    }

                    # Render the template using Odoo's mail rendering mechanism
                    rendered = self.env["mail.render.mixin"]._render_template(
                        release.chart_id.customer_notice_template,
                        "helm.release",
                        [release.id],
                        engine="qweb",
                        add_context=render_context,
                    )
                    release.customer_notice = rendered.get(release.id, "")
                except Exception as e:
                    _logger.error(f"Error rendering customer notice template: {str(e)}")
                    release.customer_notice = ""
            else:
                release.customer_notice = ""

    def _compute_display_name(self):
        for rec in self:
            if rec.namespace:
                rec.display_name = f"{rec.name} ({rec.namespace})"
            else:
                rec.display_name = rec.name

    @api.model
    def generate_password(self, length=8):
        """
        Generate a random password with letters and digits.
        """
        import random
        import string

        return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    def _eval_value(self, expression):
        context = {"self": self, "release": self, "release_id": self, "generate_password": self.generate_password}
        return safe_eval(expression, context)

    @api.depends("chart_id", "value_ids", "chart_id.value_ids", "state", "product_id", "partner_id")
    def _compute_values(self):
        """
        Evaluate custom values of the chart.
        """
        for release in self:
            if release.chart_id.state == "added":
                dict_values = {}

                # Process chart values
                for value in release.chart_id.value_ids.filtered(
                    lambda v: (not v.filter_cluster_ids or release.cluster_id in v.filter_cluster_ids)
                    and (not v.filter_product_ids or release.product_id in v.filter_product_ids)
                ):
                    try:
                        new_value = release._eval_value(value.value)

                        # Apply value to path and convert to dict
                        # Turns 'ingress.host: value' into '{"ingress": {"host": value}}'"
                        if value.path and new_value:
                            keys = value.path.split(".")
                            current = dict_values
                            for key in keys[:-1]:
                                if key not in current:
                                    current[key] = {}
                                elif not isinstance(current[key], dict):
                                    current[key] = {"_value": current[key]}
                                current = current[key]
                            current[keys[-1]] = new_value  # This should be inside the if value.path block
                    except Exception as e:
                        _logger.error(f"Invalid expression {value.value}: {str(e)}")

                for value in release.value_ids:
                    # Use the option value if option_id is set, otherwise use the main value
                    if value.option_id:
                        new_value = value.option_id.value
                    else:
                        new_value = value.value

                    # Apply value to path and convert to dict
                    if value.path and new_value:
                        keys = value.path.split(".")
                        current = dict_values
                        for key in keys[:-1]:
                            if key not in current:
                                current[key] = {}
                            elif not isinstance(current[key], dict):
                                current[key] = {"_value": current[key]}
                            current = current[key]
                        current[keys[-1]] = new_value

                try:
                    release.values = yaml.safe_dump(dict_values, sort_keys=False)
                except yaml.YAMLError as e:
                    raise ValidationError(f"Error converting to YAML: {str(e)}")

    def _compute_ingress_url(self):
        for release in self:
            if release.state == "installed" and release.namespace_id:
                release.ingress_url = "https://" + release.namespace_id.name + "." + release.cluster_id.domain
            else:
                release.ingress_url = ""

    def action_install(self):
        """
        Kubernetes API wrapper.
        Install the Helm chart using the default context configuration.
        """
        self.ensure_one()

        # Check if chart has been added
        if self.chart_id.state != "added":
            raise ValidationError(_("The chart '%s' has not been added.", self.chart_id.name))

        # Create namespace in Kubernetes first
        if self.create_namespace:
            self.namespace_id = self.env["kubectl.namespace"].create(
                {"name": self.namespace, "cluster_id": self.cluster_id.id}
            )

        # Create secrets before chart installation
        self.secret_ids._create_secret(self)

        try:
            # Setup install command
            command = [
                "helm",
                "install",
                self.name,
                f"{self.chart_id.repo_id.name}/{self.chart_id.name}",
                "--namespace",
                self.namespace,
            ]

            # Run command
            result = self.cluster_id.context_id.run(command, self.values)

            self.write({"state": "installed"})
            self.output = result.stdout
            return display_notification("Chart Installed", result.stdout, "success")
        except subprocess.CalledProcessError as e:
            self.output = e.stderr
            return display_notification("Installing Chart Failed", e.stderr, "danger")

    def action_upgrade(self):
        """
        Kubernetes API wrapper.
        Upgrade the Helm chart using the default context configuration.
        """
        self.ensure_one()
        try:
            command = [
                "helm",
                "upgrade",
                self.name,
                f"{self.chart_id.repo_id.name}/{self.chart_id.name}",
            ]
            result = self.cluster_id.context_id.run(command, self.values)

            self.output = result.stdout
            return display_notification("Release Upgraded", result.stdout, "success")
        except subprocess.CalledProcessError as e:
            self.output = e.stderr
            return display_notification("Upgrading Release Failed", e.stderr, "danger")

    def action_uninstall(self):
        """
        Kubernetes API wrapper.
        Uninstall the Helm chart using the default context configuration.
        """
        self.ensure_one()
        try:
            # Delete secrets before uninstalling chart
            self.secret_ids._delete_secret(self)

            command = [
                "helm",
                "uninstall",
                self.name,
            ]
            result = self.cluster_id.context_id.run(command)
            self.write({"state": "draft"})
            self.output = result.stdout
            return display_notification("Release Uninstalled", result.stdout, "success")
        except subprocess.CalledProcessError as e:
            self.output = e.stderr
            return display_notification("Uninstalling Release Failed", e.stderr, "danger")

    def action_status(self):
        """
        Kubernetes API wrapper.
        Show status of helm release.
        """
        self.ensure_one()
        try:
            command = [
                "helm",
                "status",
                self.name,
            ]
            result = self.cluster_id.context_id.run(command)
            self.output = result.stdout
        except subprocess.CalledProcessError as e:
            self.output = e.stderr
            return display_notification("Status Release Failed", e.stderr, "danger")
