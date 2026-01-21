import logging

from odoo import fields, models
from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)


class KubectlCluster(models.Model):
    _name = "kubectl.cluster"
    _inherit = ["kubectl.cluster", "website.published.mixin", "website.seo.metadata"]

    website_description = fields.Html(
        "Website Kubectl Cluster Description", strip_style=True, sanitize_overridable=True, translate=html_translate
    )

    def _compute_website_url(self):
        for rec in self:
            rec.website_url = "/clusters/%s" % self.env["ir.http"]._slug(rec)
