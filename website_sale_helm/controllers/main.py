import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.form import WebsiteForm

_logger = logging.getLogger(__name__)


class WebsiteSaleHelmController(WebsiteForm):
    @http.route("/website/form/shop.sale.order", type="http", auth="public", methods=["POST"], website=True)
    def website_form_saleorder(self, **kwargs):
        """
        Controller for handling the extra checkout step form submission.
        Validates form data and updates the sale order accordingly.
        """

        # Get the current order from the website
        order = request.website.sale_get_order()
        if not order:
            return json.dumps({"error": "No order found; please add a product to your cart."})

        # Extract form data directly from kwargs
        cluster_id = kwargs.get("cluster_id")
        consulting_partner_id = kwargs.get("consulting_partner_id")
        project_name = kwargs.get("project_name")
        custom_domain = kwargs.get("custom_domain")

        # Validate cluster_id
        if cluster_id:
            cluster = request.env["kubectl.cluster"].sudo().browse(int(cluster_id))
            if not cluster.exists():
                return json.dumps({"error_fields": {"cluster_id": "Invalid cluster selected"}})

        # Validate consulting_partner_id
        if consulting_partner_id:
            partner = request.env["res.partner"].sudo().browse(int(consulting_partner_id))
            if not partner.exists():
                return json.dumps({"error_fields": {"consulting_partner_id": "Invalid consulting partner selected"}})

        # Validate project_name
        if project_name:
            # Check if namespace already exists for the selected cluster
            if cluster_id:
                existing_namespace = (
                    request.env["kubectl.namespace"]
                    .sudo()
                    .search([("name", "=", project_name), ("cluster_id", "=", int(cluster_id))])
                )
                if existing_namespace:
                    return json.dumps(
                        {"error_fields": {"project_name": "Project name already exists for this cluster"}}
                    )

            # Validate project_name format (alphanumeric with hyphens)
            if not all(c.isalnum() or c == "-" for c in project_name):
                return json.dumps(
                    {
                        "error_fields": {
                            "project_name": "Project name must only contain alphanumeric characters and hyphens"
                        }
                    }
                )

            # Validate minimum length
            if len(project_name) < 4:
                return json.dumps({"error_fields": {"project_name": "Project name must be at least 4 characters long"}})

        # Update the sale order with form data
        order_values = {}
        if cluster_id:
            order_values["cluster_id"] = int(cluster_id)
        if consulting_partner_id:
            order_values["consulting_partner_id"] = int(consulting_partner_id)
        if project_name:
            order_values["project_name"] = project_name
        if custom_domain:
            order_values["custom_domain"] = custom_domain

        if order_values:
            order.sudo().write(order_values)

        return json.dumps({"id": order.id})
